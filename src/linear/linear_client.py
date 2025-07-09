"""Linear API client for interacting with Linear GraphQL API."""

import logging
import time
from datetime import datetime
from functools import lru_cache
from typing import Any

import requests

from ..security.key_manager import EnvironmentKeyManager, KeySecurityError, SecureKeyManager
from ..validation.graphql_validator import GraphQLValidator, ValidationError

logger = logging.getLogger(__name__)


class LinearClient:
    """Client for interacting with Linear's GraphQL API."""

    BASE_URL = "https://api.linear.app/graphql"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RATE_LIMIT_DELAY = 1.0  # seconds between requests

    def __init__(self, api_key: str | None = None):
        """Initialize Linear client."""
        self.secure_manager = SecureKeyManager()
        self.env_manager = EnvironmentKeyManager(self.secure_manager)

        try:
            if api_key:
                # Validate provided key
                if not self.secure_manager.validate_api_key(api_key, "linear"):
                    logger.warning("Provided Linear API key failed validation checks")
                self.api_key = api_key
            else:
                # Try both environment variables
                try:
                    self.api_key = self.env_manager.get_api_key(
                        "LINEAR_API_KEY", "linear", required=True
                    )
                except KeySecurityError:
                    self.api_key = self.env_manager.get_api_key(
                        "LINEAR_TOKEN", "linear", required=True
                    )
        except KeySecurityError as e:
            raise ValueError(f"Failed to initialize Linear client: {e}")

        self.headers = {"Authorization": self.api_key, "Content-Type": "application/json"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self._last_request_time = 0
        self._request_count = 0
        self.query_validator = GraphQLValidator()

    def _rate_limit(self):
        """Implement rate limiting between requests."""
        current_time = time.time()
        elapsed = current_time - self._last_request_time

        if elapsed < self.RATE_LIMIT_DELAY:
            sleep_time = self.RATE_LIMIT_DELAY - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _execute_query(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a GraphQL query with retry logic and security validation."""
        # Validate and sanitize query and variables
        try:
            sanitized_query, sanitized_variables = self.query_validator.validate_query(
                query, variables
            )
        except ValidationError as e:
            logger.error(f"GraphQL query validation failed: {e}")
            raise ValueError(f"Invalid GraphQL query: {e}")

        self._rate_limit()

        payload = {"query": sanitized_query}
        if sanitized_variables:
            payload["variables"] = sanitized_variables

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.post(
                    self.BASE_URL, json=payload, timeout=self.DEFAULT_TIMEOUT
                )
                self._request_count += 1

                if response.status_code == 200:
                    data = response.json()
                    if "errors" in data:
                        logger.error(f"GraphQL errors: {data['errors']}")
                        raise Exception(f"GraphQL errors: {data['errors']}")
                    return data.get("data", {})
                elif response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited. Retrying after {retry_after}s")
                    time.sleep(retry_after)
                else:
                    logger.error(
                        f"Request failed with status {response.status_code}: {response.text}"
                    )
                    if attempt < self.MAX_RETRIES - 1:
                        time.sleep(2**attempt)  # Exponential backoff
                    else:
                        raise Exception(f"Request failed: {response.status_code}")

            except requests.exceptions.Timeout:
                logger.error(f"Request timeout (attempt {attempt + 1}/{self.MAX_RETRIES})")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(2**attempt)
                else:
                    raise
            except Exception as e:
                logger.error(f"Request error: {str(e)}")
                raise

        raise Exception("Max retries exceeded")

    def get_viewer(self) -> dict[str, Any]:
        """Get information about the authenticated user."""
        query = """
        query {
            viewer {
                id
                email
                name
                admin
            }
        }
        """
        result = self._execute_query(query)
        return result.get("viewer", {})

    def get_issue_by_id(self, issue_id: str) -> dict[str, Any] | None:
        """Get a single issue by its ID (e.g., 'ENG-1234')."""
        query = """
        query GetIssue($id: String!) {
            issue(id: $id) {
                id
                identifier
                title
                description
                state {
                    id
                    name
                    type
                }
                assignee {
                    id
                    name
                    email
                }
                creator {
                    id
                    name
                    email
                }
                createdAt
                updatedAt
                completedAt
                priority
                priorityLabel
                estimate
                project {
                    id
                    name
                }
                team {
                    id
                    key
                    name
                }
                labels {
                    nodes {
                        id
                        name
                        color
                    }
                }
                url
            }
        }
        """

        try:
            result = self._execute_query(query, {"id": issue_id})
            return result.get("issue")
        except Exception as e:
            logger.error(f"Error fetching issue {issue_id}: {str(e)}")
            return None

    @lru_cache(maxsize=1000)
    def get_issue_cached(self, issue_id: str) -> dict[str, Any] | None:
        """Get issue with caching to reduce API calls."""
        return self.get_issue_by_id(issue_id)

    def get_issues_by_ids(self, issue_ids: list[str]) -> dict[str, dict[str, Any]]:
        """Get multiple issues by their IDs efficiently."""
        # GraphQL doesn't support batch queries easily, so we'll use individual queries
        # but with caching and rate limiting
        issues = {}

        for issue_id in issue_ids:
            issue = self.get_issue_cached(issue_id)
            if issue:
                issues[issue_id] = issue
            else:
                logger.warning(f"Issue {issue_id} not found or inaccessible")

        return issues

    def search_issues(
        self,
        team_key: str | None = None,
        created_after: datetime | None = None,
        updated_after: datetime | None = None,
        state_type: str | None = None,
        assignee_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Search for issues with various filters."""
        filters = []

        if team_key:
            filters.append(f'team: {{ key: {{ eq: "{team_key}" }} }}')

        if created_after:
            filters.append(f'createdAt: {{ gte: "{created_after.isoformat()}" }}')

        if updated_after:
            filters.append(f'updatedAt: {{ gte: "{updated_after.isoformat()}" }}')

        if state_type:
            filters.append(f'state: {{ type: {{ eq: "{state_type}" }} }}')

        if assignee_id:
            filters.append(f'assignee: {{ id: {{ eq: "{assignee_id}" }} }}')

        filter_str = ""
        if filters:
            filter_str = f"filter: {{ {', '.join(filters)} }}"

        query = f"""
        query SearchIssues {{
            issues({filter_str}, first: {limit}) {{
                nodes {{
                    id
                    identifier
                    title
                    description
                    state {{
                        id
                        name
                        type
                    }}
                    assignee {{
                        id
                        name
                        email
                    }}
                    createdAt
                    updatedAt
                    priority
                    team {{
                        id
                        key
                        name
                    }}
                    url
                }}
                pageInfo {{
                    hasNextPage
                    endCursor
                }}
            }}
        }}
        """

        result = self._execute_query(query)
        issues_data = result.get("issues", {})
        return issues_data.get("nodes", [])

    def get_teams(self) -> list[dict[str, Any]]:
        """Get all teams in the workspace."""
        query = """
        query {
            teams {
                nodes {
                    id
                    key
                    name
                    description
                    issueCount
                }
            }
        }
        """

        result = self._execute_query(query)
        teams_data = result.get("teams", {})
        return teams_data.get("nodes", [])

    def get_projects(self, team_id: str | None = None) -> list[dict[str, Any]]:
        """Get projects, optionally filtered by team."""
        filter_str = ""
        if team_id:
            filter_str = f'(filter: {{ team: {{ id: {{ eq: "{team_id}" }} }} }})'

        query = f"""
        query {{
            projects{filter_str} {{
                nodes {{
                    id
                    name
                    description
                    state
                    startDate
                    targetDate
                    team {{
                        id
                        key
                        name
                    }}
                    lead {{
                        id
                        name
                        email
                    }}
                    issueCount
                    completedIssueCount
                    url
                }}
            }}
        }}
        """

        result = self._execute_query(query)
        projects_data = result.get("projects", {})
        return projects_data.get("nodes", [])

    def get_issue_states(self, team_id: str | None = None) -> list[dict[str, Any]]:
        """Get workflow states, optionally filtered by team."""
        filter_str = ""
        if team_id:
            filter_str = f'(filter: {{ team: {{ id: {{ eq: "{team_id}" }} }} }})'

        query = f"""
        query {{
            workflowStates{filter_str} {{
                nodes {{
                    id
                    name
                    type
                    color
                    position
                    team {{
                        id
                        key
                        name
                    }}
                }}
            }}
        }}
        """

        result = self._execute_query(query)
        states_data = result.get("workflowStates", {})
        return states_data.get("nodes", [])

    def clear_cache(self):
        """Clear the issue cache."""
        self.get_issue_cached.cache_clear()
        logger.info("Linear client cache cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get client statistics."""
        return {
            "request_count": self._request_count,
            "cache_info": self.get_issue_cached.cache_info()._asdict(),
        }
