#!/usr/bin/env python3
"""
Free Plan / Trial Foundation — Phase 2

Create structured data for future Free Plan Finder, Trial Reality Checker
and Plan Limit Fit Checker.

Supported statuses:
- permanent_free_plan
- limited_free_account
- free_trial
- demo_only
- paid_only
- unknown
- disputed
- not_applicable

Only classify when evidence supports it.

Output: docs/internal/FREE-PLAN-TRIAL-FOUNDATION.json
"""

import json
import os


def load_json(path):
    with open(path) as f:
        return json.load(f)


def get_v2_id_for_legacy(tool_id):
    """Map legacy tool ID to v2 ID using the migration map."""
    try:
        mapping = load_json("data/migrations/legacy-to-v2-map.json")
        for record in mapping.get("records", []):
            if record.get("legacy_id") == tool_id:
                return record.get("v2_id")
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return None


def get_tools_v2_record(tool_id):
    """Load tools-v2 record from any subdirectory."""
    for path in [f"data/tools-v2/{tool_id}.json",
                 f"data/tools-v2/legacy/{tool_id}.json",
                 f"data/tools-v2/expansion/{tool_id}.json"]:
        if os.path.exists(path):
            return load_json(path)
    v2_id = get_v2_id_for_legacy(tool_id)
    if v2_id and v2_id != tool_id:
        path = f"data/tools-v2/{v2_id}.json"
        if os.path.exists(path):
            return load_json(path)
    return None


def get_evidence_claims(tool_id):
    """Get evidence ledger claims for a tool."""
    ledger = load_json("data/evidence/evidence-ledger.json")
    claims = [c for c in ledger.get("claims", []) if c.get("tool_id") == tool_id]
    disputes = [d for d in ledger.get("disputes", []) if d.get("tool_id") == tool_id]
    return claims, disputes


def classify_free_plan(tool_id, claims, disputes, v2_record):
    """Classify free plan status from evidence."""
    if disputes:
        return "disputed", ["dispute_found"]

    reasons = []
    for c in claims:
        ctype = c.get("claim_type", "")
        if ctype == "free_plan":
            return "permanent_free_plan", ["evidence_ledger_free_plan_claim"]

    if v2_record:
        fp = v2_record.get("factual_profile", {})
        if fp.get("free_plan_status"):
            return "limited_free_account", ["tools_v2_free_plan_status"]

    return "unknown", []


def classify_trial(tool_id, claims, disputes, v2_record):
    """Classify trial status from evidence."""
    if disputes:
        return "disputed", ["dispute_found"]

    reasons = []
    for c in claims:
        ctype = c.get("claim_type", "")
        if ctype == "trial":
            return "free_trial", ["evidence_ledger_trial_claim"]

    if v2_record:
        fp = v2_record.get("factual_profile", {})
        if fp.get("trial_status"):
            return "free_trial", ["tools_v2_trial_status"]

    return "unknown", []


def build_free_plan_trial_foundation():
    """Build free plan and trial foundation data."""
    catalog = load_json("data/tools.json")
    tool_ids = [t["id"] for t in catalog.get("tools", [])]

    foundation = {
        "schema_version": "free-plan-trial-foundation-v1",
        "generated_at": "2026-11-20",
        "description": "Structured free plan and trial classification for future Free Plan Finder, Trial Reality Checker, and Plan Limit Fit Checker. Only classified when evidence supports it.",
        "supported_statuses": [
            "permanent_free_plan", "limited_free_account", "free_trial",
            "demo_only", "paid_only", "unknown", "disputed", "not_applicable"
        ],
        "total_tools": len(tool_ids),
        "tools": []
    }

    for tool_id in sorted(tool_ids):
        v2_record = get_tools_v2_record(tool_id)
        claims, disputes = get_evidence_claims(tool_id)

        free_status, free_reasons = classify_free_plan(tool_id, claims, disputes, v2_record)
        trial_status, trial_reasons = classify_trial(tool_id, claims, disputes, v2_record)

        record = {
            "tool_id": tool_id,
            "free_plan_status": free_status,
            "free_plan_reasons": free_reasons,
            "trial_status": trial_status,
            "trial_reasons": trial_reasons,
            "evidence_claims_count": len(claims),
            "has_disputes": len(disputes) > 0
        }

        foundation["tools"].append(record)

    # Summary
    free_counts = {}
    trial_counts = {}
    for t in foundation["tools"]:
        free_counts[t["free_plan_status"]] = free_counts.get(t["free_plan_status"], 0) + 1
        trial_counts[t["trial_status"]] = trial_counts.get(t["trial_status"], 0) + 1

    foundation["summary"] = {
        "free_plan_distribution": free_counts,
        "trial_distribution": trial_counts,
        "tools_with_free_plan_evidence": sum(1 for t in foundation["tools"] if t["free_plan_status"] not in ("unknown", "disputed")),
        "tools_with_trial_evidence": sum(1 for t in foundation["tools"] if t["trial_status"] not in ("unknown", "disputed")),
        "tools_with_disputes": sum(1 for t in foundation["tools"] if t["has_disputes"])
    }

    return foundation


def main():
    print("=== Building Free Plan / Trial Foundation ===\n")
    data = build_free_plan_trial_foundation()

    output_path = "docs/internal/FREE-PLAN-TRIAL-FOUNDATION.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Output: {output_path}")
    print(f"Total tools: {data['total_tools']}")
    print()

    summary = data["summary"]
    print("=== Free Plan Distribution ===")
    for status, count in sorted(summary["free_plan_distribution"].items()):
        print(f"  {status}: {count}")
    print()

    print("=== Trial Distribution ===")
    for status, count in sorted(summary["trial_distribution"].items()):
        print(f"  {status}: {count}")
    print()

    print(f"Tools with free plan evidence: {summary['tools_with_free_plan_evidence']}")
    print(f"Tools with trial evidence: {summary['tools_with_trial_evidence']}")

    # Show tools with evidence
    print("\n=== Tools with Free Plan Evidence ===")
    for t in data["tools"]:
        if t["free_plan_status"] not in ("unknown", "disputed"):
            print(f"  {t['tool_id']}: {t['free_plan_status']} ({', '.join(t['free_plan_reasons'])})")

    print("\n=== Tools with Trial Evidence ===")
    for t in data["tools"]:
        if t["trial_status"] not in ("unknown", "disputed"):
            print(f"  {t['tool_id']}: {t['trial_status']} ({', '.join(t['trial_reasons'])})")

    print(f"\n=== Written to {output_path} ===")


if __name__ == "__main__":
    main()
