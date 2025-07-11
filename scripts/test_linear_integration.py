#!/usr/bin/env python3
"""Test Linear API integration."""

import os
import sys
from datetime import datetime, timedelta

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from linear import LinearClient, PRTicketMatcher, TicketExtractor


def test_linear_client():
    """Test Linear API client."""
    print("=" * 60)
    print("Testing Linear API Client")
    print("=" * 60)

    try:
        # Initialize client
        client = LinearClient()

        # Test viewer endpoint
        print("\n1. Testing viewer endpoint...")
        viewer = client.get_viewer()
        print(
            f"✅ Authenticated as: {viewer.get('name', 'Unknown')} ({viewer.get('email', 'Unknown')})"
        )

        # Test teams
        print("\n2. Testing teams endpoint...")
        teams = client.get_teams()
        print(f"✅ Found {len(teams)} teams")
        for team in teams[:3]:  # Show first 3
            print(f"   - {team['key']}: {team['name']}")

        # Test single issue (if we know an ID)
        print("\n3. Testing issue fetch...")
        test_issue_id = "ENG-1"  # Common first issue
        issue = client.get_issue_by_id(test_issue_id)
        if issue:
            print(f"✅ Found issue: {issue['identifier']} - {issue['title']}")
        else:
            print(f"ℹ️  Issue {test_issue_id} not found (may not exist)")

        # Test search
        print("\n4. Testing issue search...")
        recent_issues = client.search_issues(
            created_after=datetime.now() - timedelta(days=30), limit=5
        )
        print(f"✅ Found {len(recent_issues)} recent issues")

        return True

    except Exception as e:
        print(f"❌ Error testing Linear client: {str(e)}")
        return False


def test_ticket_extractor():
    """Test ticket extraction."""
    print("\n" + "=" * 60)
    print("Testing Ticket Extractor")
    print("=" * 60)

    test_cases = [
        ("Fix: Updated auth logic ENG-1234", {"ENG-1234"}),
        ("Implement new feature [PROD-567] and fix ENG-890", {"PROD-567", "ENG-890"}),
        ("Closes linear.app/company/issue/API-123", {"API-123"}),
        ("No tickets in this text", set()),
        ("Multiple formats: ticket:ENG-1, fixes ENG-2, (ENG-3)", {"ENG-1", "ENG-2", "ENG-3"}),
    ]

    extractor = TicketExtractor()
    all_passed = True

    for text, expected in test_cases:
        result = extractor.extract_ticket_ids(text)
        passed = result == expected
        status = "✅" if passed else "❌"
        print(f"{status} '{text}' -> {result}")
        if not passed:
            print(f"   Expected: {expected}")
            all_passed = False

    return all_passed


def test_pr_matcher():
    """Test PR matching."""
    print("\n" + "=" * 60)
    print("Testing PR Matcher")
    print("=" * 60)

    # Sample PR data
    test_pr = {
        "id": 123,
        "number": 123,
        "title": "Add authentication feature ENG-456",
        "body": "This PR implements JWT auth as described in ENG-456.\n\nAlso fixes a bug from PROD-789.",
        "html_url": "https://github.com/test/repo/pull/123",
        "user": {"login": "testuser"},
        "created_at": "2024-01-01T00:00:00Z",
    }

    try:
        client = LinearClient()
        matcher = PRTicketMatcher(client)

        print("\nMatching PR with Linear tickets...")
        match = matcher.match_pr(test_pr)

        print("\n✅ Match Results:")
        print(f"   PR: #{match.pr_number} - {match.pr_title}")
        print(f"   Found tickets: {match.ticket_ids}")
        print(f"   Match sources: {match.match_sources}")
        print(f"   Confidence: {match.match_confidence:.2f}")

        if match.primary_ticket:
            print(
                f"   Primary ticket: {match.primary_ticket.identifier} - {match.primary_ticket.title}"
            )
            print(f"   Team: {match.primary_ticket.team_name}")
            print(f"   State: {match.primary_ticket.state}")
        else:
            print("   Primary ticket: None found or accessible")

        return True

    except Exception as e:
        print(f"❌ Error testing PR matcher: {str(e)}")
        return False


def test_batch_operations():
    """Test batch operations."""
    print("\n" + "=" * 60)
    print("Testing Batch Operations")
    print("=" * 60)

    # Sample data
    test_prs = [
        {"id": 1, "number": 1, "title": "Initial setup", "body": "Setting up the project"},
        {
            "id": 2,
            "number": 2,
            "title": "Add feature ABC-123",
            "body": "Implements the feature from ABC-123",
        },
        {
            "id": 3,
            "number": 3,
            "title": "Fix bug in auth",
            "body": "Fixes issue reported in ENG-789 and ENG-790",
        },
    ]

    try:
        extractor = TicketExtractor()

        # Test batch extraction
        pr_tickets = extractor.batch_extract_from_prs(test_prs)

        print("\n✅ Batch extraction results:")
        for pr_id, tickets in pr_tickets.items():
            print(f"   PR {pr_id}: {tickets}")

        # Test compliance stats
        client = LinearClient()
        matcher = PRTicketMatcher(client)

        print("\n📊 Testing compliance statistics...")
        matches = []
        for pr in test_prs:
            match = matcher.match_pr(pr)
            matches.append(match)

        stats = matcher.get_process_compliance_stats(matches)
        print("\n✅ Compliance Stats:")
        print(f"   Total PRs: {stats['total_prs']}")
        print(f"   PRs with tickets: {stats['prs_with_tickets']}")
        print(f"   Compliance rate: {stats['compliance_rate']:.1%}")
        print(f"   Average confidence: {stats['avg_confidence']:.2f}")

        return True

    except Exception as e:
        print(f"❌ Error testing batch operations: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("North Star Metrics - Linear Integration Test")
    print("=" * 60)

    # Check for API key
    if not os.getenv("LINEAR_API_KEY") and not os.getenv("LINEAR_TOKEN"):
        print("❌ LINEAR_API_KEY not found in environment")
        print("   Please set it to run integration tests")
        print("\n📝 Running extraction tests only...")

        # Run only extraction tests
        test_ticket_extractor()
        return 1

    # Run all tests
    tests = [
        ("Linear Client", test_linear_client),
        ("Ticket Extractor", test_ticket_extractor),
        ("PR Matcher", test_pr_matcher),
        ("Batch Operations", test_batch_operations),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ Test '{name}' failed with error: {str(e)}")
            results[name] = False

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
