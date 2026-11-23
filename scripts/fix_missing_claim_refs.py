#!/usr/bin/env python3
"""Batch fix: add missing claim references to all tools-v2 records.

For each record, find all claims in the evidence ledger whose tool_id matches
the record's id, and ensure each claim_id appears in evidence.claim_refs.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL_DIR = ROOT / "data" / "tools-v2"
LEDGER_PATH = ROOT / "data" / "evidence" / "evidence-ledger.json"


def main():
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    claims = ledger.get("claims", [])

    # Group claims by tool_id
    claims_by_tool = {}
    for claim in claims:
        tool_id = claim.get("tool_id", "")
        if tool_id:
            claims_by_tool.setdefault(tool_id, []).append(claim["claim_id"])

    # Process all v2 records
    fixed_count = 0
    total_added = 0

    for record_path in sorted(TOOL_DIR.rglob("*.json")):
        if record_path.name == "README.json":
            continue

        record = json.loads(record_path.read_text(encoding="utf-8"))
        record_id = record.get("identity", {}).get("id", "")

        if record_id not in claims_by_tool:
            continue

        expected_claim_ids = set(claims_by_tool[record_id])

        # Current claim refs
        evidence = record.get("evidence", {})
        current_refs = evidence.get("claim_refs", [])
        current_ids = {ref.get("claim_id") for ref in current_refs if isinstance(ref, dict)}

        missing = expected_claim_ids - current_ids
        if not missing:
            continue

        # Add missing claims
        for claim_id in sorted(missing):
            current_refs.append({"claim_id": claim_id})

        evidence["claim_refs"] = current_refs
        record["evidence"] = evidence

        # Write back
        record_path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        fixed_count += 1
        total_added += len(missing)
        print(f"  {record_id}: added {len(missing)} missing claim refs")

    print(f"\nTotal: fixed {fixed_count} records, added {total_added} claim refs")


if __name__ == "__main__":
    main()
