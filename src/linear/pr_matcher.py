"""Match Pull Requests with Linear tickets."""

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .linear_client import LinearClient
from .ticket_extractor import LinearTicket, TicketExtractor

logger = logging.getLogger(__name__)


@dataclass
class PRTicketMatch:
    """Represents a match between a PR and Linear tickets."""

    pr_id: str
    pr_number: int
    pr_title: str
    pr_url: str
    ticket_ids: set[str]
    primary_ticket: LinearTicket | None
    all_tickets: list[LinearTicket]
    match_confidence: float  # 0.0 to 1.0
    match_sources: list[str]  # Where matches were found (title, body, etc.)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "pr_id": self.pr_id,
            "pr_number": self.pr_number,
            "pr_title": self.pr_title,
            "pr_url": self.pr_url,
            "ticket_ids": list(self.ticket_ids),
            "primary_ticket_id": self.primary_ticket.identifier if self.primary_ticket else None,
            "primary_ticket_title": self.primary_ticket.title if self.primary_ticket else None,
            "all_ticket_ids": [t.identifier for t in self.all_tickets],
            "match_confidence": self.match_confidence,
            "match_sources": self.match_sources,
            "has_linear_ticket": len(self.ticket_ids) > 0,
            "process_compliant": self.primary_ticket is not None,
        }


