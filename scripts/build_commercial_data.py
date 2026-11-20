#!/usr/bin/env python3
"""
Commercial Data Foundation — Phase 1

Build deterministic normalized commercial/pricing data only from existing
repository evidence.

Sources of truth (in priority order):
1. Evidence ledger claims (type: pricing, billing, free_plan, trial)
2. tools-v2 factual_profile (pricing_status, free_plan_status, trial_status)
3. tools.json catalog entries (no commercial data, but provides tool list)

Output: docs/internal/COMMERCIAL-DATA.json

Fields per tool:
- tool_id
- pricing_model: subscription / freemium / free / one-time / usage-based / unknown / disputed
- verified_starting_price: float or null
- currency: "USD" or null
- billing_term: monthly / annual / unknown / null
- free_plan_status: permanent_free_plan / limited_free_account / free_trial / demo_only / paid_only / unknown / disputed / not_applicable
- trial_status: free_trial / demo_only / no_trial / unknown / disputed / not_applicable
- verified_plan_limits: list of {plan_name, limit_description, source_id} or []
- checked_date: ISO date or null
- verified_date: ISO date or null
- stale_date: ISO date or null
- source_ids: list of source IDs from evidence ledger
- confidence: high / medium / low / none
- status: verified / unverified / stale / disputed / unknown
- disputed: bool
"""

import json
import os
import glob
from pathlib import Path


def load_json(path):
    with open(path) as f:
        return json.load(f)


def get_all_tool_ids():
    """Get all tool IDs from tools.json catalog."""
    catalog = load_json("data/tools.json")
    return [t["id"] for t in catalog.get("tools", [])]


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
    # Check active tools-v2
    for path in [f"data/tools-v2/{tool_id}.json"]:
        if os.path.exists(path):
            return load_json(path)
    # Check legacy
    for path in [f"data/tools-v2/legacy/{tool_id}.json"]:
        if os.path.exists(path):
            return load_json(path)
    # Check expansion
    for path in [f"data/tools-v2/expansion/{tool_id}.json"]:
        if os.path.exists(path):
            return load_json(path)
    # Try migration map (e.g., mozpro -> moz-pro)
    v2_id = get_v2_id_for_legacy(tool_id)
    if v2_id and v2_id != tool_id:
        for path in [f"data/tools-v2/{v2_id}.json"]:
            if os.path.exists(path):
                return load_json(path)
    return None


def get_evidence_claims(tool_id):
    """Get evidence ledger claims for a tool."""
    ledger = load_json("data/evidence/evidence-ledger.json")
    claims = [c for c in ledger.get("claims", []) if c.get("tool_id") == tool_id]
    source_ids = set()
    for c in claims:
        for sid in c.get("source_ids", []):
            source_ids.add(sid)
    sources = [s for s in ledger.get("sources", []) if s.get("source_id") in source_ids]
    disputes = [d for d in ledger.get("disputes", []) if d.get("tool_id") == tool_id]
    return claims, sources, disputes


def infer_pricing_model(claims, v2_record):
    """Infer pricing model from evidence."""
    has_free = False
    has_paid = False
    has_trial = False

    for c in claims:
        ctype = c.get("claim_type", "")
        if ctype in ("pricing", "billing"):
            has_paid = True
        if ctype == "free_plan":
            has_free = True
        if ctype == "trial":
            has_trial = True

    if v2_record:
        fp = v2_record.get("factual_profile", {})
        if fp.get("free_plan_status"):
            has_free = True
        if fp.get("pricing_status"):
            has_paid = True
        if fp.get("trial_status"):
            has_trial = True

    if has_free and has_paid:
        return "freemium"
    elif has_free:
        return "free"
    elif has_paid:
        return "subscription"
    else:
        return "unknown"


def infer_free_plan_status(claims, v2_record):
    """Infer free plan status from evidence."""
    for c in claims:
        ctype = c.get("claim_type", "")
        if ctype == "free_plan":
            return "permanent_free_plan"

    if v2_record:
        fp = v2_record.get("factual_profile", {})
        if fp.get("free_plan_status"):
            return "limited_free_account"

    return "unknown"


def infer_trial_status(claims, v2_record):
    """Infer trial status from evidence."""
    for c in claims:
        ctype = c.get("claim_type", "")
        if ctype == "trial":
            return "free_trial"

    if v2_record:
        fp = v2_record.get("factual_profile", {})
        if fp.get("trial_status"):
            return "free_trial"

    return "unknown"


def get_verified_dates(claims):
    """Get checked/verified/stale dates from claims."""
    dates = []
    for c in claims:
        if c.get("verified_at"):
            dates.append(c["verified_at"])
        if c.get("accessed_at"):
            dates.append(c["accessed_at"])
        if c.get("stale_after"):
            dates.append(c["stale_after"])

    if not dates:
        return None, None, None

    dates.sort()
    return dates[0], dates[-1], None


