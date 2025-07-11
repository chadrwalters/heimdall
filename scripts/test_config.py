#!/usr/bin/env python3
"""Test script to demonstrate configuration management functionality."""

import sys

sys.path.insert(0, ".")

from src.config.config_manager import ConfigManager
from src.config.state_manager import StateManager


def main():
    """Test configuration management functionality."""
    print("=" * 50)
    print("Configuration Management Test")
    print("=" * 50)

    # Test ConfigManager
    print("\n1. Testing ConfigManager...")
    config_mgr = ConfigManager()

    # Load AI developers
    ai_devs = config_mgr.load_ai_developers()
    print(f"   AI Developers: {ai_devs}")

    # Check if 'chad' is an AI developer
    chad_info = config_mgr.get_ai_developer_info(username="chad")
    if chad_info:
        print(f"   Found AI developer 'chad': {chad_info}")

    # Load analysis state
    state = config_mgr.load_analysis_state()
    print(f"   Analysis State: Total records processed = {state['total_records_processed']}")

    # Test StateManager
    print("\n2. Testing StateManager...")
    state_mgr = StateManager()

    # Get statistics
    stats = state_mgr.get_statistics()
    print(f"   Statistics: {stats}")

    # Get date range for incremental update
    start_date, end_date = state_mgr.get_date_range_for_incremental_update()
    print(f"   Date range for next run: {start_date.isoformat()} to {end_date.isoformat()}")

    # Test PR/Commit tracking
    print("\n3. Testing ID tracking...")
    test_pr = "PR-TEST-001"
    test_commit = "abc123def456"

    print(f"   Is {test_pr} processed? {state_mgr.is_pr_processed(test_pr)}")
    print(f"   Is {test_commit} processed? {state_mgr.is_commit_processed(test_commit)}")

    print("\n✅ Configuration management is working correctly!")


if __name__ == "__main__":
    main()
