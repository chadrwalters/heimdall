"""Prompt engineering for code analysis."""

import json
import logging
from dataclasses import dataclass
from typing import Any

from ..exceptions import (
    InvalidInputError,
    ResponseParsingError,
)
from ..validation.input_validator import InputValidator, ValidationError

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Structured result from code analysis."""

    work_type: str
    complexity_score: int
    risk_score: int
    clarity_score: int
    analysis_summary: str
    raw_response: str


class PromptEngineer:
    """Handles prompt design and response parsing for code analysis."""

    # Work type categories
    WORK_TYPES = ["New Feature", "Bug Fix", "Refactor", "Testing", "Documentation", "Chore"]

    # System prompt for consistent analysis
    SYSTEM_PROMPT = """You are an expert software engineer analyzing code changes. 
Your task is to classify the work and provide objective scores based on the code diff and context provided.

Respond ONLY with a valid JSON object in the exact format specified. Do not include any additional text or explanation outside the JSON."""

    @staticmethod
    def create_analysis_prompt(
        title: str,
        description: str | None,
        diff: str,
        file_changes: list[str] | None = None,
        lines_changed: int = 0,
    ) -> str:
        """Create a prompt for analyzing a code change."""
        # Validate and sanitize inputs
        try:
            title = InputValidator.validate_prompt_input(title, max_length=500)
            if description:
                description = InputValidator.validate_prompt_input(description, max_length=2000)
            # Allow larger diffs since they get truncated anyway
            diff = InputValidator.validate_prompt_input(diff, max_length=50000)

            if file_changes:
                file_changes = [
                    InputValidator.validate_prompt_input(file_name, max_length=200)
                    for file_name in file_changes
                ]
        except ValidationError as e:
            raise InvalidInputError(f"Input validation failed: {e}", input_type="prompt_creation")

        # Build context section
        context_parts = [f"Title: {title}"]

        if description:
            context_parts.append(f"Description: {description}")

        if file_changes:
            context_parts.append(f"Files Changed: {', '.join(file_changes[:10])}")
            if len(file_changes) > 10:
                context_parts.append(f"... and {len(file_changes) - 10} more files")

        context = "\n".join(context_parts)

        # Dynamic diff truncation based on change size
        num_files = len(file_changes) if file_changes else 1
        max_diff_length = min(4000 + (num_files * 200), 8000)

        if len(diff) > max_diff_length:
            diff = diff[: max_diff_length - 100] + "\n... [diff truncated for length]"

        prompt = f"""Analyze the following code change:

{context}

Code Diff:
```
{diff}
```

Provide your analysis as a JSON object with exactly these fields:
{{
    "work_type": "<one of: New Feature, Bug Fix, Refactor, Testing, Documentation, Chore>",
    "complexity_score": <integer 1-10, where 1 is trivial and 10 is extremely complex>,
    "risk_score": <integer 1-10, where 1 is minimal risk and 10 is high risk of breaking changes>,
    "clarity_score": <integer 1-10, where 1 is very unclear and 10 is perfectly clear>,
    "analysis_summary": "<one sentence summary of what this change does>"
}}

Scoring Guidelines:
- Complexity: 1-3 (simple changes <100 lines), 4-6 (moderate changes 100-1000 lines), 7-8 (complex changes >1000 lines), 9-10 (architectural/framework changes)
- Risk: Consider potential for bugs, breaking changes, security implications, and blast radius. For new frameworks/infrastructure, score 6-8 for organizational impact even if technical risk is low
- Clarity: Consider code readability, documentation, naming, and how well the intent is communicated
- Work Type: Choose the PRIMARY category that best describes the change
- For changes >1000 lines: minimum complexity score of 6, minimum risk score of 5
- For changes >5000 lines: minimum complexity score of 7, minimum risk score of 6

