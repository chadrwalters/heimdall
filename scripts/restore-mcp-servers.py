#!/usr/bin/env python3
"""
Script to restore missing MCP servers for Claude Code
Usage: python restore-mcp-servers.py [--dry-run]
"""

import argparse
import json
import subprocess

# Expected MCP server configurations
EXPECTED_SERVERS = {
    "zen": {
        "type": "stdio",
        "command": "/Users/chadwalters/source/work/zen-mcp-server/.zen_venv/bin/python",
        "args": ["/Users/chadwalters/source/work/zen-mcp-server/server.py"],
    },
    "linear": {
        "type": "stdio",
        "command": "npx",
        "args": ["mcp-remote", "https://mcp.linear.app/sse"],
    },
    "notion": {"type": "stdio", "command": "npx", "args": ["-y", "@notionhq/notion-mcp-server"]},
    "playwright": {"type": "stdio", "command": "npx", "args": ["@playwright/mcp@latest"]},
}


def get_current_servers() -> dict[str, str]:
    """Get currently configured MCP servers."""
    try:
        result = subprocess.run(
            ["claude", "mcp", "list"], capture_output=True, text=True, check=True
        )

        servers = {}
        output = result.stdout.strip()

        # Handle case where no servers are configured
        if "No MCP servers configured" in output:
            return servers

        for line in output.split("\n"):
            if ":" in line and not line.startswith(" "):  # Skip indented lines
                name, command = line.split(":", 1)
                servers[name.strip()] = command.strip()

        return servers
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to get MCP server list: {e}")
        return {}
    except FileNotFoundError:
        print("❌ Claude CLI not found. Please ensure Claude CLI is installed and in PATH.")
        return {}


def find_missing_servers(current: dict[str, str], expected: dict[str, dict]) -> set[str]:
    """Find servers that are missing or have incorrect configurations."""
    missing = set()

    for name, config in expected.items():
        if name not in current:
            missing.add(name)
        else:
            # For now, just check if it exists (harder to validate exact command format)
            pass

    return missing


def add_server(name: str, config: dict, dry_run: bool = False) -> bool:
    """Add a single MCP server."""
    if dry_run:
        print(f"🔍 Would add: {name} -> {json.dumps(config)}")
        return True

    try:
        if config["type"] == "stdio":
            # Use add-json for stdio servers
            json_config = {"command": config["command"], "args": config["args"]}
            cmd_parts = ["claude", "mcp", "add-json", name, json.dumps(json_config)]
        elif config["type"] == "sse":
            # Use regular add for SSE servers
            cmd_parts = ["claude", "mcp", "add", name, config["url"]]
        else:
            print(f"❌ Unknown server type for {name}: {config['type']}")
            return False

        subprocess.run(cmd_parts, capture_output=True, text=True, check=True)
        print(f"✅ Successfully added {name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to add {name}: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Restore missing Claude MCP servers")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without making changes"
    )
    args = parser.parse_args()

    print("🔍 Checking MCP server configuration...")

    # Get current configuration
    current_servers = get_current_servers()
    # Don't exit if empty - that's a valid state when no servers are configured

    # Find missing servers
    missing_servers = find_missing_servers(current_servers, EXPECTED_SERVERS)

    # Report status
    for name in EXPECTED_SERVERS:
        if name in missing_servers:
            print(f"❌ Missing: {name}")
        else:
            print(f"✅ Found: {name}")

    if not missing_servers:
        print("🎉 All MCP servers are configured correctly!")
        return

    # Restore missing servers
    if args.dry_run:
        print(f"\n🔍 Dry run: Would restore {len(missing_servers)} server(s)")
    else:
        print(f"\n🔧 Restoring {len(missing_servers)} missing server(s)...")

    success_count = 0
    for server_name in missing_servers:
        server_config = EXPECTED_SERVERS[server_name]
        if add_server(server_name, server_config, args.dry_run):
            success_count += 1

    if not args.dry_run:
        print(f"\n📊 Results: {success_count}/{len(missing_servers)} servers restored successfully")

        if success_count > 0:
            print("\n🔍 Verifying restored configuration...")
            subprocess.run(["claude", "mcp", "list"])

        print("\n⚠️  Note: You may need to restart Claude Code for MCP servers to work properly.")

    print("\n✨ MCP server restoration complete!")


if __name__ == "__main__":
    main()
