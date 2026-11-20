#!/usr/bin/env python3
"""
Build Disputed Claims Report.

Reads:
- data/evidence/evidence-ledger.json (claims with status=disputed, disputes array)
- data/corrections/correction-registry.json (correction submissions)
- data/changes/tool-change-ledger.json (change events with status=disputed)

Produces:
- docs/internal/DISPUTED-CLAIMS.json

Deterministic report of all disputed claims, active disputes, and related corrections.
No fabricated data — only what the evidence ledger and correction registry show.
"""

import json
import os
import sys

REFERENCE_DATE = "2026-11-20"
EVIDENCE_LEDGER_PATH = "data/evidence/evidence-ledger.json"
CORRECTION_REGISTRY_PATH = "data/corrections/correction-registry.json"
CHANGE_LEDGER_PATH = "data/changes/tool-change-ledger.json"
OUTPUT_PATH = "docs/internal/DISPUTED-CLAIMS.json"


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def build_disputed_report():
    """Build the disputed claims report."""
    ledger = load_json(EVIDENCE_LEDGER_PATH)
    corrections = load_json(CORRECTION_REGISTRY_PATH)
    changes = load_json(CHANGE_LEDGER_PATH)

    if ledger is None:
        print(f"Error: {EVIDENCE_LEDGER_PATH} not found")
        sys.exit(1)

    disputed_claims = []
    active_disputes = []
    related_corrections = []
    related_change_events = []

    # 1. Find all disputed claims in evidence ledger
    for claim in ledger.get("claims", []):
        if claim.get("status") == "disputed":
            disputed_claims.append({
                "claim_id": claim.get("claim_id"),
                "tool_id": claim.get("tool_id"),
                "claim_type": claim.get("claim_type"),
                "field_path": claim.get("field_path"),
                "disputed_by": claim.get("disputed_by"),
                "verified_at": claim.get("verified_at"),
                "stale_after": claim.get("stale_after"),
                "source_ids": claim.get("source_ids", []),
                "evidence_note": claim.get("evidence_note"),
                "replacement_claim_id": claim.get("replacement_claim_id")
            })

    # 2. Find all active disputes
    for dispute in ledger.get("disputes", []):
        active_disputes.append({
            "dispute_id": dispute.get("dispute_id"),
            "claim_id": dispute.get("claim_id"),
            "raised_by": dispute.get("raised_by"),
            "raised_at": dispute.get("raised_at"),
            "reason": dispute.get("reason"),
            "status": dispute.get("status"),
            "resolution_claim_id": dispute.get("resolution_claim_id")
        })

    # 3. Find related corrections
    if corrections:
        for corr in corrections.get("corrections", []):
            if corr.get("status") in ("submitted", "investigating", "accepted", "partially_accepted"):
                related_corrections.append({
                    "correction_id": corr.get("correction_id"),
                    "tool_id": corr.get("tool_id"),
                    "status": corr.get("status"),
                    "claim_description": corr.get("claim_description"),
                    "submitted_at": corr.get("submitted_at"),
                    "related_claim_ids": corr.get("related_claim_ids", []),
                    "public_correction_note": corr.get("public_correction_note")
                })

    # 4. Find related change events
    if changes:
        for event in changes.get("events", []):
            if event.get("status") == "disputed":
                related_change_events.append({
                    "event_id": event.get("event_id"),
                    "tool_id": event.get("tool_id"),
                    "event_type": event.get("event_type"),
                    "detected_at": event.get("detected_at"),
                    "status": event.get("status"),
                    "correction_note": event.get("correction_note"),
                    "affected_pages": event.get("affected_pages", [])
                })

    # Build report
    report = {
        "schema_version": "disputed-claims-v1",
        "generated_at": "2026-11-20",
        "reference_date": "2026-11-20",
        "description": "Deterministic report of disputed claims, active disputes, and related corrections. No fabricated data.",
        "summary": {
            "disputed_claims": len(disputed_claims),
            "active_disputes": len(active_disputes),
            "related_corrections": len(related_corrections),
            "related_change_events": len(related_change_events),
            "tools_affected": len(set(c["tool_id"] for c in disputed_claims))
        },
        "disputed_claims": disputed_claims,
        "active_disputes": active_disputes,
        "related_corrections": related_corrections,
        "related_change_events": related_change_events
    }

    save_json(OUTPUT_PATH, report)
    return report


def main():
    print("=== Building Disputed Claims Report ===\n")

    report = build_disputed_report()

    summary = report["summary"]
    print(f"Disputed claims: {summary['disputed_claims']}")
    print(f"Active disputes: {summary['active_disputes']}")
    print(f"Related corrections: {summary['related_corrections']}")
    print(f"Related change events: {summary['related_change_events']}")
    print(f"Tools affected: {summary['tools_affected']}")
    print()

    # Show disputed claims
    if report["disputed_claims"]:
        print("=== Disputed Claims ===")
        for claim in report["disputed_claims"]:
            print(f"  {claim['claim_id']}: {claim['tool_id']} / {claim['claim_type']}")
            print(f"    Disputed by: {claim['disputed_by']}")
            if claim.get("evidence_note"):
                print(f"    Note: {claim['evidence_note'][:120]}")

    # Show active disputes
    if report["active_disputes"]:
        print("\n=== Active Disputes ===")
        for dispute in report["active_disputes"]:
            print(f"  {dispute['dispute_id']}: claim={dispute['claim_id']}, "
                  f"status={dispute['status']}, raised_by={dispute['raised_by']}")
            if dispute.get("reason"):
                print(f"    Reason: {dispute['reason'][:100]}")

    # Show related corrections
    if report["related_corrections"]:
        print(f"\n=== Related Corrections ({len(report['related_corrections'])}) ===")
        for corr in report["related_corrections"]:
            print(f"  {corr['correction_id']}: {corr['tool_id']} / {corr['status']}")

    print(f"\n=== Report written to {OUTPUT_PATH} ===")


if __name__ == "__main__":
    main()
