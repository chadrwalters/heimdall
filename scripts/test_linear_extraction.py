#!/usr/bin/env python3
"""Test Linear tickets extraction separately."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def main():
    org = sys.argv[1] if len(sys.argv) > 1 else "test-org"
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7

    print(f"Testing LINEAR extraction for {org} ({days} days)...")
    print("=" * 80)

    linear_token = os.getenv("LINEAR_API_KEY") or os.getenv("LINEAR_TOKEN")

    if not linear_token:
        print("❌ LINEAR_API_KEY or LINEAR_TOKEN not set")
        sys.exit(1)

    print("✅ Linear API key found")
    print("\n⚠️ Linear extraction is currently not integrated into the main pipeline")
    print("   This would require implementing Linear API client and extraction logic")
    print("\nFor now, run: just test-linear")


if __name__ == "__main__":
    main()
