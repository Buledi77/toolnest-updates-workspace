#!/usr/bin/env python3
"""Authoritative tool inventory validation (Phase 3 Requirement A).

Validates all 147 tools across tools-v2, tools.json, HTML pages, search index,
and cross-references.  Outputs reports/phase3/tool-inventory-report.json.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL_DIR = ROOT / "data" / "tools-v2"
LEGACY_DATA_PATH = ROOT / "data" / "tools.json"
SEARCH_INDEX_PATH = ROOT / "data" / "indexes" / "tool-search-index.json"
TOOLS_HTML_DIR = ROOT / "tools"
COMPARE_HTML_DIR = ROOT / "compare"
ALTERNATIVES_HTML_DIR = ROOT / "alternatives"
GOALS_HTML_DIR = ROOT / "goals"
REPORTS_DIR = ROOT / "reports" / "phase3"

# Special tool pages that are not tool profiles
SPECIAL_TOOL_PAGES = {
    "decision-engine",
    "stack-analyzer",
    "overlap-checker",
    "workflow-explorer",
    "automation-budget-estimator",
    "index",
}

COMPARE_INDEX = "index.html"
GOALS_INDEX = "index.html"


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def list_html_slugs(directory: Path) -> set:
    """Return the set of slugs from *.html files in a directory (without .html)."""
    slugs = set()
    if not directory.is_dir():
        return slugs
    for html_file in directory.glob("*.html"):
        slug = html_file.stem
        slugs.add(slug)
    return slugs


def load_catalog_tools():
    """Load the authoritative tool list from data/tools.json."""
    data = load_json(LEGACY_DATA_PATH)
    return data.get("tools", [])


def load_tools_v2_records():
    """Load all tools-v2 JSON records."""
    records = []
    for path in sorted(TOOL_DIR.rglob("*.json")):
        if path.name == "README.json":
            continue
        records.append(load_json(path))
    return records


def load_search_index():
    """Load the search index documents."""
    if not SEARCH_INDEX_PATH.is_file():
        return []
    data = load_json(SEARCH_INDEX_PATH)
    return data.get("documents", [])


def check_unique_ids(records):
    """Check that all tool IDs are unique."""
    errors = []
    ids = [r.get("identity", {}).get("id", "<missing>") for r in records]
    seen = {}
    for tid in ids:
        if tid in seen:
            errors.append(f"Duplicate tool ID: {tid}")
        seen[tid] = seen.get(tid, 0) + 1
    return errors


def check_unique_slugs(records):
    """Check that all tool slugs are unique."""
    errors = []
    slugs = [r.get("identity", {}).get("slug", "<missing>") for r in records]
    seen = {}
    for slug in slugs:
        if slug in seen:
            errors.append(f"Duplicate tool slug: {slug}")
        seen[slug] = seen.get(slug, 0) + 1
    return errors


def check_catalog_count(catalog_tools):
    """Verify the catalog tools array length matches the declared count."""
    errors = []
    count = len(catalog_tools)
    catalog_data = load_json(LEGACY_DATA_PATH)
    expected = catalog_data.get("count", count)
    if count != expected:
        errors.append(f"Expected {expected} tools in catalog (declared count), found {count}")
    return errors


def check_each_catalog_tool_has_v2_record(catalog_tools, v2_records_by_id):
    """Check that every tool in tools.json has a tools-v2 record."""
    errors = []
    for tool in catalog_tools:
        tid = tool.get("id")
        if tid and tid not in v2_records_by_id:
            errors.append(f"Catalog tool {tid} has no tools-v2 record")
    return errors


def check_each_v2_record_has_html_page(v2_records, html_slugs):
    """Check that each tools-v2 record has a corresponding HTML page.
    
    Skips records explicitly marked as unpublished (standalone_page_status=none)
    since they are data-only expansion records not intended for public publication.
    """
    errors = []
    for record in v2_records:
        slug = record.get("identity", {}).get("slug")
        if slug and slug not in SPECIAL_TOOL_PAGES and slug not in html_slugs:
            # Skip data-only expansion records not intended for publication
            status = record.get("publishing", {}).get("standalone_page_status")
            if status == "none":
                continue
            errors.append(f"Tool {slug} has no HTML page in tools/")
    return errors


def check_each_html_page_has_v2_record(html_slugs, v2_records_by_slug):
    """Check that each HTML page in tools/ has a corresponding tools-v2 record."""
    errors = []
    for slug in html_slugs:
        if slug in SPECIAL_TOOL_PAGES:
            continue
        if slug not in v2_records_by_slug:
            errors.append(f"HTML page tools/{slug}.html has no tools-v2 record")
    return errors


def check_search_index_coverage(catalog_tools, search_docs):
    """Check that catalog tools appear in the search index."""
    errors = []
    search_ids = {doc.get("id") for doc in search_docs}
    for tool in catalog_tools:
        tid = tool.get("id")
        if tid and tid not in search_ids:
            errors.append(f"Catalog tool {tid} not in search index")
    return errors


def check_search_index_matches_inventory(search_docs, v2_records_by_id):
    """Check that search index entries correspond to tools-v2 records."""
    errors = []
    for doc in search_docs:
        doc_id = doc.get("id")
        if doc_id and doc_id not in v2_records_by_id:
            errors.append(f"Search index entry {doc_id} has no tools-v2 record")
    return errors


def check_relationship_references(v2_records, v2_ids):
    """Validate that all relationship references resolve to existing tool IDs."""
    errors = []
    relation_fields = [
        "alternatives",
        "related_tools",
        "compatible_tools",
        "replaces",
        "replaced_by",
    ]
    for record in v2_records:
        tid = record.get("identity", {}).get("id", "<missing>")
        relationships = record.get("relationships", {})
        for field in relation_fields:
            for ref_id in relationships.get(field, []):
                if ref_id not in v2_ids:
                    errors.append(
                        f"Tool {tid} references missing tool {ref_id} in {field}"
                    )
    return errors


def check_comparison_references(v2_records, v2_ids, compare_slugs):
    """Validate meaningful_comparisons references resolve to existing compare pages."""
    errors = []
    for record in v2_records:
        tid = record.get("identity", {}).get("id", "<missing>")
        comparisons = record.get("relationships", {}).get("meaningful_comparisons", [])
        for comp_slug in comparisons:
            if comp_slug not in compare_slugs:
                errors.append(
                    f"Tool {tid} references missing comparison page {comp_slug}"
                )
    return errors


def check_compare_pages_reference_existing_tools(compare_slugs, v2_ids):
    """Check that comparison pages reference existing tool IDs."""
    errors = []
    # Parse compare slugs to extract tool IDs (e.g., "ahrefs-vs-semrush" -> "ahrefs", "semrush")
    vs_pattern = re.compile(r"^([a-z0-9]+(?:-[a-z0-9]+)*)-vs-([a-z0-9]+(?:-[a-z0-9]+)*)$")
    for slug in compare_slugs:
        if slug == COMPARE_INDEX:
            continue
        match = vs_pattern.match(slug)
        if match:
            tool1, tool2 = match.group(1), match.group(2)
            if tool1 not in v2_ids:
                errors.append(f"Compare page {slug} references missing tool {tool1}")
            if tool2 not in v2_ids:
                errors.append(f"Compare page {slug} references missing tool {tool2}")
    return errors


def check_alternatives_pages_reference_existing_tools(alt_slugs, v2_ids):
    """Check that alternatives pages reference existing tool IDs."""
    errors = []
    alt_pattern = re.compile(r"^(.+)-alternatives$")
    for slug in alt_slugs:
        match = alt_pattern.match(slug)
        if match:
            tool_id = match.group(1)
            if tool_id not in v2_ids:
                errors.append(
                    f"Alternatives page {slug} references missing tool {tool_id}"
                )
    return errors


def check_goal_pages_connect_to_tools(v2_records, goals_html_dir):
    """Check that goal pages reference tools that exist in the inventory."""
    errors = []
    v2_ids = {r.get("identity", {}).get("id") for r in v2_records}
    # Goal pages reference tools via data attributes or links; we check the HTML
    if not goals_html_dir.is_dir():
        return errors
    for goal_file in goals_html_dir.glob("*.html"):
        if goal_file.name == GOALS_INDEX:
            continue
        try:
            content = goal_file.read_text(encoding="utf-8")
            # Goal pages list tool IDs in data-tool-id attributes or /tools/<slug>.html links
            tool_refs = re.findall(r'data-tool-id=["\']([a-z0-9-]+)["\']', content)
            for match in re.finditer(r'href=["\']/tools/([a-z0-9-]+)\.html["\']', content):
                tool_refs.append(match.group(1))
            for ref in tool_refs:
                # Skip non-tool references like index pages
                if ref in SPECIAL_TOOL_PAGES:
                    continue
                if ref and ref not in v2_ids:
                    errors.append(
                        f"Goal page {goal_file.name} references missing tool {ref}"
                    )
        except OSError:
            pass
    return errors


def check_orphaned_v2_records(v2_records, catalog_ids):
    """Check for tools-v2 records not in the catalog (expansion tools)."""
    warnings = []
    for record in v2_records:
        tid = record.get("identity", {}).get("id")
        if tid and tid not in catalog_ids:
            warnings.append(
                f"Tool {tid} exists in tools-v2 but not in catalog (expansion tool)"
            )
    return warnings


def run_inventory_check():
    """Run all inventory checks and return structured results."""
    print("Loading data sources...")

    # Load data
    catalog_tools = load_catalog_tools()
    v2_records = load_tools_v2_records()
    search_docs = load_search_index()

    # Build lookup maps
    v2_records_by_id = {r.get("identity", {}).get("id"): r for r in v2_records}
    v2_records_by_slug = {r.get("identity", {}).get("slug"): r for r in v2_records}
    v2_ids = set(v2_records_by_id.keys())
    catalog_ids = {t.get("id") for t in catalog_tools}

    # Load HTML slugs
    html_slugs = list_html_slugs(TOOLS_HTML_DIR)
    compare_slugs = list_html_slugs(COMPARE_HTML_DIR)
    alt_slugs = list_html_slugs(ALTERNATIVES_HTML_DIR)

    results = {
        "check": "tool_inventory",
        "timestamp": None,  # filled below
        "catalog_count": len(catalog_tools),
        "v2_record_count": len(v2_records),
        "search_index_count": len(search_docs),
        "html_profile_count": len(html_slugs - SPECIAL_TOOL_PAGES),
        "compare_page_count": len(compare_slugs) - (1 if COMPARE_INDEX in compare_slugs else 0),
        "alternatives_page_count": len(alt_slugs),
        "checks": {},
    }

    # Run checks
    checks = [
        ("unique_ids", check_unique_ids(v2_records)),
        ("unique_slugs", check_unique_slugs(v2_records)),
        ("catalog_count", check_catalog_count(catalog_tools)),
        ("catalog_tools_have_v2_records", check_each_catalog_tool_has_v2_record(catalog_tools, v2_records_by_id)),
        ("v2_records_have_html_pages", check_each_v2_record_has_html_page(v2_records, html_slugs)),
        ("html_pages_have_v2_records", check_each_html_page_has_v2_record(html_slugs, v2_records_by_slug)),
        ("search_index_coverage", check_search_index_coverage(catalog_tools, search_docs)),
        ("search_index_matches_inventory", check_search_index_matches_inventory(search_docs, v2_records_by_id)),
        ("relationship_references", check_relationship_references(v2_records, v2_ids)),
        ("comparison_references", check_comparison_references(v2_records, v2_ids, compare_slugs)),
        ("compare_pages_reference_tools", check_compare_pages_reference_existing_tools(compare_slugs, v2_ids)),
        ("alternatives_pages_reference_tools", check_alternatives_pages_reference_existing_tools(alt_slugs, v2_ids)),
        ("goal_pages_connect_to_tools", check_goal_pages_connect_to_tools(v2_records, GOALS_HTML_DIR)),
    ]

    for name, errs in checks:
        results["checks"][name] = {
            "passed": len(errs) == 0,
            "error_count": len(errs),
            "errors": errs,
        }

    # Warnings for orphaned expansion tools
    orphan_warnings = check_orphaned_v2_records(v2_records, catalog_ids)
    results["orphan_warnings"] = orphan_warnings

    # Summary
    total_errors = sum(c["error_count"] for c in results["checks"].values())
    results["total_errors"] = total_errors
    results["passed"] = total_errors == 0

    from datetime import datetime, timezone
    results["timestamp"] = datetime.now(timezone.utc).isoformat()

    return results


def main():
    results = run_inventory_check()

    # Ensure output directory exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / "tool-inventory-report.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Print summary
    status = "PASS" if results["passed"] else "FAIL"
    print(f"\nTool Inventory Check: {status}")
    print(f"  Catalog tools: {results['catalog_count']}")
    print(f"  tools-v2 records: {results['v2_record_count']}")
    print(f"  Search index entries: {results['search_index_count']}")
    print(f"  HTML profile pages: {results['html_profile_count']}")
    print(f"  Compare pages: {results['compare_page_count']}")
    print(f"  Alternatives pages: {results['alternatives_page_count']}")
    print(f"  Total errors: {results['total_errors']}")

    for check_name, check_result in results["checks"].items():
        check_status = "PASS" if check_result["passed"] else "FAIL"
        print(f"  {check_name}: {check_status} ({check_result['error_count']} errors)")

    if results["orphan_warnings"]:
        print(f"\n  Orphan warnings ({len(results['orphan_warnings'])}):")
        for warn in results["orphan_warnings"][:10]:
            print(f"    - {warn}")
        if len(results["orphan_warnings"]) > 10:
            print(f"    ... and {len(results['orphan_warnings']) - 10} more")

    print(f"\nReport written to {output_path}")

    return 0 if results["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
