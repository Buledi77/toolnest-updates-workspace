#!/usr/bin/env python3
"""
Build Stale Commercial Facts Report.

Reads:
- data/evidence/evidence-ledger.json (claims with stale_after dates)
- docs/internal/COMMERCIAL-DATA.json (normalized commercial data)
- docs/internal/FRESHNESS-RADAR.json (freshness status per page)

Produces:
- docs/internal/STALE-COMMERCIAL-FACTS.json

Deterministic report of commercial claims that are stale or approaching stale.
No fabricated facts — only what the evidence ledger shows.
"""

import json
import os
import sys
from datetime import datetime

REFERENCE_DATE = datetime(2026, 11, 20)
EVIDENCE_LEDGER_PATH = "data/evidence/evidence-ledger.json"
COMMERCIAL_DATA_PATH = "docs/internal/COMMERCIAL-DATA.json"
FRESHNESS_RADAR_PATH = "docs/internal/FRESHNESS-RADAR.json"
OUTPUT_PATH = "docs/internal/STALE-COMMERCIAL-FACTS.json"


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return None


def days_until(date_str):
    """Days until a stale_after date from reference date."""
    dt = parse_date(date_str)
    if dt is None:
        return None
    return (dt - REFERENCE_DATE).days


def build_stale_report():
    """Build the stale commercial facts report."""
    ledger = load_json(EVIDENCE_LEDGER_PATH)
    commercial_data = load_json(COMMERCIAL_DATA_PATH)
    freshness_radar = load_json(FRESHNESS_RADAR_PATH)

    if ledger is None:
        print(f"Error: {EVIDENCE_LEDGER_PATH} not found")
        sys.exit(1)

    stale_claims = []
    approaching_stale_claims = []
    missing_commercial_evidence = []

    # 1. Check evidence ledger claims for staleness
    for claim in ledger.get("claims", []):
        # Only commercial-related claims
        if claim.get("claim_type") not in ("pricing", "billing", "plan_limit", "free_plan", "trial"):
            continue

        tool_id = claim.get("tool_id", "unknown")
        claim_id = claim.get("claim_id", "")
        stale_after = claim.get("stale_after")
        verified_at = claim.get("verified_at")
        status = claim.get("status", "")

        days = days_until(stale_after)

        claim_record = {
            "claim_id": claim_id,
            "tool_id": tool_id,
            "claim_type": claim.get("claim_type"),
            "field_path": claim.get("field_path"),
            "verified_at": verified_at,
            "stale_after": stale_after,
            "days_until_stale": days,
            "status": status,
            "source_ids": claim.get("source_ids", []),
            "evidence_note": claim.get("evidence_note")
        }

        if status == "disputed":
            claim_record["dispute_reason"] = claim.get("disputed_by")
            stale_claims.append(claim_record)
        elif days is not None and days <= 0:
            stale_claims.append(claim_record)
        elif days is not None and days <= 10:
            approaching_stale_claims.append(claim_record)

    # 2. Check commercial data for tools with no verified data
    if commercial_data:
        for tool in commercial_data.get("tools", []):
            if tool.get("status") == "unknown" and tool.get("confidence") == "none":
                missing_commercial_evidence.append({
                    "tool_id": tool.get("tool_id"),
                    "pricing_model": tool.get("pricing_model"),
                    "free_plan_status": tool.get("free_plan_status"),
                    "trial_status": tool.get("trial_status"),
                    "confidence": tool.get("confidence"),
                    "status": tool.get("status")
                })

    # 3. Check freshness radar for pages with stale commercial facts
    radar_stale_pages = []
    if freshness_radar:
        for page in freshness_radar.get("pages", []):
            commercial = page.get("commercial_facts_checked", {})
            if commercial.get("status") in ("stale", "approaching_stale", "disputed"):
                radar_stale_pages.append({
                    "path": page.get("path"),
                    "type": page.get("type"),
                    "commercial_status": commercial.get("status"),
                    "last_checked": commercial.get("last_checked"),
                    "days_since_check": commercial.get("days_since_check"),
                    "stale_after": commercial.get("stale_after"),
                    "claim_count": commercial.get("claim_count", 0)
                })

    # Build report
    report = {
        "schema_version": "stale-commercial-facts-v1",
        "generated_at": "2026-11-20",
        "reference_date": "2026-11-20",
        "description": "Deterministic report of stale, approaching-stale, and missing commercial facts. No fabricated data.",
        "summary": {
            "stale_or_disputed_claims": len(stale_claims),
            "approaching_stale_claims": len(approaching_stale_claims),
            "tools_missing_commercial_evidence": len(missing_commercial_evidence),
            "pages_with_stale_commercial_facts": len(radar_stale_pages)
        },
        "stale_or_disputed_claims": stale_claims,
        "approaching_stale_claims": approaching_stale_claims,
        "tools_missing_commercial_evidence": sorted(missing_commercial_evidence, key=lambda x: x["tool_id"]),
        "pages_with_stale_commercial_facts": radar_stale_pages
    }

    save_json(OUTPUT_PATH, report)
    return report


def main():
    print("=== Building Stale Commercial Facts Report ===\n")

    report = build_stale_report()

    summary = report["summary"]
    print(f"Stale or disputed claims: {summary['stale_or_disputed_claims']}")
    print(f"Approaching stale claims: {summary['approaching_stale_claims']}")
    print(f"Tools missing commercial evidence: {summary['tools_missing_commercial_evidence']}")
    print(f"Pages with stale commercial facts: {summary['pages_with_stale_commercial_facts']}")
    print()

    # Show stale claims
    if report["stale_or_disputed_claims"]:
        print("=== Stale or Disputed Claims ===")
        for claim in report["stale_or_disputed_claims"]:
            status_note = ""
            if claim.get("dispute_reason"):
                status_note = f" (disputed: {claim['dispute_reason']})"
            elif claim.get("days_until_stale") is not None:
                status_note = f" (stale after {claim['stale_after']}, {claim['days_until_stale']} days)"
            print(f"  {claim['claim_id']}: {claim['tool_id']} / {claim['claim_type']}{status_note}")

    # Show approaching stale
    if report["approaching_stale_claims"]:
        print("\n=== Approaching Stale Claims ===")
        for claim in report["approaching_stale_claims"]:
            print(f"  {claim['claim_id']}: {claim['tool_id']} / {claim['claim_type']} "
                  f"(stale after {claim['stale_after']}, {claim['days_until_stale']} days)")

    # Show missing evidence tools
    if report["tools_missing_commercial_evidence"]:
        print(f"\n=== Tools Missing Commercial Evidence ({len(report['tools_missing_commercial_evidence'])}) ===")
        for tool in report["tools_missing_commercial_evidence"][:10]:
            print(f"  {tool['tool_id']}: pricing={tool['pricing_model']}, "
                  f"free={tool['free_plan_status']}, trial={tool['trial_status']}")
        if len(report["tools_missing_commercial_evidence"]) > 10:
            print(f"  ... and {len(report['tools_missing_commercial_evidence']) - 10} more")

    print(f"\n=== Report written to {OUTPUT_PATH} ===")


if __name__ == "__main__":
    main()
