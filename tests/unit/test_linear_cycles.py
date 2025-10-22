"""Tests for Linear cycle extraction."""

import pytest
from unittest.mock import Mock, MagicMock
from src.linear.linear_client import LinearClient


@pytest.fixture
def mock_linear_client():
    """Create a mock Linear client for testing cycle methods."""
    # Create a mock client with minimal setup
    client = LinearClient.__new__(LinearClient)
    client.rate_limiter = MagicMock()
    client.query_validator = MagicMock()
    client.query_validator.validate_query = MagicMock(side_effect=lambda q, v: (q, v))
    client.session = MagicMock()
    client._request_count = 0
    return client


def test_get_cycles_method_exists(mock_linear_client):
    """Test that get_cycles method exists."""
    assert hasattr(mock_linear_client, "get_cycles")


def test_get_cycles(mock_linear_client):
    """Test retrieving cycles from Linear."""
    # Mock successful API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "cycles": {
                "nodes": [
                    {
                        "id": "cycle1",
                        "number": 42,
                        "name": "Sprint 42",
                        "startsAt": "2024-12-18T00:00:00.000Z",
                        "endsAt": "2024-12-31T23:59:59.999Z",
                        "completedAt": "2024-12-31T20:00:00.000Z",
                        "team": {"id": "team1", "key": "ENG", "name": "Engineering"},
                        "completedIssueCount": 5,
                        "issueCount": 10,
                        "progress": 50,
                    }
                ]
            }
        }
    }
    mock_linear_client.session.post.return_value = mock_response

    cycles = mock_linear_client.get_cycles(team_key="ENG")

    assert len(cycles) == 1
    assert cycles[0]["number"] == 42
    assert cycles[0]["name"] == "Sprint 42"
    assert cycles[0]["team"]["key"] == "ENG"


def test_get_cycle_issues_method_exists(mock_linear_client):
    """Test that get_cycle_issues method exists."""
    assert hasattr(mock_linear_client, "get_cycle_issues")


def test_get_cycle_issues(mock_linear_client):
    """Test retrieving issues for a cycle."""
    # Mock successful API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "cycle": {
                "issues": {
                    "nodes": [
                        {
                            "id": "issue1",
                            "identifier": "ENG-123",
                            "title": "Implement feature",
                            "estimate": 3,
                            "assignee": {
                                "id": "user1",
                                "name": "Chad Walters",
                                "email": "chad@example.com",
                            },
                            "state": {"id": "state1", "name": "Done", "type": "completed"},
                            "completedAt": "2024-12-25T10:00:00.000Z",
                            "team": {"id": "team1", "key": "ENG", "name": "Engineering"},
                        }
                    ]
                }
            }
        }
    }
    mock_linear_client.session.post.return_value = mock_response

    issues = mock_linear_client.get_cycle_issues("cycle1")

    assert len(issues) == 1
    assert issues[0]["identifier"] == "ENG-123"
    assert issues[0]["estimate"] == 3
    assert issues[0]["assignee"]["name"] == "Chad Walters"
