#!/usr/bin/env python3
"""Verify API access to GitHub, Linear, and Anthropic services."""

import json
import os
import subprocess
import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def verify_github_api():
    """Verify GitHub API access using gh CLI."""
    print("🔍 Verifying GitHub API access...")
    try:
        # Test gh CLI authentication
        result = subprocess.run(["gh", "api", "user"], capture_output=True, text=True)
        if result.returncode == 0:
            user_data = json.loads(result.stdout)
            print(f"✅ GitHub API: Authenticated as {user_data.get('login', 'unknown')}")
            return True
        else:
            print(f"❌ GitHub API: Authentication failed - {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ GitHub API: Error - {str(e)}")
        return False


def verify_linear_api():
    """Verify Linear API access."""
    print("\n🔍 Verifying Linear API access...")
    try:
        import requests

        api_key = os.getenv("LINEAR_API_KEY") or os.getenv("LINEAR_TOKEN")
        if not api_key:
            print("❌ Linear API: No API key found in environment")
            return False

        headers = {"Authorization": api_key, "Content-Type": "application/json"}

        # Simple GraphQL query to get viewer info
        query = {"query": "{ viewer { id email name } }"}

        response = requests.post("https://api.linear.app/graphql", headers=headers, json=query)

        if response.status_code == 200:
            data = response.json()
            if "data" in data and "viewer" in data["data"]:
                viewer = data["data"]["viewer"]
                print(f"✅ Linear API: Authenticated as {viewer.get('name', 'unknown')}")
                return True
            else:
                print(f"❌ Linear API: Unexpected response - {data}")
                return False
        else:
            print(f"❌ Linear API: Request failed with status {response.status_code}")
            return False

    except ImportError:
        print("❌ Linear API: requests library not installed")
        return False
    except Exception as e:
        print(f"❌ Linear API: Error - {str(e)}")
        return False


def verify_anthropic_api():
    """Verify Anthropic API access."""
    print("\n🔍 Verifying Anthropic API access...")
    try:
        from anthropic import Anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("❌ Anthropic API: No API key found in environment")
            return False

        client = Anthropic(api_key=api_key)

        # Simple test message
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'API verified'"}],
        )

        if response and response.content:
            print(f"✅ Anthropic API: Successfully connected - {response.content[0].text}")
            return True
        else:
            print("❌ Anthropic API: Unexpected response")
            return False

    except ImportError as e:
        print(f"❌ Anthropic API: Import error - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Anthropic API: Error - {str(e)}")
        return False


def main():
    """Run all API verification tests."""
    print("=" * 50)
    print("North Star Project - API Verification")
    print("=" * 50)

    results = {
        "GitHub": verify_github_api(),
        "Linear": verify_linear_api(),
        "Anthropic": verify_anthropic_api(),
    }

    print("\n" + "=" * 50)
    print("Summary:")
    print("=" * 50)

    all_passed = True
    for service, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{service}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n✅ All API verifications passed!")
        return 0
    else:
        print("\n❌ Some API verifications failed. Please check your configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
