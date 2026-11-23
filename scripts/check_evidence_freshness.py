#!/usr/bin/env python3
"""Evidence freshness engine (Phase 3 Requirement C).

Identifies commercial/pricing facts with verification dates, flags stale facts
according to configurable policy, and classifies each fact as:
- VERIFIED_CURRENTLY: verified and within freshness threshold
- NEEDS_RECHECK: verified but past freshness threshold
- UNKNOWN: no verification date
- NOT_COLLECTED: no evidence at all

Outputs reports/phase3/evidence-freshness-report.json sorted by urgency.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL_DIR = ROOT / "data" / "tools-v2"
LEDGER_PATH = ROOT / "data" / "evidence" / "evidence-ledger.json"
FRESHNESS_POLICY_PATH = ROOT / "data" / "freshness-policy.json"
REPORTS_DIR = ROOT / "reports" / "phase3"


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_tools_v2_records():
    records = []
    for path in sorted(TOOL_DIR.rglob("*.json")):
        if path.name == "README.json":
            continue
        records.append(load_json(path))
    return records


def load_freshness_policy():
    if not FRESHNESS_POLICY_PATH.is_file():
        return {
            "thresholds": {"pricing": 90, "plan_limit": 90, "billing": 90,
                           "capabilities": 180, "free_trial": 90, "general": 365},
            "default_threshold": 365,
        }
    return load_json(FRESHNESS_POLICY_PATH)


def get_threshold_for_claim(claim_type, policy):
    """Get the freshness threshold (in days) for a claim type."""
    thresholds = policy.get("thresholds", {})
    return thresholds.get(claim_type, policy.get("default_threshold", 365))


def classify_claim(claim, policy, as_of):
    """Classify a claim based on its verification date and freshness threshold.

    Returns: (status, urgency_score)
    - VERIFIED_CURRENTLY: verified and within threshold
    - NEEDS_RECHECK: verified but past threshold
    - UNKNOWN: no verification date
    - NOT_COLLECTED: no evidence
    """
    claim_type = claim.get("claim_type", "general")
    threshold_days = get_threshold_for_claim(claim_type, policy)

    stale_after = claim.get("stale_after")
    verified_at = claim.get("verified_at")

    if not stale_after and not verified_at:
        return "UNKNOWN", 0

    if stale_after:
        try:
            stale_date = date.fromisoformat(stale_after)
            if stale_date < as_of:
                # Past stale_after date — needs recheck
                days_overdue = (as_of - stale_date).days
                return "NEEDS_RECHECK", days_overdue
            else:
                # Still within freshness window
                days_until_stale = (stale_date - as_of).days
                return "VERIFIED_CURRENTLY", -days_until_stale
        except (ValueError, TypeError):
            return "UNKNOWN", 0

    if verified_at:
        try:
            verified_date = date.fromisoformat(verified_at)
            threshold_date = verified_date + timedelta(days=threshold_days)
            if threshold_date < as_of:
                days_overdue = (as_of - threshold_date).days
                return "NEEDS_RECHECK", days_overdue
            else:
                days_until_stale = (threshold_date - as_of).days
                return "VERIFIED_CURRENTLY", -days_until_stale
        except (ValueError, TypeError):
            return "UNKNOWN", 0

    return "UNKNOWN", 0


def check_evidence_freshness(as_of=None):
    """Run freshness checks on all evidence claims and tools-v2 records."""
    as_of = as_of or date.today()
    if isinstance(as_of, str):
        as_of = date.fromisoformat(as_of)

    policy = load_freshness_policy()
    records = load_tools_v2_records()

    # Load evidence ledger
    ledger = {}
    if LEDGER_PATH.is_file():
        ledger = load_json(LEDGER_PATH)

    claims = ledger.get("claims", [])
    sources = {s.get("source_id"): s for s in ledger.get("sources", [])}

    # Build tool lookup
    v2_by_id = {r.get("identity", {}).get("id"): r for r in records}

    results = {
        "check": "evidence_freshness",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "as_of": as_of.isoformat(),
        "policy": policy,
        "claims": [],
        "tools": [],
        "summary": {},
    }

    # Classify each claim
    status_counts = {"VERIFIED_CURRENTLY": 0, "NEEDS_RECHECK": 0, "UNKNOWN": 0, "NOT_COLLECTED": 0}

    for claim in claims:
        claim_id = claim.get("claim_id", "<missing>")
        tool_id = claim.get("tool_id", "<missing>")
        claim_type = claim.get("claim_type", "general")

        status, urgency = classify_claim(claim, policy, as_of)
        status_counts[status] = status_counts.get(status, 0) + 1

        claim_entry = {
            "claim_id": claim_id,
            "tool_id": tool_id,
            "claim_type": claim_type,
            "status": status,
            "urgency_score": urgency,
            "stale_after": claim.get("stale_after"),
            "verified_at": claim.get("verified_at"),
            "source_ids": claim.get("source_ids", []),
        }

        # Add source details
        for sid in claim.get("source_ids", []):
            source = sources.get(sid)
            if source:
                claim_entry[f"source_{sid}"] = {
                    "url": source.get("url"),
                    "type": source.get("source_type"),
                }

        results["claims"].append(claim_entry)

    # Check tools-v2 freshness fields
    for record in records:
        tool_id = record.get("identity", {}).get("id", "<missing>")
        freshness = record.get("freshness", {})

        tool_entry = {
            "tool_id": tool_id,
            "last_verified_at": freshness.get("last_verified_at"),
            "next_review_at": freshness.get("next_review_at"),
            "stale_fields": freshness.get("stale_fields", []),
            "evidence_claim_refs": record.get("evidence", {}).get("claim_refs", []),
            "evidence_confidence": record.get("evidence", {}).get("confidence"),
        }

        # Check if next_review_at has passed
        next_review = freshness.get("next_review_at")
        if next_review:
            try:
                nr_date = datetime.fromisoformat(next_review.replace("Z", "+00:00")).date()
                if nr_date < as_of:
                    tool_entry["review_status"] = "OVERDUE"
                    tool_entry["days_overdue"] = (as_of - nr_date).days
                else:
                    tool_entry["review_status"] = "ON_TRACK"
                    tool_entry["days_until_review"] = (nr_date - as_of).days
            except (ValueError, TypeError):
                tool_entry["review_status"] = "INVALID_DATE"
        else:
            tool_entry["review_status"] = "NOT_SET"

        # Check if tool has any claims
        tool_claims = [c for c in claims if c.get("tool_id") == tool_id]
        if not tool_claims:
            tool_entry["has_claims"] = False
            status_counts["NOT_COLLECTED"] = status_counts.get("NOT_COLLECTED", 0)
        else:
            tool_entry["has_claims"] = True
            tool_entry["claim_count"] = len(tool_claims)

        results["tools"].append(tool_entry)

    # Sort claims by urgency (most urgent first)
    results["claims"].sort(key=lambda c: -c["urgency_score"])

    # Summary
    results["summary"] = {
        "total_claims": len(claims),
        "total_tools_checked": len(records),
        "status_counts": status_counts,
        "stale_claims": sum(1 for c in results["claims"] if c["status"] == "NEEDS_RECHECK"),
        "unknown_claims": sum(1 for c in results["claims"] if c["status"] == "UNKNOWN"),
        "tools_overdue_for_review": sum(1 for t in results["tools"] if t["review_status"] == "OVERDUE"),
        "tools_without_claims": sum(1 for t in results["tools"] if not t["has_claims"]),
    }

    return results


def main():
    results = check_evidence_freshness()

    # Ensure output directory exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / "evidence-freshness-report.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Print summary
    summary = results["summary"]
    print(f"\nEvidence Freshness Report")
    print(f"  As of: {results['as_of']}")
    print(f"  Total claims: {summary['total_claims']}")
    print(f"  Total tools checked: {summary['total_tools_checked']}")
    print(f"\n  Claim status breakdown:")
    for status, count in summary["status_counts"].items():
        print(f"    {status}: {count}")
    print(f"\n  Stale claims: {summary['stale_claims']}")
    print(f"  Unknown claims: {summary['unknown_claims']}")
    print(f"  Tools overdue for review: {summary['tools_overdue_for_review']}")
    print(f"  Tools without claims: {summary['tools_without_claims']}")

    # Show top 5 most urgent stale claims
    stale = [c for c in results["claims"] if c["status"] == "NEEDS_RECHECK"]
    if stale:
        print(f"\n  Top {min(5, len(stale))} most urgent stale claims:")
        for claim in stale[:5]:
            print(f"    - {claim['claim_id']} ({claim['tool_id']}): "
                  f"stale_after={claim['stale_after']}, urgency={claim['urgency_score']}")

    print(f"\nReport written to {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