Remember: Respond ONLY with the JSON object, no additional text."""

        return prompt

    @staticmethod
    def create_batch_prompt(changes: list[dict[str, Any]]) -> str:
        """Create a prompt for analyzing multiple changes at once."""
        prompt_parts = [
            "Analyze the following code changes and provide a JSON array of analysis results:"
        ]

        for idx, change in enumerate(changes):
            prompt_parts.append(f"\n--- Change {idx + 1} ---")
            prompt_parts.append(f"Title: {change.get('title', 'Untitled')}")

            if change.get("description"):
                prompt_parts.append(f"Description: {change['description']}")

            diff = change.get("diff", "")
            if len(diff) > 1000:
                diff = diff[:950] + "\n... [truncated]"
            prompt_parts.append(f"Diff:\n```\n{diff}\n```")

        prompt_parts.append(
            "\nProvide your analysis as a JSON array where each element has this structure:"
        )
        prompt_parts.append("""[
    {
        "work_type": "<one of: New Feature, Bug Fix, Refactor, Testing, Documentation, Chore>",
        "complexity_score": <integer 1-10>,
        "risk_score": <integer 1-10>,
        "clarity_score": <integer 1-10>,
        "analysis_summary": "<one sentence summary>"
    },
    ...
]""")

        return "\n".join(prompt_parts)

    @staticmethod
    def parse_response(response: str) -> AnalysisResult:
        """Parse the LLM response into a structured result."""
        try:
            # Try to extract JSON from the response
            response_text = response.strip()

            # Handle case where response might have markdown code blocks
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()

            # Parse JSON
            data = json.loads(response_text)

            # Validate required fields and provide defaults if missing
            if any(
                field not in data
                for field in [
                    "work_type",
                    "complexity_score",
                    "risk_score",
                    "clarity_score",
                    "analysis_summary",
                ]
            ):
                # If any required field is missing, return default fallback
                return AnalysisResult(
                    work_type="Chore",
                    complexity_score=5,
                    risk_score=5,
                    clarity_score=5,
                    analysis_summary="Unable to parse response fully - using defaults",
                )

            # Validate work type
            if data["work_type"] not in PromptEngineer.WORK_TYPES:
                # Try to find closest match
                work_type_lower = data["work_type"].lower()
                for wt in PromptEngineer.WORK_TYPES:
                    if work_type_lower in wt.lower() or wt.lower() in work_type_lower:
                        data["work_type"] = wt
                        break
                else:
                    data["work_type"] = "Chore"  # Default fallback

            # Validate scores are in range
            for score_field in ["complexity_score", "risk_score", "clarity_score"]:
                score = int(data[score_field])
                if not 1 <= score <= 10:
                    score = max(1, min(10, score))  # Clamp to range
                data[score_field] = score

            return AnalysisResult(
                work_type=data["work_type"],
                complexity_score=data["complexity_score"],
                risk_score=data["risk_score"],
                clarity_score=data["clarity_score"],
                analysis_summary=data["analysis_summary"],
                raw_response=response,
            )

        except json.JSONDecodeError as e:
            # Fallback for JSON parsing errors
            logger.warning(f"JSON parsing failed: {e}")
            return AnalysisResult(
                work_type="Chore",
                complexity_score=5,
                risk_score=5,
                clarity_score=5,
                analysis_summary="Unable to parse analysis response - invalid JSON",
                raw_response=response,
            )
        except ResponseParsingError:
            # Re-raise specific parsing errors
            raise
        except Exception as e:
            # General fallback for unexpected errors
            logger.error(f"Unexpected parsing error: {e}")
            return AnalysisResult(
                work_type="Chore",
                complexity_score=5,
                risk_score=5,
                clarity_score=5,
                analysis_summary=f"Unexpected parsing error: {str(e)}",
                raw_response=response,
            )

    @staticmethod
    def calculate_impact_score(
        complexity: int, risk: int, clarity: int, lines_changed: int = 0, files_changed: int = 0
    ) -> float:
        """Calculate weighted impact score with size-based multipliers."""
        # Base PRD formula: 40% complexity + 50% risk + 10% clarity
        base_score = (0.4 * complexity) + (0.5 * risk) + (0.1 * clarity)

        # Size multiplier for large changes
        size_multiplier = 1.0
        if lines_changed > 1000 or files_changed > 10:
            # Scale multiplier based on change size
            line_factor = min(lines_changed / 5000, 1.0)  # Cap at 5k lines
            file_factor = min(files_changed / 50, 1.0)  # Cap at 50 files
            size_multiplier = 1.0 + (0.5 * max(line_factor, file_factor))

        final_score = base_score * size_multiplier
        return min(final_score, 10.0)  # Cap at maximum score
