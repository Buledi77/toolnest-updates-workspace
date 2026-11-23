#!/usr/bin/env python3
"""Regression tests for Phase 3 QA checks.

Validates that all check modules produce expected output and structure.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REPORTS_DIR = ROOT / "reports" / "phase3"


def test_inventory_count_matches_catalog():
    """All 153 tools from tools.json appear in the inventory report."""
    report = json.loads((REPORTS_DIR / "tool-inventory-report.json").read_text())
    assert report["catalog_count"] == 153, f"Expected 153, got {report['catalog_count']}"
    print("  ✅ Inventory count matches catalog (153)")


def test_no_duplicate_ids_or_slugs():
    """No duplicate IDs or slugs in tools-v2."""
    report = json.loads((REPORTS_DIR / "tool-inventory-report.json").read_text())
    unique_ids = report["checks"]["unique_ids"]
    unique_slugs = report["checks"]["unique_slugs"]
    assert unique_ids["passed"], f"Duplicate IDs found: {unique_ids['errors']}"
    assert unique_slugs["passed"], f"Duplicate slugs found: {unique_slugs['errors']}"
    print("  ✅ No duplicate IDs or slugs")


def test_all_relationships_resolve():
    """All relationship references resolve to existing tools."""
    report = json.loads((REPORTS_DIR / "tool-inventory-report.json").read_text())
    rel_check = report["checks"]["relationship_references"]
    assert rel_check["passed"], f"Broken relationships: {rel_check['errors']}"
    print("  ✅ All relationship references resolve")


def test_coverage_report_structure():
    """Data coverage report has expected structure."""
    report = json.loads((REPORTS_DIR / "data-coverage-report.json").read_text())
    assert "per_tool" in report
    assert "aggregate_coverage" in report
    assert report["total_tools"] == 153
    # Check that all tools have field coverage data
    for tool_id, data in report["per_tool"].items():
        assert "fields" in data, f"Tool {tool_id} missing fields data"
    print("  ✅ Coverage report structure valid")


def test_freshness_thresholds_configurable():
    """Freshness policy file loads correctly."""
    policy_path = ROOT / "data" / "freshness-policy.json"
    assert policy_path.is_file(), "Freshness policy file not found"
    policy = json.loads(policy_path.read_text())
    assert "thresholds" in policy
    assert "pricing" in policy["thresholds"]
    assert policy["thresholds"]["pricing"] == 90
    print("  ✅ Freshness thresholds configurable")


def test_evidence_freshness_report():
    """Evidence freshness report has expected structure."""
    report = json.loads((REPORTS_DIR / "evidence-freshness-report.json").read_text())
    assert "claims" in report
    assert "tools" in report
    assert "summary" in report
    assert "status_counts" in report["summary"]
    for status in ["VERIFIED_CURRENTLY", "NEEDS_RECHECK", "UNKNOWN", "NOT_COLLECTED"]:
        assert status in report["summary"]["status_counts"]
    print("  ✅ Evidence freshness report valid")


def test_no_affiliate_as_evidence():
    """No affiliate URLs used as factual evidence."""
    report = json.loads((REPORTS_DIR / "source-link-integrity.json").read_text())
    source_check = report["checks"]["source_urls"]
    # Check that no errors mention affiliate URLs as evidence
    affiliate_errors = [e for e in source_check.get("errors", [])
                        if "affiliate" in e.lower()]
    assert len(affiliate_errors) == 0, f"Affiliate URLs used as evidence: {affiliate_errors}"
    print("  ✅ No affiliate URLs as evidence")


def test_beta_pages_noindex():
    """Decision engine and stack analyzer are noindex."""
    report = json.loads((REPORTS_DIR / "seo-integrity-report.json").read_text())
    beta_check = report["checks"]["beta_pages_noindex"]
    assert beta_check["passed"], f"Beta page issues: {beta_check['errors']}"
    print("  ✅ Beta pages are noindex")


def test_sitemap_no_duplicates():
    """Sitemap has no duplicate URLs."""
    report = json.loads((REPORTS_DIR / "seo-integrity-report.json").read_text())
    sitemap_check = report["checks"]["sitemap_no_duplicates"]
    assert sitemap_check["passed"], f"Duplicate sitemap URLs: {sitemap_check['errors']}"
    print("  ✅ Sitemap has no duplicates")


def test_sitemap_no_noindex_pages():
    """Sitemap does not include noindex pages."""
    report = json.loads((REPORTS_DIR / "seo-integrity-report.json").read_text())
    check = report["checks"]["sitemap_no_noindex"]
    assert check["passed"], f"Noindex pages in sitemap: {check['errors']}"
    print("  ✅ Sitemap has no noindex pages")


def test_internal_link_graph_structure():
    """Internal link graph report has expected structure."""
    report = json.loads((REPORTS_DIR / "internal-link-graph.json").read_text())
    assert "checks" in report
    assert "orphaned_pages" in report["checks"]
    assert "orphaned_profiles" in report["checks"]
    assert "unlinked_comparisons" in report["checks"]
    assert "unlinked_alternatives" in report["checks"]
    assert "unconnected_goals" in report["checks"]
    print("  ✅ Internal link graph structure valid")


def test_affiliate_integrity_structure():
    """Affiliate integrity report has expected structure."""
    report = json.loads((REPORTS_DIR / "affiliate-integrity-report.json").read_text())
    assert "checks" in report
    assert "affiliate_url_validity" in report["checks"]
    assert "affiliate_registry_consistency" in report["checks"]
    assert "affiliate_does_not_influence_ranking" in report["checks"]
    print("  ✅ Affiliate integrity structure valid")


def test_consolidated_report():
    """Consolidated report aggregates all modules."""
    report = json.loads((REPORTS_DIR / "consolidated-report.json").read_text())
    assert report["total_checks"] == 7
    assert len(report["modules"]) == 7
    module_ids = [m["module"] for m in report["modules"]]
    for mid in ["A", "B", "C", "D", "E", "F", "G"]:
        assert mid in module_ids, f"Module {mid} missing from consolidated report"
    print("  ✅ Consolidated report aggregates all 7 modules")


def test_markdown_report_exists():
    """Markdown consolidated report exists and is non-empty."""
    md_path = REPORTS_DIR / "consolidated-report.md"
    assert md_path.is_file(), "Markdown report not found"
    content = md_path.read_text()
    assert len(content) > 100, "Markdown report is too short"
    assert "Phase 3 QA Consolidated Report" in content
    print("  ✅ Markdown report exists and is valid")


def main():
    print("Running Phase 3 QA regression tests...\n")

    tests = [
        test_inventory_count_matches_catalog,
        test_no_duplicate_ids_or_slugs,
        test_all_relationships_resolve,
        test_coverage_report_structure,
        test_freshness_thresholds_configurable,
        test_evidence_freshness_report,
        test_no_affiliate_as_evidence,
        test_beta_pages_noindex,
        test_sitemap_no_duplicates,
        test_sitemap_no_noindex_pages,
        test_internal_link_graph_structure,
        test_affiliate_integrity_structure,
        test_consolidated_report,
        test_markdown_report_exists,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ {test.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")
    print(f"{'=' * 50}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
