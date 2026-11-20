#!/usr/bin/env python3
"""
Change/Correction Integration — connects change history, stale facts, disputed claims,
and correction registry into one deterministic internal trust/readiness summary.

Does not invent corrections or historical changes.
Public corrections page remains honest even when correction registry is empty.

Sources integrated:
  - data/changes/tool-change-ledger.json (change history)
  - data/evidence/evidence-ledger.json (claims with stale/disputed status)
  - reports/ (stale facts report, disputed claims report)
  - corrections.html (public corrections page)

Output:
  - data/trust-summary.json (internal trust/readiness summary)

Usage:
  python3 scripts/build_trust_summary.py
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGE_LEDGER = ROOT / "data" / "changes" / "tool-change-ledger.json"
EVIDENCE_LEDGER = ROOT / "data" / "evidence" / "evidence-ledger.json"
CORRECTIONS_PAGE = ROOT / "corrections.html"
REPORTS_DIR = ROOT / "reports"
OUTPUT = ROOT / "data" / "trust-summary.json"


def load_json_safe(path: Path) -> dict | list:
    """Load JSON file safely, returning empty dict/list on failure."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def load_change_events() -> list:
    """Load change events from the change ledger."""
    data = load_json_safe(CHANGE_LEDGER)
    if isinstance(data, dict):
        return data.get("events", [])
    return []


def load_evidence_claims() -> list:
    """Load claims from the evidence ledger."""
    data = load_json_safe(EVIDENCE_LEDGER)
    if isinstance(data, dict):
        return data.get("claims", [])
    return []


def load_evidence_sources() -> list:
    """Load sources from the evidence ledger."""
    data = load_json_safe(EVIDENCE_LEDGER)
    if isinstance(data, dict):
        return data.get("sources", [])
    return []


def find_stale_claims(claims: list, as_of: date | None = None) -> list:
    """Find claims that are stale or need review."""
    as_of = as_of or date.today()
    stale = []
    for claim in claims:
        status = claim.get("status", "verified")
        stale_after = claim.get("stale_after", "")

        # Check explicit status
        if status in ("stale", "needs_review", "disputed"):
            stale.append({
                "claim_id": claim.get("claim_id"),
                "tool_id": claim.get("tool_id"),
                "status": status,
                "reason": f"status is '{status}'",
                "stale_after": stale_after,
            })
        elif stale_after:
            try:
                stale_date = date.fromisoformat(stale_after)
                if stale_date < as_of:
                    stale.append({
                        "claim_id": claim.get("claim_id"),
                        "tool_id": claim.get("tool_id"),
                        "status": "expired",
                        "reason": f"stale_after ({stale_after}) has passed",
                        "stale_after": stale_after,
                    })
            except ValueError:
                pass

    return stale


def find_disputed_claims(claims: list) -> list:
    """Find claims that are disputed."""
    disputed = []
    for claim in claims:
        if claim.get("status") == "disputed":
            disputed.append({
                "claim_id": claim.get("claim_id"),
                "tool_id": claim.get("tool_id"),
                "disputed_by": claim.get("disputed_by"),
                "note": claim.get("note", ""),
            })
    return disputed


def summarize_change_events(events: list) -> dict:
    """Summarize change events by type and tool."""
    by_type: dict[str, int] = {}
    by_tool: dict[str, int] = {}
    recent = []

    for event in events:
        event_type = event.get("event_type", "unknown")
        tool_id = event.get("tool_id", "unknown")
        detected = event.get("detected_at", "")

        by_type[event_type] = by_type.get(event_type, 0) + 1
        by_tool[tool_id] = by_tool.get(tool_id, 0) + 1

        # Track recent events (last 30 days)
        if detected:
            try:
                event_date = date.fromisoformat(detected)
                days_ago = (date.today() - event_date).days
                if days_ago <= 30:
                    recent.append({
                        "event_id": event.get("event_id"),
                        "tool_id": tool_id,
                        "type": event_type,
                        "detected_at": detected,
                        "days_ago": days_ago,
                    })
            except ValueError:
                pass

    return {
        "total_events": len(events),
        "by_type": by_type,
        "by_tool": by_tool,
        "recent_30_days": len(recent),
        "recent_events": recent,
    }


