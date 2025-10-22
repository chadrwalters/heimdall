#!/usr/bin/env python3
"""Ingest AI usage data from submitted JSON files with deduplication.

Processes all JSON submissions in data/ai_usage/submissions/ and creates
a deduplicated dataset organized by developer and date.

Deduplication strategy: By (developer, date, source) where source is either
'claude_code' or 'codex'. If multiple submissions exist for the same key,
the most recent submission (by collected_at timestamp) wins.
"""

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def load_submissions(submissions_dir: Path) -> List[Dict[str, Any]]:
    """Load all JSON submissions from directory.

    Args:
        submissions_dir: Directory containing submission JSON files

    Returns:
        List of parsed submission objects
    """
    submissions = []

    if not submissions_dir.exists():
        print(f"❌ Submissions directory not found: {submissions_dir}")
        return submissions

    json_files = list(submissions_dir.glob("ai_usage_*.json"))
    print(f"📂 Found {len(json_files)} submission files")

    for json_file in json_files:
        try:
            with open(json_file) as f:
                data = json.load(f)
                data["_source_file"] = json_file.name
                submissions.append(data)
        except Exception as e:
            print(f"⚠️  Error loading {json_file.name}: {e}")
            continue

    return submissions


def deduplicate_data(submissions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Deduplicate submissions by (developer, date, source).

    Args:
        submissions: List of submission objects

    Returns:
        Nested dict: {developer: {date: {source: data}}}
        where source is 'claude_code' or 'codex'
    """
    # Structure: developer -> date -> source -> data
    deduplicated: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(lambda: defaultdict(dict))

    stats = {
        "total_submissions": len(submissions),
        "claude_code_entries": 0,
        "codex_entries": 0,
        "duplicates_removed": 0,
    }

    for submission in submissions:
        try:
            developer = submission["metadata"]["developer"]
            collected_at = datetime.fromisoformat(submission["metadata"]["collected_at"])

            # Process Claude Code data
            claude_data = submission.get("claude_code", {})
            if claude_data and "daily" in claude_data:
                for day_entry in claude_data["daily"]:
                    date = day_entry["date"]

                    # Check if we already have this entry
                    if "claude_code" in deduplicated[developer].get(date, {}):
                        existing_timestamp = deduplicated[developer][date]["claude_code"][
                            "_collected_at"
                        ]
                        if collected_at > existing_timestamp:
                            # This submission is newer, replace
                            deduplicated[developer][date]["claude_code"] = {
                                "data": day_entry,
                                "_collected_at": collected_at,
                                "_source_file": submission["_source_file"],
                            }
                            stats["duplicates_removed"] += 1
                        else:
                            # Keep existing (it's newer)
                            stats["duplicates_removed"] += 1
                    else:
                        # First entry for this key
                        deduplicated[developer][date]["claude_code"] = {
                            "data": day_entry,
                            "_collected_at": collected_at,
                            "_source_file": submission["_source_file"],
                        }
                        stats["claude_code_entries"] += 1

            # Process Codex data
            codex_data = submission.get("codex", {})
            if codex_data and "daily" in codex_data:
                for day_entry in codex_data["daily"]:
                    date = day_entry["date"]

                    # Check if we already have this entry
                    if "codex" in deduplicated[developer].get(date, {}):
                        existing_timestamp = deduplicated[developer][date]["codex"]["_collected_at"]
                        if collected_at > existing_timestamp:
                            # This submission is newer, replace
                            deduplicated[developer][date]["codex"] = {
                                "data": day_entry,
                                "_collected_at": collected_at,
                                "_source_file": submission["_source_file"],
                            }
                            stats["duplicates_removed"] += 1
                        else:
                            # Keep existing (it's newer)
                            stats["duplicates_removed"] += 1
                    else:
                        # First entry for this key
                        deduplicated[developer][date]["codex"] = {
                            "data": day_entry,
                            "_collected_at": collected_at,
                            "_source_file": submission["_source_file"],
                        }
                        stats["codex_entries"] += 1

        except Exception as e:
            print(
                f"⚠️  Error processing submission {submission.get('_source_file', 'unknown')}: {e}"
            )
            continue

    return deduplicated, stats


def write_ingested_data(deduplicated: Dict, output_dir: Path) -> None:
    """Write deduplicated data to structured JSON files.

    Args:
        deduplicated: Deduplicated data structure
        output_dir: Directory to write output files
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write per-developer files
    for developer, dates in deduplicated.items():
        developer_file = output_dir / f"{developer.lower()}_ingested.json"

        # Convert to serializable format and sort by date
        output_data = {
            "developer": developer,
            "ingested_at": datetime.now().isoformat(),
            "days": [],
        }

        for date in sorted(dates.keys()):
            day_data = {"date": date, "claude_code": None, "codex": None}

            if "claude_code" in dates[date]:
                entry = dates[date]["claude_code"]
                day_data["claude_code"] = {
                    **entry["data"],
                    "_metadata": {
                        "collected_at": entry["_collected_at"].isoformat(),
                        "source_file": entry["_source_file"],
                    },
                }

            if "codex" in dates[date]:
                entry = dates[date]["codex"]
                day_data["codex"] = {
                    **entry["data"],
                    "_metadata": {
                        "collected_at": entry["_collected_at"].isoformat(),
                        "source_file": entry["_source_file"],
                    },
                }

            output_data["days"].append(day_data)

        with open(developer_file, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"   📝 {developer}: {len(output_data['days'])} days → {developer_file.name}")


def main():
    """Main entry point."""
    print("📊 AI Usage Data Ingestion")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Setup paths
    base_dir = Path("data/ai_usage")
    submissions_dir = base_dir / "submissions"
    output_dir = base_dir / "ingested"

    # Load submissions
    print("\n🔍 Loading submissions...")
    submissions = load_submissions(submissions_dir)

    if not submissions:
        print("❌ No submissions found to process")
        sys.exit(1)

    # Deduplicate
    print("\n🔄 Deduplicating data...")
    deduplicated, stats = deduplicate_data(submissions)

    print(f"   ✅ Processed {stats['total_submissions']} submissions")
    print(f"   ✅ Claude Code entries: {stats['claude_code_entries']}")
    print(f"   ✅ Codex entries: {stats['codex_entries']}")
    print(f"   ⚠️  Duplicates removed: {stats['duplicates_removed']}")

    # Write output
    print("\n💾 Writing ingested data...")
    write_ingested_data(deduplicated, output_dir)

    print("\n✅ Ingestion complete!")
    print(f"   Output: {output_dir}")


if __name__ == "__main__":
    main()
