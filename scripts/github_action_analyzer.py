#!/usr/bin/env python3
"""
Simplified analysis engine for GitHub Actions PR bot.
This is a standalone version that can run in the GitHub Actions environment.
"""

import json
import os
import re
import sys
from datetime import datetime
from typing import Any

import requests


class GitHubActionAnalyzer:
    """Lightweight analyzer for GitHub Actions environment."""

    WORK_TYPES = ["New Feature", "Bug Fix", "Refactor", "Testing", "Documentation", "Chore"]

    def __init__(self, api_key: str | None = None):
        """Initialize the analyzer."""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

    def detect_ai_assistance(self, pr_data: dict[str, Any]) -> tuple[bool, str | None]:
        """Detect if PR was created with AI assistance."""
        # Check PR body for AI markers
        body = (pr_data.get("body") or "").lower()
        title = (pr_data.get("title") or "").lower()

        ai_markers = {
            "copilot": ["co-authored-by: github copilot", "copilot"],
            "claude": ["claude", "anthropic", "🤖 generated with claude"],
            "cursor": ["cursor", "generated with cursor"],
            "chatgpt": ["chatgpt", "openai", "gpt"],
        }

        for tool, markers in ai_markers.items():
            for marker in markers:
                if marker in body or marker in title:
                    return True, tool.capitalize()

        # Check commit messages in PR
        if pr_data.get("commits_url"):
            # Note: In real implementation, would fetch commits
            pass

        return False, None

    def extract_linear_ticket(self, pr_data: dict[str, Any]) -> str | None:
        """Extract Linear ticket ID from PR."""
        text = f"{pr_data.get('title', '')} {pr_data.get('body', '')}"

        # Look for Linear ticket patterns
        patterns = [
            r"[A-Z]{2,}-\d+",  # ENG-1234
            r"linear\.app/[^/]+/issue/([A-Z]{2,}-\d+)",  # Linear URL
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                if "linear.app" in pattern:
                    return match.group(1)
                return match.group(0)

        return None

    def analyze_diff(self, diff: str, title: str, description: str = "") -> dict[str, Any]:
        """Analyze a PR diff using Claude API."""
        # Prepare the prompt
        prompt = self._create_prompt(title, description, diff)

        # Call Claude API
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 500,
            "temperature": 0,
            "messages": [{"role": "user", "content": prompt}],
            "system": "You are an expert software engineer analyzing code changes. Respond ONLY with a valid JSON object.",
        }

        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages", headers=headers, json=data, timeout=30
            )
            response.raise_for_status()

            result = response.json()
            content = result["content"][0]["text"]

            # Parse the response
            return self._parse_analysis_response(content)

        except Exception as e:
            print(f"Error calling Claude API: {str(e)}")
            # Return default values on error
            return {
                "work_type": "Unknown",
                "complexity_score": 5,
                "risk_score": 5,
                "clarity_score": 5,
                "analysis_summary": "Unable to analyze due to API error",
            }

    def _create_prompt(self, title: str, description: str, diff: str) -> str:
        """Create analysis prompt."""
        # Truncate diff if too long
        if len(diff) > 4000:
            diff = diff[:3900] + "\n... [diff truncated]"

        return f"""Analyze this pull request:

Title: {title}
Description: {description or "No description provided"}

Code Diff:
```
{diff}
```

Provide your analysis as a JSON object with exactly these fields:
{{
    "work_type": "<one of: New Feature, Bug Fix, Refactor, Testing, Documentation, Chore>",
    "complexity_score": <integer 1-10, where 1 is trivial and 10 is extremely complex>,
    "risk_score": <integer 1-10, where 1 is minimal risk and 10 is high risk>,
    "clarity_score": <integer 1-10, where 1 is very unclear and 10 is perfectly clear>,
    "analysis_summary": "<one sentence summary of what this change does>"
}}

Respond ONLY with the JSON object."""

    def _parse_analysis_response(self, response: str) -> dict[str, Any]:
        """Parse Claude's response."""
        try:
            # Extract JSON from response
            response = response.strip()

            # Handle markdown code blocks
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            # Parse JSON
            data = json.loads(response)

            # Validate work type
            if data.get("work_type") not in self.WORK_TYPES:
                data["work_type"] = "Chore"

            # Validate scores
            for field in ["complexity_score", "risk_score", "clarity_score"]:
                if field in data:
                    data[field] = max(1, min(10, int(data[field])))
                else:
                    data[field] = 5

            return data

        except Exception as e:
            print(f"Error parsing response: {str(e)}")
            return {
                "work_type": "Unknown",
                "complexity_score": 5,
                "risk_score": 5,
                "clarity_score": 5,
                "analysis_summary": "Unable to parse analysis response",
            }

    def calculate_impact_score(self, complexity: int, risk: int, clarity: int) -> float:
        """Calculate impact score using PRD formula."""
        return (0.4 * complexity) + (0.5 * risk) + (0.1 * clarity)

    def analyze_pr(self, pr_data: dict[str, Any], diff: str) -> dict[str, Any]:
        """Full PR analysis combining all components."""
        # Get basic PR info
        pr_number = pr_data.get("number", "unknown")
        title = pr_data.get("title", "")
        body = pr_data.get("body", "")

        # Analyze the diff
        analysis = self.analyze_diff(diff, title, body)

        # Detect AI assistance
        ai_assisted, ai_tool = self.detect_ai_assistance(pr_data)

        # Extract Linear ticket
        linear_ticket = self.extract_linear_ticket(pr_data)

        # Calculate impact score
        impact_score = self.calculate_impact_score(
            analysis["complexity_score"], analysis["risk_score"], analysis["clarity_score"]
        )

        # Build final result
        result = {
            "pr_number": pr_number,
            "work_type": analysis["work_type"],
            "complexity_score": analysis["complexity_score"],
            "risk_score": analysis["risk_score"],
            "clarity_score": analysis["clarity_score"],
            "impact_score": round(impact_score, 1),
            "analysis_summary": analysis["analysis_summary"],
            "ai_assisted": ai_assisted,
            "ai_tool_type": ai_tool,
            "linear_ticket_id": linear_ticket,
            "has_linear_ticket": linear_ticket is not None,
            "lines_added": pr_data.get("additions", 0),
            "lines_deleted": pr_data.get("deletions", 0),
            "files_changed": pr_data.get("changed_files", 0),
            "analyzed_at": datetime.utcnow().isoformat(),
        }

        return result


