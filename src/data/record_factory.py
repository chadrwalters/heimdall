"""Factory for creating unified records from processed data."""

import logging
from datetime import UTC, datetime
from typing import Any

from .unified_record import UnifiedRecord

logger = logging.getLogger(__name__)


class RecordFactory:
    """Factory for creating unified records with consistent data extraction."""

    def create_unified_record(
        self,
        data: dict[str, Any],
        context,
        analysis,
        ticket_match,
        ai_assisted: bool,
        ai_tool: str | None,
        source_type: str,
        context_level: str,
        linear_ticket_id: str | None = None,
    ) -> UnifiedRecord:
        """Create a unified record from processed data."""

        # Extract repository name
        repository = self._extract_repository_name(data)

        # Extract date
        date = self._extract_date(data, source_type)

        # Extract author
        author = self._extract_author(data, context)

        # Get source URL
        source_url = data.get("html_url", data.get("url", ""))

        # Get analysis scores or defaults
        work_type = "Unknown"
        complexity_score = 1.0
        risk_score = 1.0
        clarity_score = 5.0
        analysis_summary = "No analysis available"

        if analysis:
            work_type = analysis.get("work_type", work_type)
            complexity_score = float(analysis.get("complexity_score", complexity_score))
            risk_score = float(analysis.get("risk_score", risk_score))
            clarity_score = float(analysis.get("clarity_score", clarity_score))
            analysis_summary = analysis.get("analysis_summary", analysis_summary)

        # Calculate impact score: 40% complexity + 50% risk + 10% clarity
        impact_score = (0.4 * complexity_score) + (0.5 * risk_score) + (0.1 * clarity_score)

        # Extract file change metrics
        lines_added = context.metadata.get("additions", 0)
        lines_deleted = context.metadata.get("deletions", 0)
        files_changed = context.metadata.get("changed_files", len(context.file_changes))

        # Handle Linear ticket information
        ticket_id = linear_ticket_id
        has_ticket = False
        process_compliant = False

        if ticket_match:
            ticket_id = (
                ticket_match.primary_ticket.identifier if ticket_match.primary_ticket else None
            )
            has_ticket = len(ticket_match.ticket_ids) > 0
            process_compliant = ticket_match.primary_ticket is not None
        elif linear_ticket_id:
            has_ticket = True
            process_compliant = True  # Assume compliance if ticket ID found

        return UnifiedRecord(
            repository=repository,
            date=date,
            author=author,
            source_type=source_type,
            source_url=source_url,
            context_level=context_level,
            work_type=work_type,
            complexity_score=complexity_score,
            risk_score=risk_score,
            clarity_score=clarity_score,
            analysis_summary=analysis_summary,
            lines_added=int(lines_added),
            lines_deleted=int(lines_deleted),
            files_changed=int(files_changed),
            impact_score=round(impact_score, 2),
            ai_assisted=ai_assisted,
            ai_tool_type=ai_tool,
            linear_ticket_id=ticket_id,
            has_linear_ticket=has_ticket,
            process_compliant=process_compliant,
        )

    def _extract_repository_name(self, data: dict[str, Any]) -> str:
        """Extract repository name from data."""
        # Try various fields where repo name might be stored
        repo_url = data.get("repository_url", data.get("repo_url", ""))
        if repo_url:
            return repo_url.split("/")[-1]

        url = data.get("html_url", data.get("url", ""))
        if url and "github.com" in url:
            parts = url.split("/")
            if len(parts) >= 5:
                return parts[4]  # owner/repo format

        return data.get("repository", "unknown")

    def _extract_date(self, data: dict[str, Any], source_type: str) -> str:
        """Extract date in ISO format."""
        if source_type == "PR":
            date_str = data.get("merged_at") or data.get("created_at")
        else:  # Commit
            date_str = data.get("committed_at") or data.get("created_at")

        if date_str:
            try:
                # Parse and convert to ISO format
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return dt.isoformat()
            except ValueError:
                pass

        # Fallback to current time
        return datetime.now(UTC).isoformat()

    def _extract_author(self, data: dict[str, Any], context) -> str:
        """Extract author email or username."""
        author = context.metadata.get("author", "")
        if not author:
            # Fallback extraction for different data formats
            if "commit" in data:
                author = data["commit"].get("author", {}).get("email", "unknown")
            elif "author_email" in data:  # Flattened CSV format
                author = data["author_email"]
            elif "user" in data:
                author = data.get("user", {}).get("login", "unknown")
            elif "user_login" in data:  # Flattened CSV format
                author = data["user_login"]
            else:
                author = "unknown"

        return author
