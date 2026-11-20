#!/usr/bin/env python3
"""
Build Change History — derives change events from evidence ledger data.

Reads:
- data/evidence/evidence-ledger.json (claims, disputes, replacements, audit_trail)
- data/changes/tool-change-ledger.json (existing events, append-only)

Produces updated:
- data/changes/tool-change-ledger.json

Rules:
1. Each dispute in the evidence ledger becomes a verification_correction event.
2. Each replacement becomes an evidence_update event.
3. Stale claims with no replacement become a detected event (not verified).
4. No historical product changes are invented — only what the evidence ledger shows.
5. Existing events are preserved; new events are appended with unique IDs.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

REFERENCE_DATE = "2026-11-20"
EVIDENCE_LEDGER_PATH = "data/evidence/evidence-ledger.json"
CHANGE_LEDGER_PATH = "data/changes/tool-change-ledger.json"
TOOLS_V2_DIR = "data/tools-v2"


def load_json(path):
    with open(path) as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def find_tool_pages(tool_id):
    """Find all HTML pages that reference a tool_id."""
    pages = []
    # Check tools directory
    tool_page = f"/tools/{tool_id}.html"
    pages.append(tool_page)

    # Scan tools-v2 for comparison and alternative references
    for subdir in ["legacy", "expansion"]:
        v2_dir = os.path.join(TOOLS_V2_DIR, subdir)
        if not os.path.isdir(v2_dir):
            continue
        for fname in os.listdir(v2_dir):
            if not fname.endswith(".json"):
                continue
            record = load_json(os.path.join(v2_dir, fname))
            relationships = record.get("relationships", {})
            all_refs = []
            for key in ["alternatives", "meaningful_comparisons", "related_tools", "compatible_tools"]:
                all_refs.extend(relationships.get(key, []))
            if tool_id in all_refs:
                other_id = fname.replace(".json", "")
                pages.append(f"/tools/{other_id}.html")
                # Add compare page if in meaningful_comparisons
                if tool_id in relationships.get("meaningful_comparisons", []):
                    pages.append(f"/compare/{other_id}-vs-{tool_id}.html")
                    pages.append(f"/compare/{tool_id}-vs-{other_id}.html")

    return sorted(set(pages))


def event_id_for(source_type, claim_id, seq):
    """Generate a deterministic event ID."""
    return f"ev-{source_type}-{claim_id}-{seq}"


def build_change_history():
    """Build change events from evidence ledger."""
    # Load evidence ledger
    if not os.path.exists(EVIDENCE_LEDGER_PATH):
        print(f"Error: {EVIDENCE_LEDGER_PATH} not found")
        sys.exit(1)
    ledger = load_json(EVIDENCE_LEDGER_PATH)

    # Load existing change ledger
    existing_events = []
    if os.path.exists(CHANGE_LEDGER_PATH):
        change_ledger = load_json(CHANGE_LEDGER_PATH)
        existing_events = change_ledger.get("events", [])

    # Track existing event IDs to avoid duplicates
    existing_ids = {e["event_id"] for e in existing_events}
    new_events = []
    seq = 1

    # 1. Process disputes → verification_correction events
    for dispute in ledger.get("disputes", []):
        claim_id = dispute.get("claim_id", "")
        dispute_id = dispute.get("dispute_id", "")
        event_id = f"ev-dispute-{claim_id}"
        if event_id in existing_ids:
            continue

        # Find the claim
        claim = None
        for c in ledger.get("claims", []):
            if c.get("claim_id") == claim_id:
                claim = c
                break

        tool_id = claim.get("tool_id", "unknown") if claim else "unknown"
        affected = find_tool_pages(tool_id) if tool_id != "unknown" else []

        event = {
            "event_id": event_id,
            "tool_id": tool_id,
            "event_type": "verification_correction",
            "detected_at": dispute.get("raised_at") or REFERENCE_DATE,
            "effective_at": None,
            "before": {"claim_status": "verified", "claim_id": claim_id},
            "after": {"claim_status": "disputed", "dispute_id": dispute_id},
            "source_ids": [dispute_id],
            "confidence": "medium",
            "status": "disputed",
            "correction_note": dispute.get("reason"),
            "affected_pages": affected,
            "note": f"Claim {claim_id} disputed: {dispute.get('reason', 'no reason given')}"
        }
        new_events.append(event)
        existing_ids.add(event_id)
        seq += 1

    # 2. Process replacements → evidence_update events
    for replacement in ledger.get("replacements", []):
        claim_id = replacement.get("old_claim_id", "")
        new_claim_id = replacement.get("new_claim_id", "")
        event_id = f"ev-replace-{claim_id}"
        if event_id in existing_ids:
            continue

        # Find the old claim for tool_id
        claim = None
        for c in ledger.get("claims", []):
            if c.get("claim_id") == claim_id:
                claim = c
                break

        tool_id = claim.get("tool_id", "unknown") if claim else "unknown"
        affected = find_tool_pages(tool_id) if tool_id != "unknown" else []

        event = {
            "event_id": event_id,
            "tool_id": tool_id,
            "event_type": "evidence_update",
            "detected_at": replacement.get("replaced_at") or REFERENCE_DATE,
            "effective_at": replacement.get("replaced_at"),
            "before": {"claim_id": claim_id},
            "after": {"claim_id": new_claim_id},
            "source_ids": [],
            "confidence": "high",
            "status": "verified",
            "correction_note": replacement.get("reason"),
            "affected_pages": affected,
            "note": f"Claim {claim_id} replaced by {new_claim_id}: {replacement.get('reason', '')}"
        }
        new_events.append(event)
        existing_ids.add(event_id)
        seq += 1

    # 3. Process stale claims → detected events (flagging for review)
    for claim in ledger.get("claims", []):
        if claim.get("status") == "stale":
            claim_id = claim.get("claim_id", "")
            event_id = f"ev-stale-{claim_id}"
            if event_id in existing_ids:
                continue

            tool_id = claim.get("tool_id", "unknown")
            affected = find_tool_pages(tool_id) if tool_id != "unknown" else []

            event = {
                "event_id": event_id,
                "tool_id": tool_id,
                "event_type": "evidence_update",
                "detected_at": REFERENCE_DATE,
                "effective_at": None,
                "before": {"claim_id": claim_id, "claim_status": "verified"},
                "after": {"claim_id": claim_id, "claim_status": "stale"},
                "source_ids": claim.get("source_ids", []),
                "confidence": "low",
                "status": "detected",
                "correction_note": f"Claim {claim_id} is stale after {claim.get('stale_after', 'unknown date')}",
                "affected_pages": affected,
                "note": f"Stale claim flagged for re-verification"
            }
            new_events.append(event)
            existing_ids.add(event_id)
            seq += 1

    # 4. Process disputed claims (status=disputed) → verification_correction
    for claim in ledger.get("claims", []):
        if claim.get("status") == "disputed" and claim.get("disputed_by"):
            claim_id = claim.get("claim_id", "")
            # Skip if already handled via disputes array
            dispute_ids = {d.get("claim_id") for d in ledger.get("disputes", [])}
            if claim_id in dispute_ids:
                continue

            event_id = f"ev-disputed-{claim_id}"
            if event_id in existing_ids:
                continue

            tool_id = claim.get("tool_id", "unknown")
            affected = find_tool_pages(tool_id) if tool_id != "unknown" else []

            event = {
                "event_id": event_id,
                "tool_id": tool_id,
                "event_type": "verification_correction",
                "detected_at": REFERENCE_DATE,
                "effective_at": None,
                "before": {"claim_id": claim_id, "claim_status": "verified"},
                "after": {"claim_id": claim_id, "claim_status": "disputed", "disputed_by": claim.get("disputed_by")},
                "source_ids": claim.get("source_ids", []),
                "confidence": "medium",
                "status": "disputed",
                "correction_note": claim.get("evidence_note"),
                "affected_pages": affected,
                "note": f"Claim {claim_id} marked disputed by {claim.get('disputed_by')}"
            }
            new_events.append(event)
            existing_ids.add(event_id)
            seq += 1

    # Merge and save
    all_events = existing_events + new_events
    change_ledger = {
        "schema_version": "tool-change-ledger-v1",
        "events": all_events
    }
    save_json(CHANGE_LEDGER_PATH, change_ledger)

    return len(new_events), len(all_events)


def main():
    print("=== Building Change History ===\n")

    new_count, total_count = build_change_history()

    print(f"New events added: {new_count}")
    print(f"Total events: {total_count}")
    print(f"Output: {CHANGE_LEDGER_PATH}")
    print()

    # Print summary of new events
    if new_count > 0:
        ledger = load_json(CHANGE_LEDGER_PATH)
        # Show last N events
        show = min(new_count, 10)
        events = ledger["events"][-show:]
        print(f"=== Last {show} Events ===")
        for ev in events:
            print(f"  {ev['event_id']}: {ev['tool_id']} / {ev['event_type']} / {ev['status']}")
            if ev.get("correction_note"):
                print(f"    Note: {ev['correction_note'][:100]}")

    print(f"\n=== Change history written to {CHANGE_LEDGER_PATH} ===")


if __name__ == "__main__":
    main()
