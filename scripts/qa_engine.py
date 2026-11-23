#!/usr/bin/env python3
"""QA Engine — central orchestrator for all Phase 3 checks.

Runs all 7 check modules (A–G) in sequence, aggregates results, and produces
consolidated reports in reports/phase3/.

Usage:
    python scripts/qa_engine.py                  # Run all checks
    python scripts/qa_engine.py --module A       # Run only module A
    python scripts/qa_engine.py --check-external # Enable external URL checks
    python scripts/qa_engine.py --json           # Machine-readable output only
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports" / "phase3"

# Add project root to path so we can import scripts
sys.path.insert(0, str(ROOT))


def run_module(module_id, check_external=False):
    """Run a single check module by ID."""
    if module_id == "A":
        from scripts.check_tool_inventory import run_inventory_check
        result = run_inventory_check()
        return {"module": "A", "name": "Tool Inventory Validation", "result": result}

    elif module_id == "B":
        from scripts.build_data_coverage_report import run_coverage_report
        result = run_coverage_report()
        return {"module": "B", "name": "Data Coverage Report", "result": result}

    elif module_id == "C":
        from scripts.check_evidence_freshness import check_evidence_freshness
        result = check_evidence_freshness()
        return {"module": "C", "name": "Evidence Freshness Engine", "result": result}

    elif module_id == "D":
        from scripts.check_source_link_integrity import run_source_link_check
        result = run_source_link_check(check_external=check_external)
        return {"module": "D", "name": "Source and Link Integrity", "result": result}

    elif module_id == "E":
        from scripts.check_affiliate_integrity import run_affiliate_check
        result = run_affiliate_check()
        return {"module": "E", "name": "Affiliate Integrity Audit", "result": result}

    elif module_id == "F":
        from scripts.check_seo_integrity import run_seo_check
        result = run_seo_check()
        return {"module": "F", "name": "SEO and Technical Integrity", "result": result}

    elif module_id == "G":
        from scripts.build_internal_link_graph import run_link_graph_check
        result = run_link_graph_check()
        return {"module": "G", "name": "Internal Link Graph", "result": result}

    else:
        return {"module": module_id, "name": "Unknown", "error": f"Unknown module: {module_id}"}


def generate_consolidated_md(results):
    """Generate a human-readable Markdown consolidated report."""
    lines = []
    lines.append("# Phase 3 QA Consolidated Report")
    lines.append("")
    lines.append(f"Generated: {results['timestamp']}")
    lines.append(f"Duration: {results.get('duration_seconds', 0):.1f}s")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    total_checks = results.get("total_checks", 0)
    passed_modules = results.get("passed_modules", 0)
    failed_modules = results.get("failed_modules", 0)
    total_errors = results.get("total_errors", 0)
    lines.append(f"- **Total modules**: {total_checks}")
    lines.append(f"- **Passed**: {passed_modules}")
    lines.append(f"- **Failed**: {failed_modules}")
    lines.append(f"- **Total errors**: {total_errors}")
    lines.append("")

    # Module results
    lines.append("## Module Results")
    lines.append("")

    for module_result in results.get("modules", []):
        module_id = module_result.get("module", "?")
        name = module_result.get("name", "Unknown")
        result = module_result.get("result", {})

        # Determine pass/fail
        passed = result.get("passed", result.get("total_issues", 0) == 0)
        status = "✅ PASS" if passed else "❌ FAIL"
        error_count = result.get("total_errors", result.get("total_issues", 0))

        lines.append(f"### {module_id}. {name} — {status}")
        lines.append("")

        if isinstance(error_count, int):
            lines.append(f"- Errors: {error_count}")

        # Show sub-checks if available
        checks = result.get("checks", {})
        if checks:
            lines.append("")
            for check_name, check_data in checks.items():
                if isinstance(check_data, dict):
                    if "passed" in check_data:
                        check_status = "✅" if check_data["passed"] else "❌"
                        check_errors = check_data.get("error_count", 0)
                        lines.append(f"  - {check_status} {check_name} ({check_errors} errors)")
                    elif "count" in check_data:
                        lines.append(f"  - {check_name}: {check_data['count']}")

        lines.append("")

    # Recommendations
    lines.append("## Recommendations")
    lines.append("")

    if failed_modules > 0:
        lines.append("The following modules require attention:")
        lines.append("")
        for module_result in results.get("modules", []):
            result = module_result.get("result", {})
            if not result.get("passed", True):
                name = module_result.get("name", "Unknown")
                error_count = result.get("total_errors", result.get("total_issues", 0))
                lines.append(f"- **{name}**: {error_count} errors — review `reports/phase3/` for details")
        lines.append("")

    lines.append("---")
    lines.append("*This report is generated automatically by the Phase 3 QA Engine.*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Phase 3 QA Engine")
    parser.add_argument("--module", type=str, default=None,
                        help="Run only a specific module (A-G)")
    parser.add_argument("--check-external", action="store_true",
                        help="Enable network-based external URL checking")
    parser.add_argument("--json", action="store_true", dest="json_only",
                        help="Output machine-readable JSON only")
    args = parser.parse_args()

    # Ensure output directory exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    start_time = time.time()

    # Determine which modules to run
    if args.module:
        modules = [args.module.upper()]
    else:
        modules = ["A", "B", "C", "D", "E", "F", "G"]

    print(f"Phase 3 QA Engine — running modules: {', '.join(modules)}")
    print(f"External URL checks: {'enabled' if args.check_external else 'disabled'}")
    print()

    # Run modules
    all_results = []
    for module_id in modules:
        print(f"Running module {module_id}...")
        result = run_module(module_id, check_external=args.check_external)
        all_results.append(result)
        print()

    duration = time.time() - start_time

    # Aggregate results
    total_errors = 0
    passed_modules = 0
    failed_modules = 0

    for module_result in all_results:
        result = module_result.get("result", {})
        errors = result.get("total_errors", result.get("total_issues", 0))
        passed = result.get("passed", errors == 0)
        if isinstance(errors, int):
            total_errors += errors
        if passed:
            passed_modules += 1
        else:
            failed_modules += 1

    consolidated = {
        "check": "consolidated_qa",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(duration, 1),
        "total_checks": len(all_results),
        "passed_modules": passed_modules,
        "failed_modules": failed_modules,
        "total_errors": total_errors,
        "modules": all_results,
    }

    # Write JSON report
    json_path = REPORTS_DIR / "consolidated-report.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(consolidated, f, indent=2, ensure_ascii=False)

    # Write Markdown report
    md_content = generate_consolidated_md(consolidated)
    md_path = REPORTS_DIR / "consolidated-report.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write(md_content)

    # Print summary
    print("=" * 60)
    print(f"Phase 3 QA Engine — Complete")
    print(f"  Duration: {duration:.1f}s")
    print(f"  Modules: {len(all_results)}")
    print(f"  Passed: {passed_modules}")
    print(f"  Failed: {failed_modules}")
    print(f"  Total errors: {total_errors}")
    print("=" * 60)

    if not args.json_only:
        print()
        print(f"JSON report: {json_path}")
        print(f"Markdown report: {md_path}")
        print()
        print("Individual reports in reports/phase3/:")
        for report_file in sorted(REPORTS_DIR.glob("*.json")):
            if report_file.name != "consolidated-report.json":
                print(f"  - {report_file.name}")

    return 0 if failed_modules == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
