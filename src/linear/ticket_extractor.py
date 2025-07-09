"""Minimal Linear ticket extractor for testing."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class LinearTicket:
    """Represents a Linear ticket."""

    identifier: str
    title: str
    state_type: str
    priority: int
    team_key: str
    updated_at: datetime | None = None


class TicketExtractor:
    """Extract Linear ticket IDs from text."""

    # Pattern to match Linear ticket IDs (e.g., ENG-123, AUTH-456)
    TICKET_PATTERN = re.compile(r"\b([A-Z]{2,10})-(\d{1,6})\b")

    @classmethod
    def extract_ticket_ids(cls, text: str) -> set[str]:
        """Extract all Linear ticket IDs from text."""
        if not text:
            return set()

        matches = cls.TICKET_PATTERN.findall(text)
        return {f"{team}-{num}" for team, num in matches}

    @classmethod
    def extract_from_pr(cls, pr_data: dict[str, Any]) -> set[str]:
        """Extract ticket IDs from PR data."""
        tickets = set()

        # Check title
        if title := pr_data.get("title", ""):
            tickets.update(cls.extract_ticket_ids(title))

        # Check body
        if body := pr_data.get("body", ""):
            tickets.update(cls.extract_ticket_ids(body))

        return tickets

    @classmethod
    def extract_from_commit(cls, commit_data: dict[str, Any]) -> set[str]:
        """Extract ticket IDs from commit data."""
        tickets = set()

        # Check commit message
        if commit := commit_data.get("commit", {}):
            if message := commit.get("message", ""):
                tickets.update(cls.extract_ticket_ids(message))

        return tickets

    @classmethod
    def parse_ticket_data(cls, ticket_data: dict[str, Any]) -> LinearTicket | None:
        """Parse Linear API ticket data into LinearTicket object."""
        if not ticket_data:
            return None

        try:
            return LinearTicket(
                identifier=ticket_data.get("identifier", ""),
                title=ticket_data.get("title", ""),
                state_type=ticket_data.get("state", {}).get("type", "unknown"),
                priority=ticket_data.get("priority", 0),
                team_key=ticket_data.get("team", {}).get("key", ""),
                updated_at=datetime.fromisoformat(ticket_data["updatedAt"].replace("Z", "+00:00"))
                if ticket_data.get("updatedAt")
                else None,
            )
        except Exception:
            return None
