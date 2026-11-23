#!/usr/bin/env python3
"""Source monitor — true continuous fact verification on top of freshness infrastructure.

Replaces the metadata-only VERIFIED_CURRENTLY status with actual verification states:
- VERIFIED_CURRENT — source actually fetched and within freshness window
- DUE_FOR_RECHECK — past threshold, needs fetch
- RECHECK_PASSED — source fetched, fact reconfirmed
- CHANGE_DETECTED — source fetched, material difference found
- REVIEW_REQUIRED — ambiguous result
- SOURCE_UNAVAILABLE — fetch failed (timeout, 403, etc.)
- PARSER_FAILURE — fetch succeeded but extraction failed
- CONFLICTING_OFFICIAL_INFORMATION — multiple sources disagree

Key invariant: last_verified_date only advances when a source is actually fetched
and parsed successfully. A metadata-only check must never create fake freshness.

Usage:
    python3 scripts/source_monitor.py                    # Dry run analysis
    python3 scripts/source_monitor.py --fetch            # Actually fetch sources
    python3 scripts/source_monitor.py --tool semrush     # Monitor a specific tool
    python3 scripts/source_monitor.py --report-only      # Generate report without changes
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "data" / "evidence" / "evidence-ledger.json"
FRESHNESS_POLICY_PATH = ROOT / "data" / "freshness-policy.json"
SOURCE_REGISTRY_PATH = ROOT / "data" / "sources" / "source-registry.json"
TOOLS_V1_PATH = ROOT / "data" / "tools-v1.json"
CATALOG_RECON_PATH = ROOT / "data" / "catalog-reconciliation.json"
REPORTS_DIR = ROOT / "reports" / "phase6"

# Pipeline component imports (lazy-loaded to avoid circular deps)
def _import_pipeline_components():
    """Lazy-import pipeline components used in the fetch→extract→update chain."""
    from extractors import get_extractor, PricingExtractor, FeatureExtractor
    from change_detector import classify_change, is_material_change, ChangeType
    from anomaly_detector import detect_anomalies, has_critical_anomaly
    from change_confidence import classify_change_risk, RiskLevel
    from update_policy import classify_update, UpdateTier, create_update_request
    return (
        get_extractor, PricingExtractor, FeatureExtractor,
        classify_change, is_material_change, ChangeType,
        detect_anomalies, has_critical_anomaly,
        classify_change_risk, RiskLevel,
        classify_update, UpdateTier, create_update_request,
    )


class VerificationStatus(str, Enum):
    """Distinct verification statuses that separate actual verification from date-window checks."""
    VERIFIED_CURRENT = "verified_current"
    DUE_FOR_RECHECK = "due_for_recheck"
    RECHECK_PASSED = "recheck_passed"
    CHANGE_DETECTED = "change_detected"
    REVIEW_REQUIRED = "review_required"
    SOURCE_UNAVAILABLE = "source_unavailable"
    PARSER_FAILURE = "parser_failure"
    CONFLICTING_OFFICIAL_INFORMATION = "conflicting_official_information"


# Map old status strings to new enum for backward compatibility
STATUS_COMPAT_MAP = {
    "verified": VerificationStatus.VERIFIED_CURRENT,
    "verified_official": VerificationStatus.VERIFIED_CURRENT,
    "needs_review": VerificationStatus.REVIEW_REQUIRED,
    "disputed": VerificationStatus.CONFLICTING_OFFICIAL_INFORMATION,
    "editorial_assessment": VerificationStatus.REVIEW_REQUIRED,
}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def load_freshness_policy() -> dict:
    if not FRESHNESS_POLICY_PATH.is_file():
        return {
            "thresholds": {
                "pricing": 90, "plan_limit": 90, "billing": 90,
                "capabilities": 180, "free_trial": 90, "general": 365,
            },
            "default_threshold": 365,
        }
    return load_json(FRESHNESS_POLICY_PATH)


def get_threshold_for_claim(claim_type: str, policy: dict) -> int:
    thresholds = policy.get("thresholds", {})
    return thresholds.get(claim_type, policy.get("default_threshold", 365))


def get_production_tool_ids() -> set:
    """Get the set of 153 production tool IDs from tools-v1.json."""
    v1 = load_json(TOOLS_V1_PATH)
    tools = v1.get("tools", []) if isinstance(v1, dict) else v1
    return {t["id"] for t in tools}


def get_expansion_only_ids() -> set:
    """Get the set of expansion-only tool IDs that must not leak into production."""
    if not CATALOG_RECON_PATH.is_file():
        return set()
    recon = load_json(CATALOG_RECON_PATH)
    return set(recon.get("expansion_only_tools", []))


def classify_claim_with_semantics(
    claim: dict, policy: dict, as_of: date, source_fetch_results: Optional[dict] = None
) -> Tuple[VerificationStatus, int]:
    """Classify a claim with proper semantics.
    
    Unlike the old classify_claim() which returns VERIFIED_CURRENTLY based purely
    on date windows, this function distinguishes between:
    - Claims that were actually verified by fetching sources
    - Claims that are merely within a freshness window but never actually checked
    
    Args:
        claim: The evidence claim dict
        policy: Freshness policy dict
        as_of: Date to check against
        source_fetch_results: Optional dict of tool_id -> fetch result from actual source fetching
    
    Returns:
        Tuple of (VerificationStatus, urgency_days)
    """
    claim_type = claim.get("claim_type", "general")
    threshold_days = get_threshold_for_claim(claim_type, policy)
    
    stale_after = claim.get("stale_after")
    verified_at = claim.get("verified_at")
    tool_id = claim.get("tool_id", "")
    last_verified = claim.get("last_verified_date")
    
    # If we have actual fetch results for this tool, use them
    if source_fetch_results and tool_id in source_fetch_results:
        fetch_result = source_fetch_results[tool_id]
        fetch_status = fetch_result.get("status")
        
        if fetch_status == "success":
            if fetch_result.get("change_detected"):
                return VerificationStatus.CHANGE_DETECTED, 0
            else:
                return VerificationStatus.RECHECK_PASSED, 0
        elif fetch_status == "parser_failure":
            return VerificationStatus.PARSER_FAILURE, 0
        elif fetch_status == "unavailable":
            return VerificationStatus.SOURCE_UNAVAILABLE, 0
        elif fetch_status == "conflict":
            return VerificationStatus.CONFLICTING_OFFICIAL_INFORMATION, 0
        else:
            return VerificationStatus.REVIEW_REQUIRED, 0
    
    # No actual fetch — fall back to date-window classification
    # This is the METADATA-ONLY path that the old pipeline used
    
    # GAP FIX: Metadata-only freshness guard
    # A metadata-only check (HTTP headers, file dates, stale_after window)
    # MUST NEVER refresh last_verified_date or factual verification dates.
    # VERIFIED_CURRENT can only be returned when a source was actually fetched
    # and parsed successfully in this run (handled above via source_fetch_results).
    # In the metadata-only path, claims within their freshness window are marked
    # DUE_FOR_RECHECK with negative urgency (days until they become urgent).
    
    if not stale_after and not verified_at and not last_verified:
        return VerificationStatus.DUE_FOR_RECHECK, 0
    
    # Check if past stale_after date
    if stale_after:
        try:
            stale_date = date.fromisoformat(stale_after)
            if stale_date < as_of:
                days_overdue = (as_of - stale_date).days
                return VerificationStatus.DUE_FOR_RECHECK, days_overdue
            else:
                # Within window but never actually fetched — this is NOT verified_current
                # It's a metadata-only status — mark as DUE_FOR_RECHECK with low urgency
                days_until_stale = (stale_date - as_of).days
                # METADATA-ONLY GUARD: Do NOT return VERIFIED_CURRENT based on
                # last_verified_date alone. That date was set by a previous actual
                # fetch, but we have no evidence the fact is still current without
                # an actual re-fetch. The old code incorrectly returned VERIFIED_CURRENT
                # here, creating fake freshness.
                return VerificationStatus.DUE_FOR_RECHECK, -days_until_stale
        except (ValueError, TypeError):
            return VerificationStatus.DUE_FOR_RECHECK, 0
    
    # Check based on verified_at + threshold
    if verified_at:
        try:
            verified_date = date.fromisoformat(verified_at)
            threshold_date = verified_date + timedelta(days=threshold_days)
            if threshold_date < as_of:
                days_overdue = (as_of - threshold_date).days
                return VerificationStatus.DUE_FOR_RECHECK, days_overdue
            else:
                days_until_stale = (threshold_date - as_of).days
                # METADATA-ONLY GUARD: Even within threshold, without actual fetch,
                # this is DUE_FOR_RECHECK, not VERIFIED_CURRENT
                return VerificationStatus.DUE_FOR_RECHECK, -days_until_stale
        except (ValueError, TypeError):
            return VerificationStatus.DUE_FOR_RECHECK, 0
    
    return VerificationStatus.DUE_FOR_RECHECK, 0


def _claim_to_old_fields(claim: dict) -> dict:
    """Convert a ledger claim's value into the field format expected by change_detector.
    
    Maps the claim's structured value back to the extractor output format so that
    change_detector can compare old vs new fields.
    """
    claim_type = claim.get("claim_type", "")
    value = claim.get("value")
    
    if claim_type == "pricing":
        # Convert pricing claim value to extractor format
        fields = {"pricing": {}}
        if isinstance(value, dict):
            plans = value.get("plans", [])
            tiers = []
            for plan in plans:
                tier = {
                    "plan": plan.get("name", ""),
                    "price": plan.get("displayed_monthly_usd", plan.get("amount")),
                    "currency": value.get("currency", "USD"),
                    "billing_interval": "monthly",
                }
                if plan.get("renewal_monthly_usd") is not None:
                    tier["renewal_price"] = plan["renewal_monthly_usd"]
                tiers.append(tier)
            fields["pricing"]["tiers"] = tiers
            fields["pricing"]["currency"] = value.get("currency")
        return fields
    elif claim_type == "free_plan":
        fields = {"pricing": {}}
        if isinstance(value, str):
            fields["pricing"]["free_plan"] = "free plan" in value.lower() and "no free plan" not in value.lower()
        elif isinstance(value, bool):
            fields["pricing"]["free_plan"] = value
        return fields
    elif claim_type == "trial":
        fields = {}
        if isinstance(value, dict):
            fields["trial"] = value
        elif isinstance(value, str):
            fields["trial"] = {"available": "trial" in value.lower(), "duration_days": None}
        return fields
    elif claim_type in ("capability", "feature"):
        fields = {}
        if isinstance(value, list):
            fields["capabilities"] = value
        return fields
    elif claim_type == "platform":
        fields = {}
        if isinstance(value, list):
            fields["platforms"] = value
        elif isinstance(value, str):
            fields["platforms"] = [value]
        return fields
    elif claim_type == "limitation":
        fields = {}
        if isinstance(value, list):
            fields["limitations"] = value
        return fields
    elif claim_type == "billing":
        fields = {"pricing": {}}
        if isinstance(value, dict):
            fields["pricing"]["billing_info"] = value
        return fields
    
    return {}


def _run_pipeline_for_claim(
    claim: dict,
    fetch_result: dict,
    source_registry: dict,
    as_of: date,
) -> dict:
    """Run the full pipeline for a single claim: extract → detect → anomaly → confidence → policy.
    
    Args:
        claim: The evidence claim from the ledger
        fetch_result: The fetch result dict from source_fetcher (per-source results)
        source_registry: The source registry for this tool
        as_of: Current date
    
    Returns:
        Pipeline result dict with status, tier, new_value, anomalies, etc.
    """
    tool_id = claim.get("tool_id", "")
    claim_type = claim.get("claim_type", "")
    claim_id = claim.get("claim_id", "")
    
    result = {
        "claim_id": claim_id,
        "tool_id": tool_id,
        "claim_type": claim_type,
        "status": VerificationStatus.REVIEW_REQUIRED.value,
        "tier": None,
        "new_value": None,
        "anomalies": [],
        "change_type": None,
        "risk_level": None,
        "action_taken": "none",
        "last_verified_preserved": True,
    }
    
    # Import all pipeline components once
    try:
        (
            get_extractor, PricingExtractor, FeatureExtractor,
            classify_change, is_material_change, ChangeType,
            detect_anomalies, has_critical_anomaly,
            classify_change_risk, RiskLevel,
            classify_update, UpdateTier, create_update_request,
        ) = _import_pipeline_components()
    except Exception:
        result["status"] = VerificationStatus.PARSER_FAILURE.value
        result["action_taken"] = "pipeline_import_failed"
        return result
    
    # Find the source role for this claim type
    source_role = _claim_type_to_source_role(claim_type)
    if not source_role:
        result["status"] = VerificationStatus.REVIEW_REQUIRED.value
        result["action_taken"] = "no_source_role"
        return result
    
    # Get the appropriate extractor
    try:
        extractor = get_extractor(tool_id, source_role)
    except Exception:
        result["status"] = VerificationStatus.PARSER_FAILURE.value
        result["action_taken"] = "extractor_import_failed"
        return result
    
    if not extractor:
        result["status"] = VerificationStatus.REVIEW_REQUIRED.value
        result["action_taken"] = "no_extractor_for_role"
        return result
    
    # Find the matching source in fetch results
    claim_source_ids = claim.get("source_ids", [])
    matched_source_result = None
    matched_source_url = None
    
    for sid in claim_source_ids:
        if sid in fetch_result.get("sources", {}):
            src_result = fetch_result["sources"][sid]
            if src_result.get("status") == "success" and src_result.get("text_content"):
                matched_source_result = src_result
                matched_source_url = src_result.get("url", "")
                break
    
    if not matched_source_result:
        # Check overall fetch status
        overall_status = fetch_result.get("status", "unavailable")
        if overall_status in ("unavailable",):
            result["status"] = VerificationStatus.SOURCE_UNAVAILABLE.value
            result["action_taken"] = "source_unavailable"
        else:
            result["status"] = VerificationStatus.REVIEW_REQUIRED.value
            result["action_taken"] = "no_matching_source"
        return result
    
    # Step 1: Extract new fields from fetched content
    try:
        text_content = matched_source_result.get("text_content", "")
        new_fields = extractor.extract(text_content, matched_source_url or "")
    except Exception as e:
        result["status"] = VerificationStatus.PARSER_FAILURE.value
        result["action_taken"] = f"extraction_failed: {str(e)[:100]}"
        return result
    
    # Step 2: Compare old vs new fields via change_detector
    old_fields = _claim_to_old_fields(claim)
    old_fingerprint = claim.get("content_fingerprint")
    new_fingerprint = matched_source_result.get("fingerprint")
    
    try:
        change_type, specific_changes = classify_change(
            old_fingerprint=old_fingerprint,
            new_fingerprint=new_fingerprint,
            old_fields=old_fields,
            new_fields=new_fields,
        )
    except Exception as e:
        result["status"] = VerificationStatus.PARSER_FAILURE.value
        result["action_taken"] = f"change_detection_failed: {str(e)[:100]}"
        return result
    
    result["change_type"] = change_type.value
    
    # Step 3: Anomaly detection
    try:
        anomalies = detect_anomalies(
            old_fields=old_fields,
            new_fields=new_fields,
            old_fingerprint=old_fingerprint,
            new_fingerprint=new_fingerprint,
        )
    except Exception:
        anomalies = []
    
    result["anomalies"] = anomalies
    
    if has_critical_anomaly(anomalies):
        result["status"] = VerificationStatus.REVIEW_REQUIRED.value
        result["action_taken"] = "critical_anomaly_preserved"
        result["last_verified_preserved"] = True
        return result
    
    # Step 4: Risk classification
    try:
        risk_level, risk_explanation = classify_change_risk(
            change_type=change_type.value,
            specific_changes=specific_changes,
            old_value=old_fields,
            new_value=new_fields,
        )
    except Exception:
        risk_level = RiskLevel.MEDIUM_RISK
        risk_explanation = "risk_classification_failed"
    
    result["risk_level"] = risk_level.value
    
    # Step 5: Policy tier classification
    try:
        source_official = False
        for sid in claim_source_ids:
            src = _get_source_from_ledger(sid)
            if src and src.get("official"):
                source_official = True
                break
        
        tier, tier_explanation = classify_update(
            change_type=change_type.value,
            risk_level=risk_level.value,
            anomaly_detected=bool(anomalies),
            source_official=source_official,
            claim_type=claim_type,
        )
    except Exception:
        tier = UpdateTier.TIER_2
        tier_explanation = "policy_classification_failed"
    
    result["tier"] = tier.value
    
    # Step 6: Apply tier-based action
    if change_type == ChangeType.NO_CHANGE:
        # No change detected — recheck passed
        result["status"] = VerificationStatus.RECHECK_PASSED.value
        result["action_taken"] = "recheck_passed_no_change"
        result["last_verified_preserved"] = False  # Will advance date
        result["new_value"] = claim.get("value")  # Keep existing value
        return result
    
    # Check if non-material change (cosmetic/layout)
    if change_type in (ChangeType.COSMETIC_CHANGE, ChangeType.LAYOUT_CHANGE):
        result["status"] = VerificationStatus.RECHECK_PASSED.value
        result["action_taken"] = "cosmetic_change_ignored"
        result["last_verified_preserved"] = False
        result["new_value"] = claim.get("value")
        return result
    
    # Material change — apply tier logic
    if tier == UpdateTier.TIER_1:
        # Auto-update: update claim value and advance dates
        result["status"] = VerificationStatus.VERIFIED_CURRENT.value
        result["action_taken"] = "tier_1_auto_update"
        result["last_verified_preserved"] = False
        result["new_value"] = _extract_new_claim_value(claim, new_fields)
    elif tier == UpdateTier.TIER_2:
        # Approval required: mark for review, preserve last verified
        result["status"] = VerificationStatus.REVIEW_REQUIRED.value
        result["action_taken"] = "tier_2_approval_required"
        result["last_verified_preserved"] = True
        result["new_value"] = _extract_new_claim_value(claim, new_fields)
    else:
        # TIER_3: manual review, preserve everything
        result["status"] = VerificationStatus.REVIEW_REQUIRED.value
        result["action_taken"] = "tier_3_manual_review"
        result["last_verified_preserved"] = True
        result["new_value"] = _extract_new_claim_value(claim, new_fields)
    
    return result


def _claim_type_to_source_role(claim_type: str) -> Optional[str]:
    """Map claim type to source role for extractor selection."""
    mapping = {
        "pricing": "PRICING",
        "free_plan": "PRICING",
        "trial": "PRICING",
        "billing": "PRICING",
        "capability": "PRODUCT_FEATURES",
        "feature": "PRODUCT_FEATURES",
        "limitation": "PRODUCT_FEATURES",
        "platform": "PRODUCT_FEATURES",
        "integration": "PRODUCT_FEATURES",
    }
    return mapping.get(claim_type)


def _get_source_from_ledger(source_id: str) -> Optional[dict]:
    """Look up a source by ID from the ledger."""
    if not LEDGER_PATH.is_file():
        return None
    try:
        ledger = load_json(LEDGER_PATH)
        for s in ledger.get("sources", []):
            if s.get("source_id") == source_id:
                return s
    except Exception:
        pass
    return None


def _extract_new_claim_value(claim: dict, new_fields: dict) -> Any:
    """Extract a new claim value from the extracted fields, preserving the claim's value structure.
    
    For pricing claims, builds a value dict matching the existing claim structure.
    For other types, returns the relevant extracted field.
    """
    claim_type = claim.get("claim_type", "")
    old_value = claim.get("value")
    
    if claim_type == "pricing":
        pricing = new_fields.get("pricing", {})
        tiers = pricing.get("detected_prices", [])
        if tiers:
            # Build a value dict matching the existing structure
            new_value = {"currency": pricing.get("currency", "USD"), "plans": []}
            for tier in tiers:
                plan = {
                    "name": tier.get("plan", "Unknown"),
                    "displayed_monthly_usd": tier.get("amount", tier.get("price")),
                }
                if tier.get("billing_basis") == "annual_billing_monthly_equivalent":
                    plan["billing_basis"] = "annual_billing_monthly_equivalent"
                new_value["plans"].append(plan)
            return new_value
        return old_value  # Preserve old if no new prices found
    elif claim_type == "free_plan":
        free = new_fields.get("free_plan")
        if free is True:
            return "Free plan available"
        elif free is False:
            return "No free plan"
        return old_value
    elif claim_type == "trial":
        trial = new_fields.get("trial")
        if trial:
            return trial
        return old_value
    elif claim_type in ("capability", "feature"):
        caps = new_fields.get("capabilities", [])
        if caps:
            return caps
        return old_value
    elif claim_type == "limitation":
        limits = new_fields.get("limitations", [])
        if limits:
            return limits
        return old_value
    elif claim_type == "platform":
        platforms = new_fields.get("platforms", [])
        if platforms:
            return platforms
        return old_value
    
    return old_value


def _apply_pipeline_results_to_ledger(
    ledger: dict,
    pipeline_results: List[dict],
    as_of: date,
    policy: dict,
) -> dict:
    """Apply pipeline results to the ledger, updating claims based on tier decisions.
    
    Args:
        ledger: The evidence ledger dict
        pipeline_results: List of pipeline result dicts from _run_pipeline_for_claim
        as_of: Current date
        policy: Freshness policy
    
    Returns:
        Stats dict with counts of updated, preserved, review_required, etc.
    """
    stats = {
        "updated": 0,
        "recheck_passed": 0,
        "preserved": 0,
        "review_required": 0,
        "source_unavailable": 0,
        "parser_failure": 0,
    }
    
    claims = ledger.get("claims", [])
    today_str = as_of.isoformat()
    
    for pr in pipeline_results:
        claim_id = pr.get("claim_id", "")
        status = pr.get("status", "")
        
        # Find the claim in the ledger
        claim = None
        for c in claims:
            if c.get("claim_id") == claim_id:
                claim = c
                break
        if not claim:
            continue
        
        claim_type = claim.get("claim_type", "general")
        threshold = get_threshold_for_claim(claim_type, policy)
        
        if status == VerificationStatus.RECHECK_PASSED.value:
            # Recheck passed — advance dates
            claim["verified_at"] = today_str
            claim["last_verified_date"] = today_str
            claim["stale_after"] = (as_of + timedelta(days=threshold)).isoformat()
            claim["status"] = "verified"
            claim["last_check_result"] = pr.get("action_taken", "recheck_passed")
            stats["recheck_passed"] += 1
        
        elif status == VerificationStatus.VERIFIED_CURRENT.value:
            # Auto-update (TIER_1) — update value and advance dates
            new_value = pr.get("new_value")
            if new_value is not None:
                claim["value"] = new_value
            claim["verified_at"] = today_str
            claim["last_verified_date"] = today_str
            claim["stale_after"] = (as_of + timedelta(days=threshold)).isoformat()
            claim["status"] = "verified"
            claim["last_check_result"] = pr.get("action_taken", "auto_updated")
            if pr.get("change_type"):
                claim["last_change_type"] = pr["change_type"]
            stats["updated"] += 1
        
        elif status == VerificationStatus.REVIEW_REQUIRED.value:
            # Review required — preserve last verified, mark for review
            claim["status"] = "needs_review"
            claim["last_check_result"] = pr.get("action_taken", "review_required")
            if pr.get("anomalies"):
                claim["anomalies_detected"] = pr["anomalies"]
            if pr.get("new_value") is not None and pr.get("new_value") != claim.get("value"):
                claim["pending_new_value"] = pr["new_value"]
            if pr.get("change_type"):
                claim["last_change_type"] = pr["change_type"]
            # Do NOT advance verified_at or last_verified_date
            stats["review_required"] += 1
        
        elif status == VerificationStatus.SOURCE_UNAVAILABLE.value:
            # Source unavailable — preserve everything
            claim["last_check_result"] = "source_unavailable"
            # Do NOT advance dates
            stats["source_unavailable"] += 1
        
        elif status == VerificationStatus.PARSER_FAILURE.value:
            # Parser failure — preserve everything
            claim["last_check_result"] = pr.get("action_taken", "parser_failure")
            # Do NOT advance dates
            stats["parser_failure"] += 1
        
        else:
            stats["preserved"] += 1
    
    return stats


def monitor_claims(
    as_of: Optional[date] = None,
    fetch_sources: bool = False,
    tool_filter: Optional[str] = None,
    report_only: bool = False,
) -> dict:
    """Run the source monitor pipeline.
    
    Args:
        as_of: Date to check against (defaults to today)
        fetch_sources: Whether to actually fetch official sources
        tool_filter: Optional tool_id to monitor only one tool
        report_only: Generate report without modifying any data
    
    Returns:
        Report dict with monitoring results
    """
    as_of = as_of or date.today()
    if isinstance(as_of, str):
        as_of = date.fromisoformat(as_of)
    
    policy = load_freshness_policy()
    ledger = load_json(LEDGER_PATH) if LEDGER_PATH.is_file() else {"sources": [], "claims": []}
    
    claims = ledger.get("claims", [])
    sources = {s.get("source_id"): s for s in ledger.get("sources", [])}
    
    production_ids = get_production_tool_ids()
    expansion_ids = get_expansion_only_ids()
    
    # Filter claims to production-only scope
    if tool_filter:
        filtered_claims = [c for c in claims if c.get("tool_id") == tool_filter]
    else:
        filtered_claims = [c for c in claims if c.get("tool_id") in production_ids]
    
    # Source fetch results
    source_fetch_results = {}
    if fetch_sources:
        try:
            from source_fetcher import SourceFetcher
            fetcher = SourceFetcher()
            # Fetch sources for tools with claims
            tools_to_fetch = set()
            for claim in filtered_claims:
                tid = claim.get("tool_id", "")
                if tid in production_ids and tid not in expansion_ids:
                    tools_to_fetch.add(tid)
            
            for tool_id in tools_to_fetch:
                result = fetcher.fetch_tool_sources(tool_id)
                source_fetch_results[tool_id] = result
        except ImportError:
            print("Warning: source_fetcher.py not available — skipping actual fetch")
        except Exception as e:
            print(f"Warning: source fetch failed: {e}")
    
    # Pipeline results from fetch→extract→update chain
    pipeline_results = []
    ledger_stats = None
    if fetch_sources and source_fetch_results:
        # Load source registry for source role lookups
        source_registry = {}
        if SOURCE_REGISTRY_PATH.is_file():
            source_registry = load_json(SOURCE_REGISTRY_PATH)
        
        # For each tool that was fetched, run pipeline on its claims
        for tool_id, fetch_result in source_fetch_results.items():
            tool_claims = [c for c in filtered_claims if c.get("tool_id") == tool_id]
            for claim in tool_claims:
                pr = _run_pipeline_for_claim(claim, fetch_result, source_registry, as_of)
                pipeline_results.append(pr)
        
        # Apply pipeline results to ledger (unless report_only)
        ledger_stats = None
        if not report_only and pipeline_results:
            ledger_stats = _apply_pipeline_results_to_ledger(
                ledger, pipeline_results, as_of, policy
            )
            # Save updated ledger
            save_json(LEDGER_PATH, ledger)
            # Reload claims for classification below
            claims = ledger.get("claims", [])
    
    # Classify all claims with proper semantics
    classified = []
    status_counts = {s.value: 0 for s in VerificationStatus}
    
    for claim in filtered_claims:
        status, urgency = classify_claim_with_semantics(claim, policy, as_of, source_fetch_results)
        status_counts[status.value] = status_counts.get(status.value, 0) + 1
        classified.append({
            "claim_id": claim.get("claim_id"),
            "tool_id": claim.get("tool_id"),
            "claim_type": claim.get("claim_type"),
            "status": status.value,
            "urgency_days": urgency,
            "stale_after": claim.get("stale_after"),
            "verified_at": claim.get("verified_at"),
            "last_verified_date": claim.get("last_verified_date"),
        })
    
    # Identify claims that need actual source fetching
    due_for_recheck = [c for c in classified if c["status"] == VerificationStatus.DUE_FOR_RECHECK.value]
    change_detected = [c for c in classified if c["status"] == VerificationStatus.CHANGE_DETECTED.value]
    source_unavailable = [c for c in classified if c["status"] == VerificationStatus.SOURCE_UNAVAILABLE.value]
    
    # Check for expansion-only leakage
    expansion_leaks = []
    for claim in claims:
        tid = claim.get("tool_id", "")
        if tid in expansion_ids and tid not in production_ids:
            expansion_leaks.append({
                "claim_id": claim.get("claim_id"),
                "tool_id": tid,
                "issue": "expansion-only tool in evidence ledger",
            })
    
    # Build report
    report = {
        "pipeline": "source_monitor",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "as_of": as_of.isoformat(),
        "mode": "fetch" if fetch_sources else "metadata_only",
        "summary": {
            "total_claims_monitored": len(filtered_claims),
            "total_production_tools": len(production_ids),
            "expansion_only_tools": len(expansion_ids),
            "status_counts": status_counts,
            "due_for_recheck": len(due_for_recheck),
            "change_detected": len(change_detected),
            "source_unavailable": len(source_unavailable),
            "expansion_leaks_found": len(expansion_leaks),
            "sources_actually_fetched": len(source_fetch_results),
            "report_only": report_only,
            "pipeline_results_count": len(pipeline_results),
            "ledger_stats": ledger_stats,
        },
        "classified_claims": classified,
        "due_for_recheck_claims": due_for_recheck,
        "expansion_leaks": expansion_leaks,
        "source_fetch_results": source_fetch_results if fetch_sources else {},
        "pipeline_results": pipeline_results if fetch_sources else [],
    }
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Source monitor — true fact verification")
    parser.add_argument("--as-of", type=str, default=None, help="Date to check (YYYY-MM-DD)")
    parser.add_argument("--fetch", action="store_true", help="Actually fetch official sources")
    parser.add_argument("--tool", type=str, default=None, help="Monitor only a specific tool")
    parser.add_argument("--report-only", action="store_true", help="Generate report without changes")
    parser.add_argument("--output", type=Path, default=None, help="Output report path")
    args = parser.parse_args()
    
    report = monitor_claims(
        as_of=args.as_of,
        fetch_sources=args.fetch,
        tool_filter=args.tool,
        report_only=args.report_only,
    )
    
    # Save report
    output_path = args.output or REPORTS_DIR / "source-monitor-report.json"
    save_json(output_path, report)
    
    # Print summary
    summary = report["summary"]
    mode = "FETCH" if summary.get("sources_actually_fetched", 0) > 0 else "METADATA_ONLY"
    print(f"\n{'='*60}")
    print(f"Source Monitor — {mode}")
    print(f"{'='*60}")
    print(f"  As of: {report['as_of']}")
    print(f"  Claims monitored: {summary['total_claims_monitored']}")
    print(f"  Production tools: {summary['total_production_tools']}")
    print(f"  Expansion-only tools: {summary['expansion_only_tools']}")
    print(f"\n  Status breakdown:")
    for status, count in summary["status_counts"].items():
        if count > 0:
            print(f"    {status}: {count}")
    print(f"\n  Due for recheck: {summary['due_for_recheck']}")
    print(f"  Change detected: {summary['change_detected']}")
    print(f"  Source unavailable: {summary['source_unavailable']}")
    print(f"  Expansion leaks: {summary['expansion_leaks_found']}")
    print(f"\nReport written to {output_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