def main():
    """Main entry point for GitHub Actions."""
    # Check for required files
    if not os.path.exists("pr_data.json"):
        print("Error: pr_data.json not found")
        sys.exit(1)

    if not os.path.exists("pr_diff.txt"):
        print("Error: pr_diff.txt not found")
        sys.exit(1)

    # Load PR data
    with open("pr_data.json") as f:
        pr_data = json.load(f)

    # Load diff
    with open("pr_diff.txt") as f:
        diff = f.read()

    # Initialize analyzer
    try:
        analyzer = GitHubActionAnalyzer()
    except ValueError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

    # Analyze PR
    try:
        result = analyzer.analyze_pr(pr_data, diff)

        # Save result
        with open("analysis_result.json", "w") as f:
            json.dump(result, f, indent=2)

        print("Analysis completed successfully")
        print(f"Work Type: {result['work_type']}")
        print(f"Impact Score: {result['impact_score']}/10")

    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        # Create minimal result for error case
        error_result = {
            "pr_number": pr_data.get("number", "unknown"),
            "work_type": "Unknown",
            "complexity_score": 5,
            "risk_score": 5,
            "clarity_score": 5,
            "impact_score": 5.0,
            "analysis_summary": f"Analysis failed: {str(e)}",
            "ai_assisted": False,
            "ai_tool_type": None,
            "linear_ticket_id": None,
            "has_linear_ticket": False,
            "error": str(e),
        }

        with open("analysis_result.json", "w") as f:
            json.dump(error_result, f, indent=2)

        sys.exit(1)


if __name__ == "__main__":
    main()
