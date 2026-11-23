#!/usr/bin/env python3
"""Data coverage report generator (Phase 3 Requirement B).

Scans every tools-v2 record for field coverage across all 147 authoritative tools
and outputs structured reports showing what data exists and what is missing.
Missing data is labelled "missing", "unknown", or "not collected" — never inferred.

Outputs:
- reports/phase3/data-coverage-report.json (machine-readable)
- reports/phase3/data-coverage-report.md (human-readable)
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL_DIR = ROOT / "data" / "tools-v2"
LEGACY_DATA_PATH = ROOT / "data" / "tools.json"
TOOLS_HTML_DIR = ROOT / "tools"
COMPARE_HTML_DIR = ROOT / "compare"
ALTERNATIVES_HTML_DIR = ROOT / "alternatives"
GOALS_HTML_DIR = ROOT / "goals"
REPORTS_DIR = ROOT / "reports" / "phase3"


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_catalog_tools():
    data = load_json(LEGACY_DATA_PATH)
    return data.get("tools", [])


def load_tools_v2_records():
    records = []
    for path in sorted(TOOL_DIR.rglob("*.json")):
        if path.name == "README.json":
            continue
        records.append(load_json(path))
    return records


def list_html_slugs(directory: Path) -> set:
    slugs = set()
    if not directory.is_dir():
        return slugs
    for html_file in directory.glob("*.html"):
        slugs.add(html_file.stem)
    return slugs


def field_status(record, *paths):
    """Check the status of a nested field in a record.

    Returns: "present", "empty", or "missing"
    - "present": field exists and has non-empty value
    - "empty": field exists but is empty (empty list, empty string, empty dict)
    - "missing": field does not exist
    """
    current = record
    for path_part in paths:
        if not isinstance(current, dict):
            return "missing"
        if path_part not in current:
            return "missing"
        current = current[path_part]

    # Check if the final value is empty
    if isinstance(current, (list, dict)) and len(current) == 0:
        return "empty"
    if isinstance(current, str) and current.strip() == "":
        return "empty"
    if current is None:
        return "missing"

    return "present"


def check_field_coverage(record):
    """Check coverage of all important fields in a tools-v2 record."""
    coverage = {}

    # Identity fields
    coverage["name"] = field_status(record, "identity", "name")
    coverage["slug"] = field_status(record, "identity", "slug")
    coverage["official_url"] = field_status(record, "identity", "official_url")
    coverage["logo"] = field_status(record, "identity", "logo")

    # Discovery fields
    coverage["category"] = field_status(record, "discovery", "categories")
    coverage["use_case_tags"] = field_status(record, "discovery", "use_cases")
    coverage["audiences"] = field_status(record, "discovery", "audiences")
    coverage["platforms"] = field_status(record, "discovery", "platforms")
    coverage["integrations"] = field_status(record, "discovery", "integrations")
    coverage["tags"] = field_status(record, "discovery", "tags")

    # Factual profile fields
    coverage["description"] = field_status(record, "factual_profile", "concise_summary")
    coverage["primary_purpose"] = field_status(record, "factual_profile", "primary_purpose")
    coverage["capabilities"] = field_status(record, "factual_profile", "capabilities")
    coverage["limitations"] = field_status(record, "factual_profile", "limitations")
    coverage["free_plan_status"] = field_status(record, "factual_profile", "free_plan_status")
    coverage["trial_status"] = field_status(record, "factual_profile", "trial_status")
    coverage["pricing_status"] = field_status(record, "factual_profile", "pricing_status")

    # Editorial fields
    coverage["editorial_tier"] = field_status(record, "editorial", "editorial_tier")
    coverage["best_for"] = field_status(record, "editorial", "best_for")
    coverage["not_recommended_for"] = field_status(record, "editorial", "not_recommended_for")
    coverage["editorial_summary"] = field_status(record, "editorial", "editorial_summary")
    coverage["review_status"] = field_status(record, "editorial", "review_status")

    # Relationship fields
    coverage["alternatives"] = field_status(record, "relationships", "alternatives")
    coverage["meaningful_comparisons"] = field_status(record, "relationships", "meaningful_comparisons")
    coverage["related_tools"] = field_status(record, "relationships", "related_tools")
    coverage["compatible_tools"] = field_status(record, "relationships", "compatible_tools")

    # Evidence fields
    coverage["evidence_claim_refs"] = field_status(record, "evidence", "claim_refs")
    coverage["evidence_source_ids"] = field_status(record, "evidence", "source_ids")
    coverage["evidence_confidence"] = field_status(record, "evidence", "confidence")
    coverage["evidence_hands_on"] = field_status(record, "evidence", "handsOn")

    # Monetization fields
    coverage["affiliate_url"] = field_status(record, "monetization", "affiliate_url")
    coverage["official_non_affiliate_url"] = field_status(record, "monetization", "official_non_affiliate_url")

    # Publishing fields
    coverage["indexability"] = field_status(record, "publishing", "indexability")
    coverage["canonical_url"] = field_status(record, "publishing", "canonical_url")
    coverage["sitemap_eligible"] = field_status(record, "publishing", "sitemap_eligible")

    # Freshness fields
    coverage["last_verified_at"] = field_status(record, "freshness", "last_verified_at")
    coverage["next_review_at"] = field_status(record, "freshness", "next_review_at")

    return coverage


def check_page_coverage(tool_id, tool_slug, html_slugs, compare_slugs, alt_slugs, goal_tools):
    """Check whether a tool has associated HTML pages."""
    page_coverage = {}
    page_coverage["profile_page"] = "present" if tool_slug in html_slugs else "missing"
    page_coverage["alternatives_page"] = "present" if f"{tool_slug}-alternatives" in alt_slugs else "missing"

    # Check if tool appears in any comparison
    in_comparison = False
    for comp_slug in compare_slugs:
        if tool_slug in comp_slug:
            in_comparison = True
            break
    page_coverage["comparison_coverage"] = "present" if in_comparison else "missing"

    # Check if tool appears in any goal page
    in_goal = tool_id in goal_tools
    page_coverage["goal_coverage"] = "present" if in_goal else "missing"

    return page_coverage


def compute_aggregate_coverage(per_tool_coverage):
    """Compute aggregate coverage percentages across all tools."""
    fields = set()
    for tool_id, coverage in per_tool_coverage.items():
        fields.update(coverage.keys())

    aggregate = {}
    for field in sorted(fields):
        present = sum(1 for c in per_tool_coverage.values() if c.get(field) == "present")
        empty = sum(1 for c in per_tool_coverage.values() if c.get(field) == "empty")
        missing = sum(1 for c in per_tool_coverage.values() if c.get(field) == "missing")
        total = len(per_tool_coverage)
        aggregate[field] = {
            "present": present,
            "empty": empty,
            "missing": missing,
            "total": total,
            "coverage_pct": round(present / total * 100, 1) if total else 0,
        }

    return aggregate


def generate_markdown_report(results):
    """Generate a human-readable Markdown report."""
    lines = []
    lines.append("# Data Coverage Report")
    lines.append("")
    lines.append(f"Generated: {results['timestamp']}")
    lines.append(f"Total tools analysed: {results['total_tools']}")
    lines.append("")

    # Aggregate summary
    lines.append("## Aggregate Coverage")
    lines.append("")
    lines.append("| Field | Present | Empty | Missing | Coverage % |")
    lines.append("|-------|---------|-------|---------|------------|")

    for field, stats in results["aggregate_coverage"].items():
        lines.append(
            f"| {field} | {stats['present']} | {stats['empty']} | {stats['missing']} | {stats['coverage_pct']}% |"
        )

    lines.append("")

    # Page coverage summary
    lines.append("## Page Coverage")
    lines.append("")
    page_agg = results.get("page_coverage_aggregate", {})
    if page_agg:
        lines.append("| Page Type | Present | Missing | Coverage % |")
        lines.append("|-----------|---------|---------|------------|")
        for field, stats in page_agg.items():
            lines.append(
                f"| {field} | {stats['present']} | {stats['missing']} | {stats.get('coverage_pct', 0)}% |"
            )
    lines.append("")

    # Tools with low coverage
    low_coverage_tools = []
    for tool_id, coverage in results["per_tool"].items():
        present_count = sum(1 for v in coverage["fields"].values() if v == "present")
        total_fields = len(coverage["fields"])
        pct = present_count / total_fields * 100 if total_fields else 0
        if pct < 50:
            low_coverage_tools.append((tool_id, present_count, total_fields, pct))

    if low_coverage_tools:
        lines.append("## Tools with Low Coverage (< 50%)")
        lines.append("")
        lines.append(f"{len(low_coverage_tools)} tools have less than 50% field coverage.")
        lines.append("")
        lines.append("| Tool ID | Present | Total | Coverage % |")
        lines.append("|---------|---------|-------|------------|")
        for tool_id, present, total, pct in sorted(low_coverage_tools, key=lambda x: x[3]):
            lines.append(f"| {tool_id} | {present} | {total} | {pct:.1f}% |")
        lines.append("")

    # Tools with complete coverage
    complete_tools = []
    for tool_id, coverage in results["per_tool"].items():
        present_count = sum(1 for v in coverage["fields"].values() if v == "present")
        total_fields = len(coverage["fields"])
        pct = present_count / total_fields * 100 if total_fields else 0
        if pct >= 80:
            complete_tools.append((tool_id, present_count, total_fields, pct))

    if complete_tools:
        lines.append("## Tools with High Coverage (>= 80%)")
        lines.append("")
        lines.append(f"{len(complete_tools)} tools have 80%+ field coverage.")
        lines.append("")
        lines.append("| Tool ID | Present | Total | Coverage % |")
        lines.append("|---------|---------|-------|------------|")
        for tool_id, present, total, pct in sorted(complete_tools, key=lambda x: -x[3]):
            lines.append(f"| {tool_id} | {present} | {total} | {pct:.1f}% |")
        lines.append("")

    lines.append("---")
    lines.append("*This report is generated automatically. Missing data is labelled as missing, empty, or not collected — never inferred.*")

    return "\n".join(lines)


def run_coverage_report():
    """Run the data coverage analysis and return structured results."""
    print("Loading data sources...")

    catalog_tools = load_catalog_tools()
    v2_records = load_tools_v2_records()

    # Build lookup maps
    v2_by_id = {r.get("identity", {}).get("id"): r for r in v2_records}
    catalog_ids = {t.get("id") for t in catalog_tools}

    # HTML slugs
    html_slugs = list_html_slugs(TOOLS_HTML_DIR)
    compare_slugs = list_html_slugs(COMPARE_HTML_DIR)
    alt_slugs = list_html_slugs(ALTERNATIVES_HTML_DIR)

    # Goal page tool references
    goal_tools = set()
    if GOALS_HTML_DIR.is_dir():
        import re
        for goal_file in GOALS_HTML_DIR.glob("*.html"):
            if goal_file.name == "index.html":
                continue
            try:
                content = goal_file.read_text(encoding="utf-8")
                for match in re.finditer(r'href=["\']/tools/([a-z0-9-]+)\.html["\']', content):
                    goal_tools.add(match.group(1))
                for match in re.finditer(r'data-tool-id=["\']([a-z0-9-]+)["\']', content):
                    goal_tools.add(match.group(1))
            except OSError:
                pass

    # Per-tool coverage
    per_tool = {}
    all_field_coverage = {}

    for tool in catalog_tools:
        tool_id = tool.get("id")
        if not tool_id:
            continue

        record = v2_by_id.get(tool_id)
        if not record:
            # Tool in catalog but no v2 record
            per_tool[tool_id] = {
                "fields": {},
                "pages": {},
                "note": "no tools-v2 record",
            }
            continue

        tool_slug = record.get("identity", {}).get("slug", tool_id)

        # Field coverage
        field_cov = check_field_coverage(record)
        per_tool[tool_id] = {
            "fields": field_cov,
            "pages": check_page_coverage(tool_id, tool_slug, html_slugs, compare_slugs, alt_slugs, goal_tools),
        }
        all_field_coverage[tool_id] = field_cov

    # Aggregate coverage
    aggregate = compute_aggregate_coverage(all_field_coverage)

    # Page coverage aggregate
    page_fields = set()
    page_coverage_data = {}
    for tool_id, data in per_tool.items():
        pages = data.get("pages", {})
        page_fields.update(pages.keys())
        for pf, status in pages.items():
            if pf not in page_coverage_data:
                page_coverage_data[pf] = {"present": 0, "missing": 0, "total": 0}
            page_coverage_data[pf]["total"] += 1
            if status == "present":
                page_coverage_data[pf]["present"] += 1
            else:
                page_coverage_data[pf]["missing"] += 1

    page_agg = {}
    for pf, stats in page_coverage_data.items():
        total = stats["total"]
        present = stats["present"]
        page_agg[pf] = {
            "present": present,
            "missing": stats["missing"],
            "total": total,
            "coverage_pct": round(present / total * 100, 1) if total else 0,
        }

    results = {
        "check": "data_coverage",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_tools": len(catalog_tools),
        "tools_with_v2_records": sum(1 for t in catalog_tools if t.get("id") in v2_by_id),
        "per_tool": per_tool,
        "aggregate_coverage": aggregate,
        "page_coverage_aggregate": page_agg,
    }

    return results


def main():
    results = run_coverage_report()

    # Ensure output directory exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # JSON report
    json_path = REPORTS_DIR / "data-coverage-report.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Markdown report
    md_content = generate_markdown_report(results)
    md_path = REPORTS_DIR / "data-coverage-report.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write(md_content)

    # Print summary
    print(f"\nData Coverage Report")
    print(f"  Total tools: {results['total_tools']}")
    print(f"  Tools with v2 records: {results['tools_with_v2_records']}")
    print(f"\n  Aggregate coverage (top fields):")
    for field, stats in list(results["aggregate_coverage"].items())[:10]:
        print(f"    {field}: {stats['coverage_pct']}%")

    print(f"\n  JSON report: {json_path}")
    print(f"  Markdown report: {md_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
