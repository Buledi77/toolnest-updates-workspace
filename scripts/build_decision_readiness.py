#!/usr/bin/env python3
"""
Decision-Readiness Framework for ToolNest (Strict Evidence Mode).

Evaluates each tool against a decision-critical field checklist to determine
whether the tool has enough verified data to responsibly recommend or compare it.

KEY CHANGE — Strict Evidence Requirements:
A field is only counted as "verified" for DECISION_READY when backed by
VERIFIED_OFFICIAL or verified evidence status. EDITORIAL_ASSESSMENT counts
as partial. Non-empty fields without evidence backing do NOT count as verified.

States:
- DECISION_READY: Enough decision-critical fields have verified evidence
- PARTIALLY_VERIFIED: Some critical fields verified, others missing or editorial-only
- RESEARCH_REQUIRED: Very few critical fields verified
- CONFLICTING_EVIDENCE: Verified data contains contradictions
- INSUFFICIENT_OFFICIAL_INFORMATION: Tool has too little official data overall

Evidence Status per Field:
- VERIFIED_OFFICIAL: Backed by official first-party source evidence
- VERIFIED: Backed by verified evidence (non-official but confirmed)
- EDITORIAL: Backed by editorial assessment only
- DATA_PRESENT: Field has content but no evidence claim
- UNKNOWN: Field is empty or missing

Decision-critical fields:
1. core_use_case (useCaseTags or discovery.use_cases)
2. meaningful_capabilities (factual_profile.capabilities with content)
3. important_limitations (factual_profile.limitations with content)
4. platform (platforms or discovery.platforms)
5. pricing_model (pricing.model in v1)
6. pricing_state (pricing tiers or pricing claims in evidence)
7. free_plan_status (pricing.freePlan or evidence claims)
8. trial_status (pricing.freeTrial or evidence claims)
9. target_user (bestFor or editorial.best_for)
10. meaningful_alternatives (alternatives with verification)
11. evidence_freshness (recent evidence claims)

DECISION_READY Threshold (Strict):
- pricing_model OR pricing_state must have VERIFIED_OFFICIAL evidence
- meaningful_capabilities must have VERIFIED_OFFICIAL or verified evidence
- At least 3 other fields must have VERIFIED_OFFICIAL or verified evidence
- Total verified fields >= 5 out of 11
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

ROOT = Path(__file__).resolve().parents[1]
TOOLS_V1_PATH = ROOT / "data" / "tools-v1.json"
TOOLS_V2_DIR = ROOT / "data" / "tools-v2"
EVIDENCE_LEDGER_PATH = ROOT / "data" / "evidence" / "evidence-ledger.json"
RESEARCH_PRIORITY_PATH = ROOT / "data" / "research-priority.json"

# A claim older than this is considered stale
STALE_THRESHOLD_DAYS = 90

# Evidence status hierarchy
EVIDENCE_VERIFIED_OFFICIAL = "VERIFIED_OFFICIAL"
EVIDENCE_VERIFIED = "VERIFIED"
EVIDENCE_EDITORIAL = "EDITORIAL"
EVIDENCE_DATA_PRESENT = "DATA_PRESENT"
EVIDENCE_UNKNOWN = "UNKNOWN"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_evidence_index() -> Dict[str, List[Dict]]:
    """Load evidence ledger and index claims by tool_id."""
    ledger = load_json(EVIDENCE_LEDGER_PATH)
    claims = ledger.get("claims", [])
    by_tool: Dict[str, List[Dict]] = {}
    for claim in claims:
        tid = claim.get("tool_id")
        if tid:
            by_tool.setdefault(tid, []).append(claim)
    return by_tool


def load_v2_tools() -> Dict[str, Dict]:
    """Load all tools-v2 JSON files indexed by tool id."""
    tools: Dict[str, Dict] = {}
    for f in TOOLS_V2_DIR.rglob("*.json"):
        try:
            t = load_json(f)
            tid = t.get("identity", {}).get("id", f.stem)
            tools[tid] = t
        except (json.JSONDecodeError, KeyError):
            continue
    return tools


def load_v1_tools() -> Dict[str, Dict]:
    """Load tools-v1.json indexed by tool id."""
    data = load_json(TOOLS_V1_PATH)
    tools_list = data.get("tools", [])
    return {t["id"]: t for t in tools_list}


def check_field_exists(value: Any) -> bool:
    """Check if a field has meaningful content."""
    if value is None:
        return False
    if isinstance(value, str):
        return len(value.strip()) > 0
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, dict):
        return len(value) > 0
    return bool(value)


def get_evidence_status_for_field(
    field_path_patterns: List[str],
    evidence_claims: List[Dict],
    has_data: bool
) -> str:
    """
    Determine the evidence status for a field based on matching evidence claims.
    
    Returns the highest evidence status found:
    - VERIFIED_OFFICIAL if any claim has status verified_official
    - VERIFIED if any claim has status verified
    - EDITORIAL if any claim has status editorial_assessment
    - DATA_PRESENT if field has data but no evidence claims
    - UNKNOWN if field is empty and no evidence
    """
    matching_claims = []
    for claim in evidence_claims:
        fp = claim.get("field_path", "")
        for pattern in field_path_patterns:
            if pattern in fp:
                matching_claims.append(claim)
                break
    
    if not matching_claims:
        return EVIDENCE_DATA_PRESENT if has_data else EVIDENCE_UNKNOWN
    
    # Check for highest status
    statuses = [c.get("status", "") for c in matching_claims]
    
    if "verified_official" in statuses:
        return EVIDENCE_VERIFIED_OFFICIAL
    if "verified" in statuses:
        return EVIDENCE_VERIFIED
    if "editorial_assessment" in statuses:
        return EVIDENCE_EDITORIAL
    if "needs_review" in statuses:
        return EVIDENCE_EDITORIAL  # Treat needs_review as editorial-level
    if "disputed" in statuses:
        return EVIDENCE_EDITORIAL  # Disputed claims still indicate some research
    
    return EVIDENCE_DATA_PRESENT if has_data else EVIDENCE_UNKNOWN


def is_strong_evidence(status: str) -> bool:
    """Check if an evidence status counts as strong verification for DECISION_READY."""
    return status in (EVIDENCE_VERIFIED_OFFICIAL, EVIDENCE_VERIFIED)


def is_any_evidence(status: str) -> bool:
    """Check if an evidence status indicates any research backing."""
    return status in (EVIDENCE_VERIFIED_OFFICIAL, EVIDENCE_VERIFIED, EVIDENCE_EDITORIAL)


def evaluate_tool(
    tool_id: str,
    v1_tool: Dict,
    v2_tool: Dict,
    evidence_claims: List[Dict],
) -> Dict[str, Any]:
    """
    Evaluate a single tool against the decision-critical field checklist.
    
    STRICT EVIDENCE MODE: Each field gets an evidence_status that reflects
    the quality of backing evidence, not just whether the field is non-empty.
    
    Returns a detailed evaluation result with per-field evidence status.
    """
    fields: Dict[str, Dict[str, Any]] = {}
    now = datetime.now()
    stale_cutoff = now - timedelta(days=STALE_THRESHOLD_DAYS)

    # --- 1. Core Use Case ---
    v1_uc = v1_tool.get("useCaseTags")
    v2_uc = (v2_tool.get("discovery") or {}).get("use_cases")
    has_use_case = check_field_exists(v1_uc) or check_field_exists(v2_uc)
    ev_status = get_evidence_status_for_field(
        ["use_case", "useCase"], evidence_claims, has_use_case
    )
    fields["core_use_case"] = {
        "verified": is_strong_evidence(ev_status),
        "evidence_status": ev_status,
        "has_data": has_use_case,
        "source": "v1" if check_field_exists(v1_uc) else ("v2" if check_field_exists(v2_uc) else None),
        "detail": f"{len(v1_uc or [])} v1 tags, {len(v2_uc or [])} v2 tags"
    }

    # --- 2. Meaningful Capabilities ---
    v1_caps = v1_tool.get("pros")
    v2_caps = (v2_tool.get("factual_profile") or {}).get("capabilities")
    has_capabilities = (
        check_field_exists(v1_caps) or
        check_field_exists(v2_caps)
    )
    ev_status = get_evidence_status_for_field(
        ["capabilities", "capability"], evidence_claims, has_capabilities
    )
    fields["meaningful_capabilities"] = {
        "verified": is_strong_evidence(ev_status),
        "evidence_status": ev_status,
        "has_data": has_capabilities,
        "source": "evidence" if is_any_evidence(ev_status) else ("v1" if check_field_exists(v1_caps) else "v2"),
        "detail": f"{len(v1_caps or [])} v1 pros, {len(v2_caps or [])} v2 caps"
    }

    # --- 3. Important Limitations ---
    v1_cons = v1_tool.get("cons")
    v1_skip = v1_tool.get("skipIf")
    v2_lim = (v2_tool.get("factual_profile") or {}).get("limitations")
    v2_not_rec = (v2_tool.get("editorial") or {}).get("not_recommended_for")
    has_limitations = (
        check_field_exists(v1_cons) or
        check_field_exists(v1_skip) or
        check_field_exists(v2_lim) or
        check_field_exists(v2_not_rec)
    )
    ev_status = get_evidence_status_for_field(
        ["limitations", "limitation"], evidence_claims, has_limitations
    )
    fields["important_limitations"] = {
        "verified": is_strong_evidence(ev_status),
        "evidence_status": ev_status,
        "has_data": has_limitations,
        "source": "evidence" if is_any_evidence(ev_status) else ("v1" if check_field_exists(v1_cons) or check_field_exists(v1_skip) else "v2"),
        "detail": f"{len(v1_cons or [])} v1 cons, {len(v1_skip or [])} skipIf, {len(v2_lim or [])} v2 lims"
    }

    # --- 4. Platform ---
    v1_plat = v1_tool.get("platforms")
    v2_plat = (v2_tool.get("discovery") or {}).get("platforms")
    has_platform = check_field_exists(v1_plat) or check_field_exists(v2_plat)
    ev_status = get_evidence_status_for_field(
        ["platforms", "platform"], evidence_claims, has_platform
    )
    fields["platform"] = {
        "verified": is_strong_evidence(ev_status),
        "evidence_status": ev_status,
        "has_data": has_platform,
        "source": "v1" if check_field_exists(v1_plat) else "v2",
        "detail": f"{len(v1_plat or [])} v1 platforms, {len(v2_plat or [])} v2 platforms"
    }

    # --- 5. Pricing Model ---
    v1_pricing = v1_tool.get("pricing") or {}
    v1_model = v1_pricing.get("model")
    has_pricing_model = check_field_exists(v1_model)
    ev_status = get_evidence_status_for_field(
        ["pricing.model", "model"], evidence_claims, has_pricing_model
    )
    fields["pricing_model"] = {
        "verified": is_strong_evidence(ev_status),
        "evidence_status": ev_status,
        "has_data": has_pricing_model,
        "source": "evidence" if is_any_evidence(ev_status) else "v1",
        "detail": f"model={v1_model}"
    }

    # --- 6. Pricing State (tiers or detailed pricing data) ---
    v1_tiers = v1_pricing.get("tiers")
    has_pricing_state = check_field_exists(v1_tiers)
    ev_status = get_evidence_status_for_field(
        ["pricing.tiers", "pricing_status"], evidence_claims, has_pricing_state
    )
    fields["pricing_state"] = {
        "verified": is_strong_evidence(ev_status),
        "evidence_status": ev_status,
        "has_data": has_pricing_state,
        "source": "v1" if check_field_exists(v1_tiers) else "evidence",
        "detail": f"{len(v1_tiers or [])} tiers"
    }

    # --- 7. Free Plan Status ---
    v1_free = v1_pricing.get("freePlan", {})
    v1_free_avail = v1_free.get("available")
    has_free_plan = v1_free_avail is not None
    ev_status = get_evidence_status_for_field(
        ["pricing.freePlan", "free_plan"], evidence_claims, has_free_plan
    )
    fields["free_plan_status"] = {
        "verified": is_strong_evidence(ev_status),
        "evidence_status": ev_status,
        "has_data": has_free_plan,
        "value": v1_free_avail,
        "source": "v1" if v1_free_avail is not None else "evidence",
        "detail": f"available={v1_free_avail}"
    }

    # --- 8. Trial Status ---
    v1_trial = v1_pricing.get("freeTrial", {})
    v1_trial_avail = v1_trial.get("available")
    has_trial = v1_trial_avail is not None
    ev_status = get_evidence_status_for_field(
        ["pricing.freeTrial", "trial"], evidence_claims, has_trial
    )
    fields["trial_status"] = {
        "verified": is_strong_evidence(ev_status),
        "evidence_status": ev_status,
        "has_data": has_trial,
        "value": v1_trial_avail,
        "source": "v1" if v1_trial_avail is not None else "evidence",
        "detail": f"available={v1_trial_avail}"
    }

    # --- 9. Target User (bestFor) ---
    v1_bf = v1_tool.get("bestFor")
    v2_bf = (v2_tool.get("editorial") or {}).get("best_for")
    has_target_user = check_field_exists(v1_bf) or check_field_exists(v2_bf)
    ev_status = get_evidence_status_for_field(
        ["bestFor", "best_for", "target_user"], evidence_claims, has_target_user
    )
    fields["target_user"] = {
        "verified": is_strong_evidence(ev_status),
        "evidence_status": ev_status,
        "has_data": has_target_user,
        "source": "v1" if check_field_exists(v1_bf) else "v2",
        "detail": f"{len(v1_bf or [])} v1 bestFor, {len(v2_bf or [])} v2 best_for"
    }

    # --- 10. Meaningful Alternatives ---
    v1_alts = v1_tool.get("alternatives")
    v2_alts = (v2_tool.get("relationships") or {}).get("alternatives")
    verified_alts = 0
    if v1_alts:
        for a in v1_alts:
            if isinstance(a, dict) and a.get("verification_status") == "VERIFIED":
                verified_alts += 1
    string_alt_count = 0
    if v2_alts:
        string_alt_count = sum(1 for a in v2_alts if isinstance(a, str))
    has_alternatives = check_field_exists(v1_alts) or check_field_exists(v2_alts)
    # Alternatives are editorial by nature — they can't be "officially verified"
    # but having alternatives listed counts as DATA_PRESENT
    ev_status = EVIDENCE_DATA_PRESENT if has_alternatives else EVIDENCE_UNKNOWN
    fields["meaningful_alternatives"] = {
        "verified": False,  # Alternatives are editorial, not verifiable
        "evidence_status": ev_status,
        "has_data": has_alternatives,
        "verified_count": verified_alts,
        "string_refs": string_alt_count,
        "source": "v1" if check_field_exists(v1_alts) else "v2",
        "detail": f"{len(v1_alts or [])} v1 alts, {len(v2_alts or [])} v2 alts, {verified_alts} verified"
    }

    # --- 11. Evidence Freshness ---
    recent_claims = []
    for c in evidence_claims:
        verified_at = c.get("verified_at") or c.get("accessed_at")
        if verified_at:
            try:
                v_date = datetime.strptime(verified_at[:10], "%Y-%m-%d")
                if v_date >= stale_cutoff:
                    recent_claims.append(c)
            except (ValueError, TypeError):
                pass
    has_fresh_evidence = len(recent_claims) > 0
    total_evidence = len(evidence_claims)
    ev_status = EVIDENCE_VERIFIED if has_fresh_evidence else EVIDENCE_UNKNOWN
    fields["evidence_freshness"] = {
        "verified": has_fresh_evidence,
        "evidence_status": ev_status,
        "has_data": total_evidence > 0,
        "total_claims": total_evidence,
        "recent_claims": len(recent_claims),
        "detail": f"{total_evidence} total claims, {len(recent_claims)} recent"
    }

    # --- Check for conflicting evidence ---
    conflicting = False
    for c in evidence_claims:
        if c.get("status") == "disputed":
            conflicting = True
            break
    if not conflicting:
        field_statuses: Dict[str, List[str]] = {}
        for c in evidence_claims:
            fp = c.get("field_path", "")
            field_statuses.setdefault(fp, []).append(c.get("status", ""))
        for fp, statuses in field_statuses.items():
            if "disputed" in statuses and "verified" in statuses:
                conflicting = True
                break

    # --- Calculate overall state (STRICT EVIDENCE MODE) ---
    # Count fields by evidence quality
    strong_verified_count = sum(
        1 for f in fields.values() if is_strong_evidence(f.get("evidence_status", EVIDENCE_UNKNOWN))
    )
    editorial_count = sum(
        1 for f in fields.values() if f.get("evidence_status") == EVIDENCE_EDITORIAL
    )
    data_present_count = sum(
        1 for f in fields.values() if f.get("evidence_status") == EVIDENCE_DATA_PRESENT
    )
    total_fields = len(fields)

    # Check key fields for strict requirements
    pricing_verified = (
        is_strong_evidence(fields["pricing_model"].get("evidence_status")) or
        is_strong_evidence(fields["pricing_state"].get("evidence_status"))
    )
    capabilities_verified = is_strong_evidence(fields["meaningful_capabilities"].get("evidence_status"))

    if conflicting:
        overall_state = "CONFLICTING_EVIDENCE"
    elif (
        strong_verified_count >= 5 and
        pricing_verified and
        capabilities_verified
    ):
        # Strict: 5+ fields with strong evidence, including pricing and capabilities
        overall_state = "DECISION_READY"
    elif strong_verified_count >= 3 or (strong_verified_count >= 1 and editorial_count >= 3):
        # At least 3 strong evidence fields, or 1 strong + 3 editorial
        overall_state = "PARTIALLY_VERIFIED"
    elif strong_verified_count >= 1 or editorial_count >= 2 or data_present_count >= 5:
        # Some evidence or substantial data
        overall_state = "PARTIALLY_VERIFIED"
    elif data_present_count >= 3:
        # Data present but little evidence
        overall_state = "PARTIALLY_VERIFIED"
    else:
        overall_state = "RESEARCH_REQUIRED"

    # Special case: if there's absolutely no evidence and very few fields
    if total_evidence == 0 and strong_verified_count == 0 and editorial_count == 0:
        if data_present_count <= 3:
            overall_state = "INSUFFICIENT_OFFICIAL_INFORMATION"

    # For backward compatibility, keep "verified" count as strong evidence count
    verified_count = strong_verified_count

    return {
        "tool_id": tool_id,
        "overall_state": overall_state,
        "verified_fields": verified_count,
        "total_fields": total_fields,
        "verification_percentage": round(verified_count / total_fields * 100) if total_fields > 0 else 0,
        "fields": fields,
        "total_evidence_claims": total_evidence,
        "has_conflicting_evidence": conflicting,
        "strong_verified_count": strong_verified_count,
        "editorial_count": editorial_count,
        "data_present_count": data_present_count,
    }


def main():
    print("=" * 60)
    print("ToolNest Decision-Readiness Evaluation (Strict Evidence Mode)")
    print("=" * 60)

    # Load data
    print("\nLoading data...")
    evidence_index = load_evidence_index()
    v2_tools = load_v2_tools()
    v1_tools = load_v1_tools()

    print(f"  Evidence claims: {sum(len(v) for v in evidence_index.values())} across {len(evidence_index)} tools")
    print(f"  V2 tool files: {len(v2_tools)}")
    print(f"  V1 tools: {len(v1_tools)}")

    # Load previous decision readiness summary for downgrade tracking
    previous_summary_path = ROOT / "data" / "decision-readiness-summary.json"
    previous_states: Dict[str, str] = {}
    if previous_summary_path.exists():
        try:
            prev = load_json(previous_summary_path)
            for tool_entry in prev.get("tools", []):
                previous_states[tool_entry["tool_id"]] = tool_entry.get("state", "")
        except (json.JSONDecodeError, KeyError):
            pass

    # All tool IDs from v1 (authoritative list)
    all_tool_ids = sorted(v1_tools.keys())

    # Evaluate each tool
    results: List[Dict] = []
    for tool_id in all_tool_ids:
        v1_tool = v1_tools.get(tool_id, {})
        v2_tool = v2_tools.get(tool_id, {})
        evidence_claims = evidence_index.get(tool_id, [])
        result = evaluate_tool(tool_id, v1_tool, v2_tool, evidence_claims)
        results.append(result)

    # Aggregate statistics
    state_counts: Dict[str, int] = {}
    for r in results:
        state = r["overall_state"]
        state_counts[state] = state_counts.get(state, 0) + 1

    # Track downgrades
    downgrades = []
    for r in results:
        prev_state = previous_states.get(r["tool_id"], "")
        if prev_state == "DECISION_READY" and r["overall_state"] != "DECISION_READY":
            downgrades.append({
                "tool_id": r["tool_id"],
                "previous_state": prev_state,
                "new_state": r["overall_state"],
                "strong_verified": r.get("strong_verified_count", 0),
                "editorial": r.get("editorial_count", 0),
                "data_present": r.get("data_present_count", 0),
                "pricing_verified": is_strong_evidence(r["fields"]["pricing_state"].get("evidence_status")) or is_strong_evidence(r["fields"]["pricing_model"].get("evidence_status")),
                "capabilities_verified": is_strong_evidence(r["fields"]["meaningful_capabilities"].get("evidence_status"))
            })

    print("\n" + "=" * 60)
    print("DECISION-READINESS STRICT EVIDENCE REPORT")
    print("=" * 60)

    print(f"\nTotal tools evaluated: {len(results)}")
    print(f"\nOverall State Distribution:")
    for state in ["DECISION_READY", "PARTIALLY_VERIFIED", "RESEARCH_REQUIRED", "CONFLICTING_EVIDENCE", "INSUFFICIENT_OFFICIAL_INFORMATION"]:
        count = state_counts.get(state, 0)
        pct = round(count / len(results) * 100) if results else 0
        print(f"  {state}: {count} ({pct}%)")

    # Downgrade report
    if downgrades:
        print(f"\nDOWNGRADES from DECISION_READY: {len(downgrades)}")
        for d in sorted(downgrades, key=lambda x: x["tool_id"]):
            print(f"  {d['tool_id']}: strong_verified={d['strong_verified']}, editorial={d['editorial']}, pricing_verified={d['pricing_verified']}, capabilities_verified={d['capabilities_verified']}")

    # Field-level verification rates (strict evidence)
    print(f"\nField-Level Verification Rates (Strict Evidence):")
    field_names = [
        "core_use_case", "meaningful_capabilities", "important_limitations",
        "platform", "pricing_model", "pricing_state", "free_plan_status",
        "trial_status", "target_user", "meaningful_alternatives", "evidence_freshness"
    ]
    for fname in field_names:
        verified = sum(1 for r in results if r["fields"].get(fname, {}).get("verified"))
        editorial = sum(1 for r in results if r["fields"].get(fname, {}).get("evidence_status") == EVIDENCE_EDITORIAL)
        data_present = sum(1 for r in results if r["fields"].get(fname, {}).get("evidence_status") == EVIDENCE_DATA_PRESENT)
        pct = round(verified / len(results) * 100) if results else 0
        print(f"  {fname}: verified={verified}, editorial={editorial}, data_present={data_present} ({pct}% verified)")

    # Tools by state
    print(f"\nTools by State:")
    for state in ["DECISION_READY", "PARTIALLY_VERIFIED", "RESEARCH_REQUIRED", "CONFLICTING_EVIDENCE", "INSUFFICIENT_OFFICIAL_INFORMATION"]:
        tools_in_state = [r["tool_id"] for r in results if r["overall_state"] == state]
        if tools_in_state:
            print(f"\n  {state} ({len(tools_in_state)}):")
            for tid in sorted(tools_in_state)[:20]:
                r = next(r for r in results if r["tool_id"] == tid)
                print(f"    {tid}: strong_verified={r.get('strong_verified_count', 0)}, editorial={r.get('editorial_count', 0)}, data_present={r.get('data_present_count', 0)}")
            if len(tools_in_state) > 20:
                print(f"    ... and {len(tools_in_state) - 20} more")

    # Update v2 JSON files with decision_readiness
    print(f"\nUpdating v2 JSON files with decision_readiness...")
    updated_count = 0
    for result in results:
        tool_id = result["tool_id"]
        v2_path = TOOLS_V2_DIR / "legacy" / f"{tool_id}.json"
        if not v2_path.exists():
            v2_path = TOOLS_V2_DIR / "expansion" / f"{tool_id}.json"
        if v2_path.exists():
            try:
                v2_data = load_json(v2_path)
                v2_data["decision_readiness"] = {
                    "state": result["overall_state"],
                    "verified_fields": result["verified_fields"],
                    "total_fields": result["total_fields"],
                    "verification_percentage": result["verification_percentage"],
                    "total_evidence_claims": result["total_evidence_claims"],
                    "strong_verified_count": result.get("strong_verified_count", 0),
                    "editorial_count": result.get("editorial_count", 0),
                    "data_present_count": result.get("data_present_count", 0),
                    "field_details": {
                        fname: {
                            "verified": fdata.get("verified"),
                            "evidence_status": fdata.get("evidence_status", "UNKNOWN"),
                            "has_data": fdata.get("has_data", False),
                            "detail": fdata.get("detail", "")
                        }
                        for fname, fdata in result["fields"].items()
                    },
                    "evaluated_at": datetime.now().isoformat()
                }
                save_json(v2_path, v2_data)
                updated_count += 1
            except (json.JSONDecodeError, KeyError) as e:
                print(f"  Warning: Could not update {v2_path}: {e}")

    print(f"  Updated {updated_count} v2 JSON files")

    # Generate summary JSON
    summary = {
        "generated_at": datetime.now().isoformat(),
        "evaluation_mode": "strict_evidence",
        "total_tools": len(results),
        "state_distribution": state_counts,
        "downgrades_from_decision_ready": downgrades,
        "field_verification_rates": {
            fname: {
                "verified": sum(1 for r in results if r["fields"].get(fname, {}).get("verified")),
                "editorial": sum(1 for r in results if r["fields"].get(fname, {}).get("evidence_status") == EVIDENCE_EDITORIAL),
                "data_present": sum(1 for r in results if r["fields"].get(fname, {}).get("evidence_status") == EVIDENCE_DATA_PRESENT),
                "unknown": sum(1 for r in results if r["fields"].get(fname, {}).get("evidence_status") == EVIDENCE_UNKNOWN),
                "total": len(results),
                "percentage": round(sum(1 for r in results if r["fields"].get(fname, {}).get("verified")) / len(results) * 100) if results else 0
            }
            for fname in field_names
        },
        "tools": [
            {
                "tool_id": r["tool_id"],
                "state": r["overall_state"],
                "verification_percentage": r["verification_percentage"],
                "evidence_claims": r["total_evidence_claims"],
                "strong_verified_count": r.get("strong_verified_count", 0),
                "editorial_count": r.get("editorial_count", 0),
                "data_present_count": r.get("data_present_count", 0)
            }
            for r in sorted(results, key=lambda x: (-x["verification_percentage"], x["tool_id"]))
        ]
    }

    summary_path = ROOT / "data" / "decision-readiness-summary.json"
    save_json(summary_path, summary)
    print(f"\nSummary saved to {summary_path}")

    # Print final summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Tools evaluated: {len(results)}")
    print(f"DECISION_READY: {state_counts.get('DECISION_READY', 0)}")
    print(f"PARTIALLY_VERIFIED: {state_counts.get('PARTIALLY_VERIFIED', 0)}")
    print(f"RESEARCH_REQUIRED: {state_counts.get('RESEARCH_REQUIRED', 0)}")
    print(f"CONFLICTING_EVIDENCE: {state_counts.get('CONFLICTING_EVIDENCE', 0)}")
    print(f"INSUFFICIENT_OFFICIAL_INFORMATION: {state_counts.get('INSUFFICIENT_OFFICIAL_INFORMATION', 0)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
