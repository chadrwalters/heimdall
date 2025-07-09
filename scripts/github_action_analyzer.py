#!/usr/bin/env python3
"""
Simplified analysis engine for GitHub Actions PR bot.
This is a standalone version that can run in the GitHub Actions environment.
Uses rule-based analysis instead of API calls for reliability.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any


class GitHubActionAnalyzer:
    """Lightweight analyzer for GitHub Actions environment."""

    WORK_TYPES = ["New Feature", "Bug Fix", "Refactor", "Testing", "Documentation", "Chore"]

    def __init__(self, api_key: str | None = None):
        """Initialize the analyzer."""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        # Don't require API key - use rule-based analysis instead
        self.use_api = bool(self.api_key)

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

    def analyze_diff_rules(self, diff: str, title: str, description: str = "") -> dict[str, Any]:
        """Analyze diff using rule-based logic."""
        # Analyze work type
        work_type = self._detect_work_type(title, description, diff)
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity(diff, title, description)
        
        # Calculate risk score
        risk_score = self._calculate_risk(diff, title, description)
        
        # Calculate clarity score
        clarity_score = self._calculate_clarity(diff, title, description)
        
        # Generate summary
        summary = self._generate_summary(work_type, diff, title, description)
        
        return {
            "work_type": work_type,
            "complexity_score": complexity_score,
            "risk_score": risk_score,
            "clarity_score": clarity_score,
            "analysis_summary": summary,
        }

    def _detect_work_type(self, title: str, description: str, diff: str) -> str:
        """Detect work type based on title, description, and diff."""
        text = f"{title} {description}".lower()
        
        # Check for explicit keywords
        if any(keyword in text for keyword in ["fix", "bug", "issue", "error", "problem"]):
            return "Bug Fix"
        
        if any(keyword in text for keyword in ["test", "spec", "unit", "integration"]):
            return "Testing"
        
        if any(keyword in text for keyword in ["doc", "readme", "guide", "comment"]):
            return "Documentation"
        
        if any(keyword in text for keyword in ["refactor", "clean", "optimize", "improve"]):
            return "Refactor"
        
        if any(keyword in text for keyword in ["chore", "deps", "dependency", "build", "ci"]):
            return "Chore"
        
        # Analyze diff patterns
        diff_lines = diff.split('\n')
        
        # Check for test files
        test_files = sum(1 for line in diff_lines if line.startswith('+++') and any(
            test_dir in line for test_dir in ['test', 'spec', '__test__']
        ))
        
        # Check for documentation files
        doc_files = sum(1 for line in diff_lines if line.startswith('+++') and any(
            ext in line for ext in ['.md', '.rst', '.txt', 'README', 'CHANGELOG']
        ))
        
        # Check for config/build files
        config_files = sum(1 for line in diff_lines if line.startswith('+++') and any(
            file_type in line for file_type in ['.yml', '.yaml', '.toml', '.json', 'Dockerfile', 'requirements']
        ))
        
        if test_files > 0 and test_files >= len([l for l in diff_lines if l.startswith('+++')]) * 0.5:
            return "Testing"
        
        if doc_files > 0 and doc_files >= len([l for l in diff_lines if l.startswith('+++')]) * 0.5:
            return "Documentation"
        
        if config_files > 0 and config_files >= len([l for l in diff_lines if l.startswith('+++')]) * 0.5:
            return "Chore"
        
        # Default to New Feature for substantial changes
        return "New Feature"

    def _calculate_complexity(self, diff: str, title: str, description: str) -> int:
        """Calculate complexity score (1-10)."""
        score = 1
        
        # Count lines of code changes
        diff_lines = diff.split('\n')
        added_lines = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
        deleted_lines = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))
        
        # File count
        files_changed = len([line for line in diff_lines if line.startswith('+++')])
        
        # Base complexity on lines changed
        total_lines = added_lines + deleted_lines
        if total_lines > 500:
            score += 4
        elif total_lines > 200:
            score += 3
        elif total_lines > 100:
            score += 2
        elif total_lines > 50:
            score += 1
        
        # Add complexity for multiple files
        if files_changed > 10:
            score += 2
        elif files_changed > 5:
            score += 1
        
        # Look for complex patterns in diff
        complex_patterns = [
            r'class\s+\w+',  # Class definitions
            r'def\s+\w+',    # Function definitions
            r'async\s+def',  # Async functions
            r'@\w+',         # Decorators
            r'import\s+\w+', # New imports
            r'from\s+\w+',   # New imports
            r'if\s+.*:',     # Conditional logic
            r'for\s+.*:',    # Loops
            r'while\s+.*:',  # Loops
            r'try:',         # Exception handling
            r'except\s+.*:', # Exception handling
        ]
        
        for pattern in complex_patterns:
            matches = len(re.findall(pattern, diff))
            if matches > 10:
                score += 2
            elif matches > 5:
                score += 1
        
        return min(10, max(1, score))

    def _calculate_risk(self, diff: str, title: str, description: str) -> int:
        """Calculate risk score (1-10)."""
        score = 1
        
        # High-risk patterns
        high_risk_patterns = [
            r'delete|remove|drop',           # Deletion operations
            r'password|secret|key|token',    # Security-related
            r'auth|login|session',           # Authentication
            r'admin|root|sudo',              # Privilege escalation
            r'database|db|sql',              # Database changes
            r'migration|migrate',            # Database migrations
            r'config|settings|env',          # Configuration changes
            r'api|endpoint|route',           # API changes
            r'security|vulnerability',       # Security fixes
            r'production|prod|deploy',       # Production changes
        ]
        
        diff_lower = diff.lower()
        title_lower = title.lower()
        desc_lower = description.lower()
        
        for pattern in high_risk_patterns:
            if re.search(pattern, diff_lower) or re.search(pattern, title_lower) or re.search(pattern, desc_lower):
                score += 1
        
        # Check for critical files
        diff_lines = diff.split('\n')
        critical_files = [
            'dockerfile', 'docker-compose', 'requirements.txt', 'package.json',
            'pyproject.toml', 'setup.py', 'makefile', 'justfile',
            '.env', 'config', 'settings', 'constants'
        ]
        
        for line in diff_lines:
            if line.startswith('+++'):
                filename = line[4:].lower()
                if any(critical in filename for critical in critical_files):
                    score += 1
        
        # Large changes are riskier
        total_lines = len([l for l in diff_lines if l.startswith(('+', '-')) and not l.startswith(('+++', '---'))])
        if total_lines > 500:
            score += 3
        elif total_lines > 200:
            score += 2
        elif total_lines > 100:
            score += 1
        
        return min(10, max(1, score))

    def _calculate_clarity(self, diff: str, title: str, description: str) -> int:
        """Calculate clarity score (1-10)."""
        score = 5  # Start with neutral
        
        # Title quality
        if len(title) < 20:
            score -= 1
        elif len(title) > 100:
            score -= 1
        else:
            score += 1
        
        # Description quality
        if not description or len(description) < 50:
            score -= 2
        elif len(description) > 200:
            score += 1
        
        # Check for good patterns in diff
        good_patterns = [
            r'#.*comment',           # Comments
            r'""".*"""',            # Docstrings
            r"'''.*'''",            # Docstrings
            r'TODO|FIXME|NOTE',     # Code annotations
            r'def\s+test_',         # Test functions
            r'assert\s+',           # Test assertions
            r'readme|documentation', # Documentation
        ]
        
        for pattern in good_patterns:
            matches = len(re.findall(pattern, diff, re.IGNORECASE | re.DOTALL))
            if matches > 0:
                score += 1
        
        # Check for unclear patterns
        unclear_patterns = [
            r'TODO.*',              # Too many TODOs
            r'FIXME.*',             # Too many FIXMEs
            r'hack|temp|tmp',       # Temporary code
            r'magic.*number',       # Magic numbers
            r'hardcode',            # Hardcoded values
        ]
        
        for pattern in unclear_patterns:
            matches = len(re.findall(pattern, diff, re.IGNORECASE))
            if matches > 3:
                score -= 1
        
        return min(10, max(1, score))

    def _generate_summary(self, work_type: str, diff: str, title: str, description: str) -> str:
        """Generate a summary of the changes."""
        # Count changes
        diff_lines = diff.split('\n')
        added_lines = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
        deleted_lines = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))
        files_changed = len([line for line in diff_lines if line.startswith('+++')])
        
        # Extract file types
        file_extensions = set()
        for line in diff_lines:
            if line.startswith('+++'):
                filename = line[4:].strip()
                if '.' in filename:
                    ext = filename.split('.')[-1]
                    file_extensions.add(ext)
        
        # Build summary
        summary_parts = []
        
        if work_type == "New Feature":
            summary_parts.append("Introduces new functionality")
        elif work_type == "Bug Fix":
            summary_parts.append("Fixes an existing issue")
        elif work_type == "Refactor":
            summary_parts.append("Improves code structure")
        elif work_type == "Testing":
            summary_parts.append("Adds or updates tests")
        elif work_type == "Documentation":
            summary_parts.append("Updates documentation")
        else:
            summary_parts.append("Makes maintenance changes")
        
        if files_changed == 1:
            summary_parts.append("in 1 file")
        elif files_changed > 1:
            summary_parts.append(f"across {files_changed} files")
        
        if added_lines > 0 and deleted_lines > 0:
            summary_parts.append(f"with {added_lines} additions and {deleted_lines} deletions")
        elif added_lines > 0:
            summary_parts.append(f"adding {added_lines} lines")
        elif deleted_lines > 0:
            summary_parts.append(f"removing {deleted_lines} lines")
        
        if file_extensions:
            ext_list = sorted(file_extensions)[:3]  # Show max 3 extensions
            summary_parts.append(f"({', '.join(ext_list)} files)")
        
        return " ".join(summary_parts)

    def analyze_diff(self, diff: str, title: str, description: str = "") -> dict[str, Any]:
        """Analyze a PR diff using API or rule-based analysis."""
        # Use rule-based analysis by default, fall back to API if available
        if self.use_api:
            try:
                return self._analyze_with_api(diff, title, description)
            except Exception as e:
                print(f"API analysis failed: {str(e)}, falling back to rule-based analysis")
                return self.analyze_diff_rules(diff, title, description)
        else:
            return self.analyze_diff_rules(diff, title, description)

    def _analyze_with_api(self, diff: str, title: str, description: str = "") -> dict[str, Any]:
        """Analyze a PR diff using Claude API."""
        # Import requests only when needed
        import requests
        
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

        response = requests.post(
            "https://api.anthropic.com/v1/messages", headers=headers, json=data, timeout=30
        )
        response.raise_for_status()

        result = response.json()
        content = result["content"][0]["text"]

        # Parse the response
        return self._parse_analysis_response(content)

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
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
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
        print(f"Analyzer initialized with {'API' if analyzer.use_api else 'rule-based'} analysis")
    except Exception as e:
        print(f"Error initializing analyzer: {str(e)}")
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
            "lines_added": pr_data.get("additions", 0),
            "lines_deleted": pr_data.get("deletions", 0),
            "files_changed": pr_data.get("changed_files", 0),
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }

        with open("analysis_result.json", "w") as f:
            json.dump(error_result, f, indent=2)

        sys.exit(1)


if __name__ == "__main__":
    main()
