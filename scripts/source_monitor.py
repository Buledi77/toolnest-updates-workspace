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
    
    # Classify all claims with proper semantics
    classified = []
    status_counts = {s.value: 0 for s in VerificationStatus}
    
    # Source fetch results (placeholder — actual fetching done by source_fetcher.py)
    source_fetch_results = {}
    if fetch_sources:
        # Import source_fetcher only when needed to avoid circular deps
        try:
            from source_fetcher import SourceFetcher
            fetcher = SourceFetcher()
            # Fetch sources for tools with due-for-recheck claims
            tools_to_fetch = set()
            for claim in filtered_claims:
                tid = claim.get("tool_id", "")
                if tid in production_ids:
                    tools_to_fetch.add(tid)
            
            for tool_id in tools_to_fetch:
                result = fetcher.fetch_tool_sources(tool_id)
                source_fetch_results[tool_id] = result
        except ImportError:
            print("Warning: source_fetcher.py not available — skipping actual fetch")
        except Exception as e:
            print(f"Warning: source fetch failed: {e}")
    
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
        },
        "classified_claims": classified,
        "due_for_recheck_claims": due_for_recheck,
        "expansion_leaks": expansion_leaks,
        "source_fetch_results": source_fetch_results if fetch_sources else {},
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
