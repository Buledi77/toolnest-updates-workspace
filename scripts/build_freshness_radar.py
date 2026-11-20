#!/usr/bin/env python3
"""
Freshness Radar Foundation — Phase B

Deterministic, machine-readable freshness report from existing evidence fields.

Keeps these concepts strictly separate:
1. Editorial review
2. Commercial facts checked
3. Hands-on tested

Creates states only when data supports them:
- current
- approaching_stale
- stale
- disputed
- missing_evidence
- not_applicable

Uses existing verified_at, accessed_at, stale_after, pricingCheckedOn, testedOn
or equivalent fields.

Output: docs/internal/FRESHNESS-RADAR.json
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path


# Reference date for freshness calculations
REFERENCE_DATE = datetime(2026, 11, 20)

# Staleness thresholds (in days)
EDITORIAL_STALE_THRESHOLD = 90
EDITORIAL_APPROACHING_STALE = 60
COMMERCIAL_STALE_THRESHOLD = 30
COMMERCIAL_APPROACHING_STALE = 20
HANDS_ON_STALE_THRESHOLD = 60
HANDS_ON_APPROACHING_STALE = 45


def load_json(path):
    """Load a JSON file and return its contents."""
    with open(path) as f:
        return json.load(f)


def parse_date(date_str):
    """Parse a date string in various formats."""
    if not date_str:
        return None
    # Try ISO format
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return None


def days_since(date_str):
    """Calculate days since a date string."""
    dt = parse_date(date_str)
    if dt is None:
        return None
    return (REFERENCE_DATE - dt).days


def freshness_state(days_ago, stale_threshold, approaching_threshold):
    """Determine freshness state based on days since last check."""
    if days_ago is None:
        return "missing_evidence"
    if days_ago <= approaching_threshold:
        return "current"
    if days_ago <= stale_threshold:
        return "approaching_stale"
    return "stale"


def get_html_date(filepath):
    """Extract the most recent date from an HTML file's content."""
    if not os.path.exists(filepath):
        return None
    with open(filepath) as f:
        content = f.read()
    # Look for dates near freshness-related keywords
    dates = re.findall(
        r'(?:last reviewed|reviewed|checked|updated|verified|pricing checked|commercial facts)[^<>]*?(\d{4}[-/]\d{2}[-/]\d{2})',
        content, re.IGNORECASE
    )
    if dates:
        return dates[-1]  # Most recent
    # Fallback: any YYYY-MM-DD pattern
    all_dates = re.findall(r'\d{4}-\d{2}-\d{2}', content)
    if all_dates:
        return all_dates[-1]
    return None


def get_tools_v2_freshness(tool_id):
    """Get freshness data from tools-v2 record."""
    v2_path = f"data/tools-v2/{tool_id}.json"
    if not os.path.exists(v2_path):
        return None
    record = load_json(v2_path)
    return {
        "freshness": record.get("freshness", {}),
        "editorial": record.get("editorial", {}),
        "evidence": record.get("evidence", {}),
        "factual_profile": record.get("factual_profile", {}),
        "monetization": record.get("monetization", {})
    }


def get_evidence_ledger_data(tool_id):
    """Get evidence ledger claims and sources for a tool."""
    ledger = load_json("data/evidence/evidence-ledger.json")
    claims = [c for c in ledger.get("claims", []) if c.get("tool_id") == tool_id]
    source_ids = set()
    for c in claims:
        for sid in c.get("source_ids", []):
            source_ids.add(sid)
    sources = [s for s in ledger.get("sources", []) if s.get("source_id") in source_ids]
    # Check for disputes
    disputes = [d for d in ledger.get("disputes", []) if d.get("claim_id") in
                {c.get("claim_id") for c in claims}]
    return claims, sources, disputes


def get_review_data(tool_id):
    """Check for review data in data/reviews/."""
    review_path = f"data/reviews/{tool_id}.json"
    if os.path.exists(review_path):
        return load_json(review_path)
    return None


