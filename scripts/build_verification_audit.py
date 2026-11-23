"""Build a field-level verification audit report for all tools.

Scans every tools-v2 record and the evidence ledger to produce a summary
of verification status per tool, per claim, and overall coverage metrics.

Output: reports/phase2/verification-audit.json
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from decision_graph_common import (
    VALID_CLAIM_STATUSES,
    VALID_VERIFICATION_STATUSES,
    load_json,
    load_records,
    LEDGER_PATH,
    ROOT,
)

REPORTS_DIR = ROOT / "reports" / "phase2"


def build_audit():
    records = load_records()
    ledger = load_json(LEDGER_PATH)

    claims_by_tool = {}
    for claim in ledger.get("claims", []):
        tool_id = claim.get("tool_id", "")
        claims_by_tool.setdefault(tool_id, []).append(claim)

    sources_by_id = {s["source_id"]: s for s in ledger.get("sources", [])}

    tools = []
    summary = {
        "total_tools": len(records),
        "tools_with_any_verified_claims": 0,
        "tools_with_verified_official_claims": 0,
        "tools_with_pricing_claims": 0,
        "tools_with_verified_pricing": 0,
        "total_claims": len(ledger.get("claims", [])),
        "claims_by_status": {},
        "claims_by_verification_status": {},
        "claims_by_type": {},
    }

    for record in records:
        identity = record.get("identity", {})
        record_id = identity.get("id")
        record_name = identity.get("name", "")
        evidence = record.get("evidence", {})
        factual = record.get("factual_profile", {})

        tool_claims = claims_by_tool.get(record_id, [])
        tool_entry = {
            "tool_id": record_id,
            "name": record_name,
            "evidence_verification_status": evidence.get("verification_status"),
            "total_claims": len(tool_claims),
            "verified_claims": 0,
            "verified_official_claims": 0,
            "research_required_claims": 0,
            "stale_claims": 0,
            "disputed_claims": 0,
            "pricing_claims": [],
            "capability_claims": [],
            "limitation_claims": [],
            "claims_with_official_sources": 0,
            "factual_profile_populated": bool(
                factual.get("concise_summary") or factual.get("primary_purpose")
            ),
            "has_capabilities": bool(factual.get("capabilities")),
            "has_limitations": bool(factual.get("limitations")),
            "has_pricing_status": bool(factual.get("pricing_status")),
            "has_free_plan_status": bool(factual.get("free_plan_status")),
            "has_trial_status": bool(factual.get("trial_status")),
        }

        for claim in tool_claims:
            status = claim.get("status", "")
            v_status = claim.get("verification_status")
            claim_type = claim.get("claim_type", "")

            # Count by status
            summary["claims_by_status"][status] = summary["claims_by_status"].get(status, 0) + 1
            if v_status:
                summary["claims_by_verification_status"][v_status] = summary["claims_by_verification_status"].get(v_status, 0) + 1
            summary["claims_by_type"][claim_type] = summary["claims_by_type"].get(claim_type, 0) + 1

            # Per-tool counts
            if status in ("verified", "verified_official", "verified_official_dynamic"):
                tool_entry["verified_claims"] += 1
            if status == "verified_official":
                tool_entry["verified_official_claims"] += 1
            if status == "research_required":
                tool_entry["research_required_claims"] += 1
            if status == "stale":
                tool_entry["stale_claims"] += 1
            if status == "disputed":
                tool_entry["disputed_claims"] += 1

            # Check if claim has official sources
            has_official = False
            for sid in claim.get("source_ids", []):
                src = sources_by_id.get(sid, {})
                if src.get("official") is True:
                    has_official = True
                    break
            if has_official:
                tool_entry["claims_with_official_sources"] += 1

            # Categorize claims
            claim_info = {
                "claim_id": claim.get("claim_id"),
                "status": status,
                "verification_status": v_status,
                "field_path": claim.get("field_path"),
                "claim_type": claim_type,
                "has_official_source": has_official,
            }

            if claim_type == "pricing":
                tool_entry["pricing_claims"].append(claim_info)
            elif claim_type == "capability":
                tool_entry["capability_claims"].append(claim_info)
            elif claim_type == "limitation":
                tool_entry["limitation_claims"].append(claim_info)

        # Summary counters
        if tool_entry["verified_claims"] > 0:
            summary["tools_with_any_verified_claims"] += 1
        if tool_entry["verified_official_claims"] > 0:
            summary["tools_with_verified_official_claims"] += 1
        if tool_entry["pricing_claims"]:
            summary["tools_with_pricing_claims"] += 1
            # Check if any pricing claim is verified
            for pc in tool_entry["pricing_claims"]:
                if pc["status"] in ("verified", "verified_official", "verified_official_dynamic"):
                    summary["tools_with_verified_pricing"] += 1
                    break

        tools.append(tool_entry)

    report = {
        "generated_at": date.today().isoformat(),
        "schema_version": "verification-audit-v1",
        "summary": summary,
        "tools": tools,
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / "verification-audit.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Verification audit written to {output_path}")
    print(f"Total tools: {summary['total_tools']}")
    print(f"Tools with any verified claims: {summary['tools_with_any_verified_claims']}")
    print(f"Tools with verified_official claims: {summary['tools_with_verified_official_claims']}")
    print(f"Tools with pricing claims: {summary['tools_with_pricing_claims']}")
    print(f"Tools with verified pricing: {summary['tools_with_verified_pricing']}")
    print(f"Total claims: {summary['total_claims']}")
    print(f"Claims by status: {json.dumps(summary['claims_by_status'], indent=2)}")
    if summary["claims_by_verification_status"]:
        print(f"Claims by verification_status: {json.dumps(summary['claims_by_verification_status'], indent=2)}")
    print(f"Claims by type: {json.dumps(summary['claims_by_type'], indent=2)}")

    return report


if __name__ == "__main__":
    build_audit()