def check_corrections_page() -> dict:
    """Check that the corrections page exists and is honest."""
    result = {
        "exists": False,
        "has_workflow": False,
        "has_evidence_standards": False,
        "has_submission_info": False,
    }

    if not CORRECTIONS_PAGE.exists():
        return result

    result["exists"] = True
    try:
        content = CORRECTIONS_PAGE.read_text(encoding="utf-8").lower()
        result["has_workflow"] = "correction workflow" in content or "workflow" in content
        result["has_evidence_standards"] = "evidence" in content and "standard" in content
        result["has_submission_info"] = "submit" in content or "contact" in content or "email" in content
    except OSError:
        pass

    return result


def build_trust_summary() -> dict:
    """Build the complete trust/readiness summary."""
    change_events = load_change_events()
    claims = load_evidence_claims()
    sources = load_evidence_sources()

    stale_claims = find_stale_claims(claims)
    disputed_claims = find_disputed_claims(claims)
    change_summary = summarize_change_events(change_events)
    corrections_check = check_corrections_page()

    # Calculate overall trust score
    total_claims = len(claims)
    healthy_claims = total_claims - len(stale_claims) - len(disputed_claims)
    trust_score = (healthy_claims / total_claims * 100) if total_claims > 0 else 100

    # Tools with issues
    tools_with_stale = list({claim["tool_id"] for claim in stale_claims})
    tools_with_disputed = list({claim["tool_id"] for claim in disputed_claims})
    tools_with_changes = list(change_summary["by_tool"].keys())

    summary = {
        "schema_version": "trust-summary-v1",
        "generated_at": date.today().isoformat(),
        "trust_score": round(trust_score, 1),
        "claims": {
            "total": total_claims,
            "healthy": healthy_claims,
            "stale": len(stale_claims),
            "disputed": len(disputed_claims),
            "stale_claims": stale_claims,
            "disputed_claims": disputed_claims,
        },
        "changes": change_summary,
        "corrections_page": corrections_check,
        "tools_with_issues": {
            "stale_claims": sorted(tools_with_stale),
            "disputed_claims": sorted(tools_with_disputed),
            "recent_changes": sorted(tools_with_changes),
        },
        "sources": {
            "total": len(sources),
        },
        "readiness": {
            "corrections_page_exists": corrections_check["exists"],
            "corrections_page_complete": all([
                corrections_check["has_workflow"],
                corrections_check["has_evidence_standards"],
                corrections_check["has_submission_info"],
            ]),
            "change_ledger_active": len(change_events) > 0,
            "evidence_ledger_active": len(claims) > 0,
        },
    }

    return summary


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Build Trust Summary from change/correction data"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT,
        help="Output path for trust summary JSON",
    )
    args = parser.parse_args()

    summary = build_trust_summary()

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    # Print summary
    print(f"Trust Summary:")
    print(f"  Trust score: {summary['trust_score']}%")
    print(f"  Claims: {summary['claims']['total']} total, "
          f"{summary['claims']['healthy']} healthy, "
          f"{summary['claims']['stale']} stale, "
          f"{summary['claims']['disputed']} disputed")
    print(f"  Change events: {summary['changes']['total_events']} total, "
          f"{summary['changes']['recent_30_days']} in last 30 days")
    print(f"  Corrections page: {'complete' if summary['readiness']['corrections_page_complete'] else 'incomplete'}")
    print(f"  Tools with stale claims: {summary['tools_with_issues']['stale_claims']}")
    print(f"  Tools with disputed claims: {summary['tools_with_issues']['disputed_claims']}")
    print(f"\nWritten to {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