def analyze_editorial_freshness(tool_id, v2_data, html_date):
    """Analyze editorial review freshness."""
    result = {
        "status": "missing_evidence",
        "last_reviewed": None,
        "days_since_review": None,
        "next_review_due": None,
        "source": None
    }

    # Check tools-v2 editorial data
    if v2_data:
        editorial = v2_data.get("editorial", {})
        if editorial.get("editorial_last_reviewed"):
            date_str = editorial["editorial_last_reviewed"]
            result["last_reviewed"] = date_str
            result["days_since_review"] = days_since(date_str)
            result["status"] = freshness_state(
                result["days_since_review"],
                EDITORIAL_STALE_THRESHOLD,
                EDITORIAL_APPROACHING_STALE
            )
            result["source"] = "tools-v2:editorial.editorial_last_reviewed"

        freshness = v2_data.get("freshness", {})
        if freshness.get("next_review_at"):
            result["next_review_due"] = freshness["next_review_at"]

    # Fallback: HTML date
    if result["status"] == "missing_evidence" and html_date:
        result["last_reviewed"] = html_date
        result["days_since_review"] = days_since(html_date)
        result["status"] = freshness_state(
            result["days_since_review"],
            EDITORIAL_STALE_THRESHOLD,
            EDITORIAL_APPROACHING_STALE
        )
        result["source"] = "html:embedded_date"

    return result


def analyze_commercial_facts_freshness(tool_id, v2_data, ledger_data):
    """Analyze commercial facts checked freshness."""
    result = {
        "status": "missing_evidence",
        "last_checked": None,
        "days_since_check": None,
        "stale_after": None,
        "source": None,
        "pricing_sources": [],
        "claim_count": 0
    }

    claims, sources, disputes = ledger_data

    # Check for disputes
    if disputes:
        result["status"] = "disputed"
        result["disputed_claims"] = [d.get("claim_id") for d in disputes]

    # Check evidence ledger for pricing/commercial claims
    if claims and result["status"] != "disputed":
        pricing_claims = [c for c in claims if c.get("claim_type") in
                          ("pricing", "billing", "feature", "limitation")]
        if pricing_claims:
            # Get most recent verified_at
            verified_dates = [c.get("verified_at") for c in pricing_claims
                             if c.get("verified_at")]
            if verified_dates:
                latest = max(verified_dates)
                result["last_checked"] = latest
                result["days_since_check"] = days_since(latest)
                result["status"] = freshness_state(
                    result["days_since_check"],
                    COMMERCIAL_STALE_THRESHOLD,
                    COMMERCIAL_APPROACHING_STALE
                )
                result["source"] = "evidence-ledger:claims.verified_at"
                result["claim_count"] = len(pricing_claims)

            # Get stale_after
            stale_dates = [c.get("stale_after") for c in pricing_claims
                          if c.get("stale_after")]
            if stale_dates:
                result["stale_after"] = min(stale_dates)

        # Collect pricing sources
        for src in sources:
            if src.get("source_type") == "official_pricing":
                result["pricing_sources"].append({
                    "source_id": src.get("source_id"),
                    "url": src.get("url"),
                    "verified_at": src.get("verified_at")
                })

    # Check tools-v2 monetization
    if v2_data and result["status"] == "missing_evidence":
        monetization = v2_data.get("monetization", {})
        if monetization.get("last_link_check"):
            result["last_checked"] = monetization["last_link_check"]
            result["days_since_check"] = days_since(monetization["last_link_check"])
            result["status"] = freshness_state(
                result["days_since_check"],
                COMMERCIAL_STALE_THRESHOLD,
                COMMERCIAL_APPROACHING_STALE
            )
            result["source"] = "tools-v2:monetization.last_link_check"

    return result


def analyze_hands_on_freshness(tool_id, v2_data, review_data):
    """Analyze hands-on testing freshness."""
    result = {
        "status": "not_applicable",
        "last_tested": None,
        "days_since_test": None,
        "plan_tested": None,
        "test_tasks": 0,
        "source": None
    }

    # Check review data
    if review_data:
        if review_data.get("testStatus") == "tested":
            result["status"] = "current"  # Will be updated below
            if review_data.get("testedOn"):
                result["last_tested"] = review_data["testedOn"]
                result["days_since_test"] = days_since(review_data["testedOn"])
                result["status"] = freshness_state(
                    result["days_since_test"],
                    HANDS_ON_STALE_THRESHOLD,
                    HANDS_ON_APPROACHING_STALE
                )
                result["source"] = "data/reviews:testedOn"
            if review_data.get("planTested"):
                result["plan_tested"] = review_data["planTested"]
            if review_data.get("testTasks"):
                result["test_tasks"] = len(review_data["testTasks"])

    # Check tools-v2 for any hands-on indicators
    if v2_data:
        editorial = v2_data.get("editorial", {})
        # tools-v2 doesn't directly track hands-on, but review_status might indicate it
        if editorial.get("review_status") == "tested":
            if not result["last_tested"]:
                result["status"] = "missing_evidence"
                result["source"] = "tools-v2:editorial.review_status (no date)"

    # If no review data and no hands-on indicators, it's not_applicable
    if not review_data and not v2_data:
        result["status"] = "not_applicable"
    elif not review_data and v2_data:
        # Has v2 but no review data — check if there's any indication of testing
        editorial = v2_data.get("editorial", {})
        if editorial.get("review_status") not in ("tested",):
            result["status"] = "not_applicable"

    return result


