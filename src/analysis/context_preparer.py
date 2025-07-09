"""Context preparation for code analysis."""

import hashlib
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class PreparedContext:
    """Prepared context for analysis."""

    title: str
    description: str | None
    diff: str
    file_changes: list[str]
    cache_key: str
    metadata: dict[str, Any]


class ContextPreparer:
    """Prepares PR and commit data for LLM analysis."""

    # Patterns to detect file types
    FILE_PATTERNS = {
        "test": re.compile(r"(test_|_test\.|\.test\.|spec\.|\.spec\.)", re.IGNORECASE),
        "config": re.compile(r"(config|settings|\.env|\.yml|\.yaml|\.json|\.toml)", re.IGNORECASE),
        "docs": re.compile(r"(readme|docs?/|\.md$|\.rst$|\.txt$)", re.IGNORECASE),
        "build": re.compile(
            r"(makefile|dockerfile|\.gradle|pom\.xml|package\.json|requirements\.txt|setup\.py)",
            re.IGNORECASE,
        ),
    }

    # Patterns to prioritize in diffs
    IMPORTANT_PATTERNS = [
        re.compile(r"^[+-]\s*(class|def|function|interface|struct|enum)\s+\w+"),
        re.compile(r"^[+-]\s*(import|from|require|include|using)\s+"),
        re.compile(r"^[+-]\s*(if|while|for|switch|try|catch|throw|raise)\s*\("),
        re.compile(r"^[+-]\s*(@\w+|#\[|decorator)"),  # Decorators/attributes
        re.compile(r"^[+-]\s*(public|private|protected|static|final|const)\s+"),
    ]

    @staticmethod
    def prepare_pr_context(pr_data: dict[str, Any], diff: str | None = None) -> PreparedContext:
        """Prepare PR data for analysis."""
        title = pr_data.get("title", "Untitled PR")
        description = pr_data.get("body", "")
        pr_id = pr_data.get("id", pr_data.get("number", "unknown"))

        # Extract file changes
        file_changes = []
        if "files" in pr_data:
            file_changes = [f["filename"] for f in pr_data["files"] if "filename" in f]

        # Prepare diff
        prepared_diff = diff or pr_data.get("diff", "")
        if prepared_diff:
            prepared_diff = ContextPreparer._prepare_diff(prepared_diff, file_changes)

        # Generate cache key
        cache_content = f"{pr_id}:{title}:{len(prepared_diff)}"
        cache_key = hashlib.md5(cache_content.encode()).hexdigest()

        # Collect metadata
        metadata = {
            "pr_id": pr_id,
            "author": pr_data.get("user", {}).get("login", "unknown"),
            "created_at": pr_data.get("created_at"),
            "merged_at": pr_data.get("merged_at"),
            "additions": pr_data.get("additions", 0),
            "deletions": pr_data.get("deletions", 0),
            "changed_files": pr_data.get("changed_files", len(file_changes)),
            "url": pr_data.get("html_url", ""),
            "base_branch": pr_data.get("base", {}).get("ref", ""),
            "head_branch": pr_data.get("head", {}).get("ref", ""),
        }

        return PreparedContext(
            title=title,
            description=description,
            diff=prepared_diff,
            file_changes=file_changes,
            cache_key=cache_key,
            metadata=metadata,
        )

    @staticmethod
    def prepare_commit_context(
        commit_data: dict[str, Any], diff: str | None = None
    ) -> PreparedContext:
        """Prepare commit data for analysis."""
        # Extract commit message (first line as title, rest as description)
        message = commit_data.get("commit", {}).get("message", "") or commit_data.get("message", "")
        lines = message.strip().split("\n")
        title = lines[0] if lines else "Untitled commit"
        description = "\n".join(lines[1:]).strip() if len(lines) > 1 else None

        sha = commit_data.get("sha", "unknown")

        # Extract file changes
        file_changes = []
        if "files" in commit_data:
            file_changes = [f["filename"] for f in commit_data["files"] if "filename" in f]

        # Prepare diff
        prepared_diff = diff or commit_data.get("diff", "")
        if prepared_diff:
            prepared_diff = ContextPreparer._prepare_diff(prepared_diff, file_changes)

        # Generate cache key
        cache_key = hashlib.md5(sha.encode()).hexdigest()

        # Collect metadata
        metadata = {
            "commit_sha": sha,
            "author": commit_data.get("commit", {}).get("author", {}).get("email", "unknown"),
            "committer": commit_data.get("commit", {}).get("committer", {}).get("email", "unknown"),
            "committed_at": commit_data.get("commit", {}).get("committer", {}).get("date"),
            "additions": commit_data.get("stats", {}).get("additions", 0),
            "deletions": commit_data.get("stats", {}).get("deletions", 0),
            "total_changes": commit_data.get("stats", {}).get("total", 0),
            "url": commit_data.get("html_url", ""),
        }

        return PreparedContext(
            title=title,
            description=description,
            diff=prepared_diff,
            file_changes=file_changes,
            cache_key=cache_key,
            metadata=metadata,
        )

    @staticmethod
    def _prepare_diff(diff: str, file_changes: list[str]) -> str:
        """Prepare and truncate diff while preserving important context."""
        if not diff:
            return ""

        # If diff is already within limits, return as-is
        if len(diff) <= 4000:
            return diff

        # Strategy: Prioritize important code changes
        lines = diff.split("\n")
        important_lines = []
        context_lines = []

        in_important_section = False

        for line in lines:
            # Track current file
            if line.startswith("diff --git") or line.startswith("+++") or line.startswith("---"):
                important_lines.append(line)
                continue

            # Always include file headers
            if line.startswith("@@"):
                important_lines.append(line)
                in_important_section = False
                continue

            # Check if line matches important patterns
            is_important = any(
                pattern.match(line) for pattern in ContextPreparer.IMPORTANT_PATTERNS
            )

            if is_important:
                important_lines.append(line)
                in_important_section = True
            elif in_important_section and (line.startswith("+") or line.startswith("-")):
                # Include changed lines immediately after important lines
                important_lines.append(line)
            else:
                context_lines.append(line)

        # Build final diff
        final_lines = important_lines

        # Add context lines if there's room
        remaining_space = 3800 - sum(len(line) + 1 for line in final_lines)
        for line in context_lines:
            if remaining_space > len(line) + 1:
                final_lines.append(line)
                remaining_space -= len(line) + 1
            else:
                break

        result = "\n".join(final_lines)
        if len(result) > 3900:
            result = result[:3900]

        result += f"\n... [truncated from {len(diff)} to {len(result)} characters]"

        return result

    @staticmethod
    def detect_ai_assistance(data: dict[str, Any]) -> tuple[bool, str | None]:
        """Detect if the work was done with AI assistance."""
        # Check commit message or PR body for AI indicators
        ai_indicators = [
            ("co-authored-by: github copilot", "GitHub Copilot"),
            ("co-authored-by: copilot", "GitHub Copilot"),
            ("github copilot", "GitHub Copilot"),
            ("generated with claude code", "Claude Code"),
            ("🤖 generated with claude", "Claude Code"),
            ("generated with claude", "Claude"),
            ("generated by claude", "Claude"),
            ("claude code", "Claude Code"),
            ("cursor.ai", "Cursor"),
            ("written with cursor", "Cursor"),
            ("generated with cursor", "Cursor"),
            ("co-authored-by: assistant", "Assistant"),
            ("generated by ai", "Unknown AI Tool"),
            ("ai assistant", "Unknown AI Tool"),
            ("ai coding assistant", "Unknown AI Tool"),
            ("ai-assisted", "Unknown AI Tool"),
            ("ai assisted", "Unknown AI Tool"),
            ("copilot", "GitHub Copilot"),
            ("🤖", "Unknown AI Tool"),
        ]

        # Check in commit message
        message = data.get("commit", {}).get("message", "") or data.get("message", "")
        body = data.get("body", "")

        combined_text = f"{message} {body}".lower()

        # Check indicators in order (more specific first)
        for indicator_text, tool_name in ai_indicators:
            if indicator_text in combined_text:
                return True, tool_name

        return False, None

    @staticmethod
    def extract_linear_ticket_id(data: dict[str, Any]) -> str | None:
        """Extract Linear ticket ID from PR/commit data."""
        # Import here to avoid circular dependency
        from src.linear.ticket_extractor import TicketExtractor

        # Use the new ticket extractor
        if "title" in data:  # PR data
            ticket_ids = TicketExtractor.extract_from_pr(data)
        else:  # Commit data
            ticket_ids = TicketExtractor.extract_from_commit(data)

        # Return the first ticket ID found (primary ticket)
        if ticket_ids:
            return list(ticket_ids)[0]

        return None