class PRTicketMatcher:
    """Match PRs with Linear tickets and enrich with ticket data."""

    def __init__(self, linear_client: LinearClient):
        """Initialize the matcher with a Linear client."""
        self.linear_client = linear_client
        self.ticket_extractor = TicketExtractor()
        self._match_cache = {}

    def match_pr(self, pr_data: dict[str, Any]) -> PRTicketMatch:
        """Match a single PR with Linear tickets."""
        pr_id = str(pr_data.get("id", pr_data.get("number", "unknown")))
        pr_number = pr_data.get("number", 0)
        pr_title = pr_data.get("title", "")
        pr_url = pr_data.get("html_url", pr_data.get("url", ""))

        # Check cache
        cache_key = f"{pr_id}_{pr_number}"
        if cache_key in self._match_cache:
            logger.debug(f"Using cached match for PR {pr_number}")
            return self._match_cache[cache_key]

        # Extract ticket IDs from PR
        ticket_ids = self.ticket_extractor.extract_from_pr(pr_data)
        match_sources = []

        # Track where matches were found
        title_tickets = self.ticket_extractor.extract_ticket_ids(pr_title)
        if title_tickets:
            match_sources.append("title")

        body = pr_data.get("body", "")
        if body:
            body_tickets = self.ticket_extractor.extract_ticket_ids(body)
            if body_tickets:
                match_sources.append("body")

        # Fetch ticket data from Linear
        all_tickets = []
        primary_ticket = None

        if ticket_ids:
            # Get ticket data for all found IDs
            tickets_data = self.linear_client.get_issues_by_ids(list(ticket_ids))

            for ticket_id, ticket_data in tickets_data.items():
                if ticket_data:
                    ticket = self.ticket_extractor.parse_ticket_data(ticket_data)
                    if ticket:
                        all_tickets.append(ticket)

            # Determine primary ticket
            primary_ticket = self._select_primary_ticket(all_tickets, title_tickets)

        # Calculate match confidence
        confidence = self._calculate_confidence(ticket_ids, all_tickets, match_sources, pr_data)

        # Create match result
        match = PRTicketMatch(
            pr_id=pr_id,
            pr_number=pr_number,
            pr_title=pr_title,
            pr_url=pr_url,
            ticket_ids=ticket_ids,
            primary_ticket=primary_ticket,
            all_tickets=all_tickets,
            match_confidence=confidence,
            match_sources=match_sources,
        )

        # Cache the result
        self._match_cache[cache_key] = match

        return match

    def batch_match_prs(
        self, pr_list: list[dict[str, Any]], progress_callback: callable = None
    ) -> list[PRTicketMatch]:
        """Match multiple PRs with Linear tickets."""
        matches = []
        total = len(pr_list)

        # First, extract all ticket IDs to batch fetch
        all_ticket_ids = set()
        pr_ticket_map = {}

        for i, pr in enumerate(pr_list):
            pr_id = str(pr.get("id", pr.get("number", f"unknown_{i}")))
            ticket_ids = self.ticket_extractor.extract_from_pr(pr)

            if ticket_ids:
                all_ticket_ids.update(ticket_ids)
                pr_ticket_map[pr_id] = ticket_ids

        # Batch fetch all tickets
        if all_ticket_ids:
            logger.info(f"Fetching {len(all_ticket_ids)} unique tickets from Linear")
            self.linear_client.get_issues_by_ids(list(all_ticket_ids))

        # Now match each PR
        for i, pr in enumerate(pr_list):
            match = self.match_pr(pr)
            matches.append(match)

            if progress_callback:
                progress_callback(i + 1, total)

        return matches

    def match_commits(self, commit_list: list[dict[str, Any]]) -> dict[str, set[str]]:
        """Extract ticket IDs from commits (simpler than PR matching)."""
        commit_tickets = {}

        for commit in commit_list:
            commit_sha = commit.get("sha", commit.get("oid", "unknown"))
            ticket_ids = self.ticket_extractor.extract_from_commit(commit)

            if ticket_ids:
                commit_tickets[commit_sha] = ticket_ids

        return commit_tickets

    def _select_primary_ticket(
        self, tickets: list[LinearTicket], title_tickets: set[str]
    ) -> LinearTicket | None:
        """Select the primary ticket from multiple matches."""
        if not tickets:
            return None

        if len(tickets) == 1:
            return tickets[0]

        # Prefer tickets mentioned in the title
        if title_tickets:
            for ticket in tickets:
                if ticket.identifier in title_tickets:
                    return ticket

        # Sort by priority and state
        priority_order = {"started": 0, "unstarted": 1, "backlog": 2, "completed": 3, "canceled": 4}

        sorted_tickets = sorted(
            tickets,
            key=lambda t: (
                priority_order.get(t.state_type, 5),
                t.priority,  # Lower number = higher priority
                t.updated_at or datetime.min,
            ),
        )

        return sorted_tickets[0]

    def _calculate_confidence(
        self,
        ticket_ids: set[str],
        tickets: list[LinearTicket],
        match_sources: list[str],
        pr_data: dict[str, Any],
    ) -> float:
        """Calculate confidence score for the match."""
        if not ticket_ids:
            return 0.0

        confidence = 0.0

        # Base confidence for finding any tickets
        confidence += 0.5

        # Bonus for tickets in title
        if "title" in match_sources:
            confidence += 0.3

        # Bonus for valid tickets fetched
        if tickets:
            valid_ratio = len(tickets) / len(ticket_ids)
            confidence += 0.2 * valid_ratio

        # Penalty for too many tickets (likely false positives)
        if len(ticket_ids) > 3:
            confidence *= 0.8

        return min(confidence, 1.0)

    def get_process_compliance_stats(self, matches: list[PRTicketMatch]) -> dict[str, Any]:
        """Calculate process compliance statistics."""
        total_prs = len(matches)
        prs_with_tickets = sum(1 for m in matches if m.ticket_ids)
        prs_with_valid_tickets = sum(1 for m in matches if m.all_tickets)

        compliance_rate = prs_with_tickets / total_prs if total_prs > 0 else 0
        valid_ticket_rate = prs_with_valid_tickets / total_prs if total_prs > 0 else 0

        # Group by team
        team_stats = defaultdict(lambda: {"total": 0, "with_tickets": 0})

        for match in matches:
            if match.primary_ticket:
                team_key = match.primary_ticket.team_key
                team_stats[team_key]["total"] += 1
                team_stats[team_key]["with_tickets"] += 1
            else:
                team_stats["NO_TICKET"]["total"] += 1

        return {
            "total_prs": total_prs,
            "prs_with_tickets": prs_with_tickets,
            "prs_with_valid_tickets": prs_with_valid_tickets,
            "compliance_rate": compliance_rate,
            "valid_ticket_rate": valid_ticket_rate,
            "team_breakdown": dict(team_stats),
            "avg_confidence": sum(m.match_confidence for m in matches) / total_prs
            if total_prs > 0
            else 0,
        }

    def clear_cache(self):
        """Clear the match cache."""
        self._match_cache.clear()
        self.linear_client.clear_cache()
        logger.info("PR matcher cache cleared")