def build_freshness_radar():
    """Build the freshness radar for all pages."""
    quality_report = load_json("docs/internal/QUALITY-REPORT.json")

    radar = {
        "schema_version": "freshness-radar-v1",
        "generated_at": "2026-11-20",
        "reference_date": "2026-11-20",
        "description": "Deterministic freshness report from existing evidence fields. "
                       "Keeps editorial review, commercial facts checked, and hands-on tested strictly separate. "
                       "States: current, approaching_stale, stale, disputed, missing_evidence, not_applicable.",
        "staleness_thresholds": {
            "editorial_review": {
                "current": f"≤{EDITORIAL_APPROACHING_STALE} days",
                "approaching_stale": f"{EDITORIAL_APPROACHING_STALE + 1}-{EDITORIAL_STALE_THRESHOLD} days",
                "stale": f">{EDITORIAL_STALE_THRESHOLD} days"
            },
            "commercial_facts": {
                "current": f"≤{COMMERCIAL_APPROACHING_STALE} days",
                "approaching_stale": f"{COMMERCIAL_APPROACHING_STALE + 1}-{COMMERCIAL_STALE_THRESHOLD} days",
                "stale": f">{COMMERCIAL_STALE_THRESHOLD} days"
            },
            "hands_on_tested": {
                "current": f"≤{HANDS_ON_APPROACHING_STALE} days",
                "approaching_stale": f"{HANDS_ON_APPROACHING_STALE + 1}-{HANDS_ON_STALE_THRESHOLD} days",
                "stale": f">{HANDS_ON_STALE_THRESHOLD} days"
            }
        },
        "pages": []
    }

    # Process all pages from quality report
    for page in quality_report["pages"]:
        path = page["path"]
        page_type = page["type"]

        # Extract tool_id or slug
        if page_type == "tool_review":
            tool_id = path.split("/")[-1].replace(".html", "")
            html_path = f"tools/{tool_id}.html"
        elif page_type == "compare":
            tool_id = path.split("/")[-1].replace(".html", "")
            html_path = f"compare/{tool_id}.html"
        elif page_type == "alternatives":
            tool_id = path.split("/")[-1].replace(".html", "")
            html_path = f"alternatives/{tool_id}.html"
        elif page_type == "best":
            tool_id = path.split("/")[-1].replace(".html", "")
            html_path = f"best/{tool_id}.html"
        elif page_type == "category":
            tool_id = path.split("/")[-1].replace(".html", "")
            html_path = f"categories/{tool_id}.html" if "categories" in path else f"category/{tool_id}.html"
        else:
            continue

        # Get data sources
        v2_data = get_tools_v2_freshness(tool_id)
        claims, sources, disputes = get_evidence_ledger_data(tool_id)
        ledger_data = (claims, sources, disputes)
        review_data = get_review_data(tool_id)
        html_date = get_html_date(html_path)

        # Analyze freshness dimensions
        editorial = analyze_editorial_freshness(tool_id, v2_data, html_date)
        commercial = analyze_commercial_facts_freshness(tool_id, v2_data, ledger_data)
        hands_on = analyze_hands_on_freshness(tool_id, v2_data, review_data)

        # Determine overall freshness status (most restrictive)
        status_priority = {
            "disputed": 0,
            "stale": 1,
            "missing_evidence": 2,
            "approaching_stale": 3,
            "current": 4,
            "not_applicable": 5
        }
        statuses = [editorial["status"], commercial["status"], hands_on["status"]]
        # Filter out not_applicable for overall status
        relevant = [s for s in statuses if s != "not_applicable"]
        if not relevant:
            overall = "not_applicable"
        else:
            overall = min(relevant, key=lambda s: status_priority.get(s, 99))

        page_record = {
            "path": path,
            "type": page_type,
            "grade": page.get("grade", "unknown"),
            "editorial_review": editorial,
            "commercial_facts_checked": commercial,
            "hands_on_tested": hands_on,
            "overall_freshness": overall,
            "data_sources": {
                "has_tools_v2": v2_data is not None,
                "has_evidence_ledger": len(claims) > 0,
                "has_review_data": review_data is not None,
                "has_html_date": html_date is not None
            }
        }

        radar["pages"].append(page_record)

    # Add summary statistics
    editorial_counts = {}
    commercial_counts = {}
    hands_on_counts = {}
    overall_counts = {}

    for page in radar["pages"]:
        for dim, counts in [
            ("editorial_review", editorial_counts),
            ("commercial_facts_checked", commercial_counts),
            ("hands_on_tested", hands_on_counts)
        ]:
            status = page[dim]["status"]
            counts[status] = counts.get(status, 0) + 1

        status = page["overall_freshness"]
        overall_counts[status] = overall_counts.get(status, 0) + 1

    radar["summary"] = {
        "total_pages": len(radar["pages"]),
        "by_type": {},
        "editorial_review_distribution": editorial_counts,
        "commercial_facts_distribution": commercial_counts,
        "hands_on_tested_distribution": hands_on_counts,
        "overall_freshness_distribution": overall_counts,
        "pages_with_tools_v2": sum(1 for p in radar["pages"] if p["data_sources"]["has_tools_v2"]),
        "pages_with_evidence_ledger": sum(1 for p in radar["pages"] if p["data_sources"]["has_evidence_ledger"]),
        "pages_with_review_data": sum(1 for p in radar["pages"] if p["data_sources"]["has_review_data"]),
        "pages_with_html_date": sum(1 for p in radar["pages"] if p["data_sources"]["has_html_date"])
    }

    # Count by type
    type_counts = {}
    for page in radar["pages"]:
        t = page["type"]
        if t not in type_counts:
            type_counts[t] = 0
        type_counts[t] += 1
    radar["summary"]["by_type"] = type_counts

    return radar


