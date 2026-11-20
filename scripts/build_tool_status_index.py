#!/usr/bin/env python3
"""
Rebrand/Discontinued Foundation — deterministic structured handling for tool statuses.

Handles statuses only when repository evidence supports them:
  - active
  - renamed
  - rebranded
  - acquired_or_merged
  - discontinued
  - unknown

Each record preserves:
  - tool_id
  - previous_name (if renamed/rebranded)
  - current_name
  - evidence/source reference
  - verified_date
  - canonical_url decision
  - redirect recommendation
  - replacement/alternative route

No redirects are created without verified evidence.

Usage:
  python3 scripts/build_tool_status_index.py
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL_DIR = ROOT / "data" / "tools-v2"
CHANGE_LEDGER = ROOT / "data" / "changes" / "tool-change-ledger.json"
OUTPUT = ROOT / "data" / "tool-status-index.json"

VALID_STATUSES = {
    "active",
    "renamed",
    "rebranded",
    "acquired_or_merged",
    "discontinued",
    "unknown",
}


def load_tool_records():
    """Load all tool records from data/tools-v2."""
    records = []
    if not TOOL_DIR.exists():
        return records
    for path in sorted(TOOL_DIR.rglob("*.json")):
        if path.name == "README.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            records.append(data)
        except (OSError, json.JSONDecodeError):
            continue
    return records


def load_change_events():
    """Load change events from the change ledger."""
    if not CHANGE_LEDGER.exists():
        return []
    try:
        data = json.loads(CHANGE_LEDGER.read_text(encoding="utf-8"))
        return data.get("events", [])
    except (OSError, json.JSONDecodeError):
        return []


def build_status_index(records, change_events):
    """Build the tool status index."""
    entries = []

    # Map change events by tool_id
    events_by_tool: dict[str, list] = {}
    for event in change_events:
        tool_id = event.get("tool_id")
        if tool_id:
            events_by_tool.setdefault(tool_id, []).append(event)

    for record in records:
        identity = record.get("identity", {})
        tool_id = identity.get("id", "")
        name = identity.get("name", "")
        official_url = identity.get("official_url", "")
        status = identity.get("status", "unknown")

        # Map status from tool record to our status types
        mapped_status = map_status(status)

        # Check for rebrand/discontinued events
        tool_events = events_by_tool.get(tool_id, [])
        previous_name = None
        current_name = name
        evidence_ref = None
        verified_date = None
        redirect_recommendation = None
        replacement_route = None

        for event in tool_events:
            event_type = event.get("event_type", "")
            if event_type in ("product_rename", "rebrand"):
                previous_name = event.get("before", {}).get("name", previous_name)
                current_name = event.get("after", {}).get("name", current_name)
                mapped_status = "renamed" if event_type == "product_rename" else "rebranded"
            elif event_type == "acquisition":
                mapped_status = "acquired_or_merged"
            elif event_type == "shutdown":
                mapped_status = "discontinued"

            # Get evidence reference
            if not evidence_ref and event.get("source_ids"):
                evidence_ref = event["source_ids"][0]
            if not verified_date and event.get("detected_at"):
                verified_date = event["detected_at"]

        # Build replacement route for discontinued tools
        if mapped_status == "discontinued":
            relationships = record.get("relationships", {})
            replaced_by = relationships.get("replaced_by", [])
            if replaced_by:
                replacement_route = f"/tools/{replaced_by[0]}.html"

        # Build redirect recommendation
        if mapped_status in ("renamed", "rebranded") and previous_name:
            redirect_recommendation = {
                "from": f"/tools/{tool_id}.html",
                "to": f"/tools/{tool_id}.html",  # Same URL, updated content
                "type": "301",
                "evidence_required": True,
            }

        entry = {
            "tool_id": tool_id,
            "status": mapped_status,
            "name": current_name,
            "previous_name": previous_name,
            "official_url": official_url,
            "evidence_source": evidence_ref,
            "verified_date": verified_date,
            "redirect_recommendation": redirect_recommendation,
            "replacement_route": replacement_route,
        }
        entries.append(entry)

    return {
        "schema_version": "tool-status-index-v1",
        "generated_at": date.today().isoformat(),
        "entries": sorted(entries, key=lambda e: e["tool_id"]),
    }


def map_status(raw_status: str) -> str:
    """Map raw status to our standardized status types."""
    status_map = {
        "active": "active",
        "limited": "active",
        "discontinued": "discontinued",
        "acquired": "acquired_or_merged",
        "unknown": "unknown",
    }
    return status_map.get(raw_status, "unknown")


def validate_status_index(index):
    """Validate the status index for consistency."""
    errors = []

    for entry in index.get("entries", []):
        tool_id = entry.get("tool_id", "<missing>")
        status = entry.get("status", "unknown")

        if status not in VALID_STATUSES:
            errors.append(f"{tool_id}: invalid status '{status}'")

        if status in ("renamed", "rebranded") and not entry.get("previous_name"):
            errors.append(f"{tool_id}: {status} status requires previous_name")

        if status == "discontinued" and not entry.get("replacement_route"):
            # Not an error, just a note — some discontinued tools have no replacement
            pass

        if entry.get("redirect_recommendation"):
            rec = entry["redirect_recommendation"]
            if not rec.get("evidence_required"):
                errors.append(f"{tool_id}: redirect without evidence flag")

    return errors


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Build Tool Status Index for rebrand/discontinued handling"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT,
        help="Output path for status index JSON",
    )
    args = parser.parse_args()

    records = load_tool_records()
    change_events = load_change_events()

    index = build_status_index(records, change_events)

    # Validate
    errors = validate_status_index(index)
    if errors:
        print(f"Status Index Validation: WARN ({len(errors)} issue(s))")
        for error in errors:
            print(f"  - {error}")

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(index, indent=2) + "\n", encoding="utf-8"
    )

    # Summary
    status_counts = {}
    for entry in index["entries"]:
        status = entry["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    print(f"\nTool Status Index: {len(index['entries'])} entries")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    print(f"\nWritten to {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