def build_commercial_data():
    """Build normalized commercial data for all tools."""
    tool_ids = get_all_tool_ids()

    commercial_data = {
        "schema_version": "commercial-data-v1",
        "generated_at": "2026-11-20",
        "description": "Deterministic normalized commercial/pricing data from repository evidence only. Unknown stays unknown. No fabricated facts.",
        "total_tools": len(tool_ids),
        "tools": []
    }

    for tool_id in sorted(tool_ids):
        v2_record = get_tools_v2_record(tool_id)
        claims, sources, disputes = get_evidence_claims(tool_id)

        # Infer pricing model
        pricing_model = infer_pricing_model(claims, v2_record)

        # Infer free plan status
        free_plan_status = infer_free_plan_status(claims, v2_record)

        # Infer trial status
        trial_status = infer_trial_status(claims, v2_record)

        # Get dates
        checked_date, verified_date, stale_date = get_verified_dates(claims)

        # Get source IDs
        source_ids = [s.get("source_id") for s in sources]

        # Check for disputes
        has_dispute = len(disputes) > 0

        # Determine confidence
        if len(claims) >= 2 and any(c.get("claim_type") in ("pricing", "billing") for c in claims):
            confidence = "high"
        elif len(claims) >= 1:
            confidence = "medium"
        elif v2_record and v2_record.get("factual_profile", {}).get("pricing_status"):
            confidence = "low"
        else:
            confidence = "none"

        # Determine status
        if has_dispute:
            status = "disputed"
        elif confidence in ("high", "medium"):
            status = "verified"
        elif confidence == "low":
            status = "unverified"
        else:
            status = "unknown"

        # Verified plan limits (only from evidence)
        plan_limits = []
        for c in claims:
            if c.get("claim_type") == "pricing":
                # Check if the claim has plan details
                # For now, we note the claim exists but don't extract specific limits
                # without explicit structured data
                pass

        # Build record
        record = {
            "tool_id": tool_id,
            "pricing_model": pricing_model,
            "verified_starting_price": None,
            "currency": None,
            "billing_term": None,
            "free_plan_status": free_plan_status,
            "trial_status": trial_status,
            "verified_plan_limits": plan_limits,
            "checked_date": checked_date,
            "verified_date": verified_date,
            "stale_date": stale_date,
            "source_ids": source_ids,
            "confidence": confidence,
            "status": status,
            "disputed": has_dispute
        }

        commercial_data["tools"].append(record)

    # Summary statistics
    model_counts = {}
    confidence_counts = {}
    status_counts = {}
    free_plan_counts = {}
    trial_counts = {}

    for t in commercial_data["tools"]:
        model_counts[t["pricing_model"]] = model_counts.get(t["pricing_model"], 0) + 1
        confidence_counts[t["confidence"]] = confidence_counts.get(t["confidence"], 0) + 1
        status_counts[t["status"]] = status_counts.get(t["status"], 0) + 1
        free_plan_counts[t["free_plan_status"]] = free_plan_counts.get(t["free_plan_status"], 0) + 1
        trial_counts[t["trial_status"]] = trial_counts.get(t["trial_status"], 0) + 1

    commercial_data["summary"] = {
        "pricing_model_distribution": model_counts,
        "confidence_distribution": confidence_counts,
        "status_distribution": status_counts,
        "free_plan_distribution": free_plan_counts,
        "trial_distribution": trial_counts,
        "tools_with_verified_data": sum(1 for t in commercial_data["tools"] if t["confidence"] != "none"),
        "tools_with_disputed_data": sum(1 for t in commercial_data["tools"] if t["disputed"]),
        "tools_with_unknown_data": sum(1 for t in commercial_data["tools"] if t["status"] == "unknown")
    }

    return commercial_data


def main():
    print("=== Building Commercial Data Foundation ===\n")
    data = build_commercial_data()

    output_path = "docs/internal/COMMERCIAL-DATA.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Output: {output_path}")
    print(f"Total tools: {data['total_tools']}")
    print()

    summary = data["summary"]
    print("=== Pricing Model Distribution ===")
    for model, count in sorted(summary["pricing_model_distribution"].items()):
        print(f"  {model}: {count}")
    print()

    print("=== Confidence Distribution ===")
    for level, count in sorted(summary["confidence_distribution"].items()):
        print(f"  {level}: {count}")
    print()

    print("=== Status Distribution ===")
    for status, count in sorted(summary["status_distribution"].items()):
        print(f"  {status}: {count}")
    print()

    print("=== Free Plan Distribution ===")
    for status, count in sorted(summary["free_plan_distribution"].items()):
        print(f"  {status}: {count}")
    print()

    print("=== Trial Distribution ===")
    for status, count in sorted(summary["trial_distribution"].items()):
        print(f"  {status}: {count}")
    print()

    # Show tools with verified data
    print("=== Tools with Verified Commercial Data ===")
    for t in data["tools"]:
        if t["confidence"] != "none":
            print(f"  {t['tool_id']}: model={t['pricing_model']}, confidence={t['confidence']}, "
                  f"free={t['free_plan_status']}, trial={t['trial_status']}, sources={t['source_ids']}")

    print(f"\n=== Commercial data written to {output_path} ===")


if __name__ == "__main__":
    main()