def main():
    print("=== Building Freshness Radar ===\n")
    radar = build_freshness_radar()

    # Write output
    output_path = "docs/internal/FRESHNESS-RADAR.json"
    with open(output_path, "w") as f:
        json.dump(radar, f, indent=2)

    print(f"Output: {output_path}")
    print(f"Total pages: {radar['summary']['total_pages']}")
    print()

    # Print summary
    summary = radar["summary"]
    print("=== Summary ===")
    print(f"Pages with tools-v2: {summary['pages_with_tools_v2']}")
    print(f"Pages with evidence ledger: {summary['pages_with_evidence_ledger']}")
    print(f"Pages with review data: {summary['pages_with_review_data']}")
    print(f"Pages with HTML date: {summary['pages_with_html_date']}")
    print()

    print("=== Editorial Review Distribution ===")
    for status, count in sorted(summary["editorial_review_distribution"].items()):
        print(f"  {status}: {count}")
    print()

    print("=== Commercial Facts Distribution ===")
    for status, count in sorted(summary["commercial_facts_distribution"].items()):
        print(f"  {status}: {count}")
    print()

    print("=== Hands-on Tested Distribution ===")
    for status, count in sorted(summary["hands_on_tested_distribution"].items()):
        print(f"  {status}: {count}")
    print()

    print("=== Overall Freshness Distribution ===")
    for status, count in sorted(summary["overall_freshness_distribution"].items()):
        print(f"  {status}: {count}")
    print()

    # Print by type
    print("=== By Page Type ===")
    for ptype, count in sorted(summary["by_type"].items()):
        print(f"  {ptype}: {count}")
    print()

    # Show pages with issues
    print("=== Pages with Stale or Disputed Status ===")
    for page in radar["pages"]:
        if page["overall_freshness"] in ("stale", "disputed"):
            print(f"  {page['path']}: overall={page['overall_freshness']}, "
                  f"editorial={page['editorial_review']['status']}, "
                  f"commercial={page['commercial_facts_checked']['status']}, "
                  f"hands_on={page['hands_on_tested']['status']}")

    print(f"\n=== Radar written to {output_path} ===")


if __name__ == "__main__":
    main()
