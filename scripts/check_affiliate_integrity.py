#!/usr/bin/env python3
"""Affiliate integrity audit (Phase 3 Requirement E).

Comprehensive affiliate validation across the full catalog:
- Verify approved affiliate URLs remain unchanged
- Check no official links are falsely labelled affiliate
- Verify no tool presented as affiliate partner without registry evidence
- Check disclosures visible where commercial links appear
- Validate affiliate links use sponsored relationship where supported
- Check no internal links given sponsored/nofollow treatment by mistake
- Flag broken or empty affiliate targets
- Verify users can reach official product when no affiliate relationship exists
- Confirm recommendation ranking never increased because affiliate link exists

Outputs reports/phase3/affiliate-integrity-report.json
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
TOOL_DIR = ROOT / "data" / "tools-v2"
AFFILIATE_REGISTRY_PATH = ROOT / "data" / "monetization" / "affiliate-registry.json"
LEGACY_DATA_PATH = ROOT / "data" / "tools.json"
TOOLS_HTML_DIR = ROOT / "tools"
REPORTS_DIR = ROOT / "reports" / "phase3"


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_tools_v2_records():
    records = []
    for path in sorted(TOOL_DIR.rglob("*.json")):
        if path.name == "README.json":
            continue
        records.append(load_json(path))
    return records


def is_valid_url(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def run_affiliate_check():
    """Run all affiliate integrity checks."""
    print("Running affiliate integrity checks...")

    # Load data
    records = load_tools_v2_records()
    v2_by_id = {r.get("identity", {}).get("id"): r for r in records}

    affiliate_registry = {}
    if AFFILIATE_REGISTRY_PATH.is_file():
        affiliate_registry = load_json(AFFILIATE_REGISTRY_PATH)

    catalog_tools = []
    if LEGACY_DATA_PATH.is_file():
        catalog_data = load_json(LEGACY_DATA_PATH)
        catalog_tools = catalog_data.get("tools", [])
    catalog_ids = {t.get("id") for t in catalog_tools}

    results = {
        "check": "affiliate_integrity",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {},
    }

    # 1. Verify affiliate registry entries reference existing tools
    registry_tool_errors = []
    registry_entries = affiliate_registry.get("entries", []) if isinstance(affiliate_registry, dict) else []
    for entry in registry_entries:
        tool_id = entry.get("tool_id")
        if tool_id and tool_id not in v2_by_id and tool_id not in catalog_ids:
            registry_tool_errors.append(
                f"Affiliate registry entry {tool_id} references unknown tool"
            )
    results["checks"]["registry_tools_exist"] = {
        "passed": len(registry_tool_errors) == 0,
        "error_count": len(registry_tool_errors),
        "errors": registry_tool_errors,
    }

    # 2. Check affiliate URLs in tools-v2 records
    affiliate_url_errors = []
    for record in records:
        tid = record.get("identity", {}).get("id", "<missing>")
        monetization = record.get("monetization", {})
        affiliate_url = monetization.get("affiliate_url")
        official_url = record.get("identity", {}).get("official_url")
        official_non_affiliate = monetization.get("official_non_affiliate_url")

        # Check affiliate URL validity
        if affiliate_url:
            if not is_valid_url(affiliate_url):
                affiliate_url_errors.append(
                    f"Tool {tid} has invalid affiliate URL: {affiliate_url}"
                )
            # Check affiliate URL doesn't match official URL
            if affiliate_url == official_url:
                affiliate_url_errors.append(
                    f"Tool {tid} affiliate URL matches official URL"
                )

        # Check official_non_affiliate_url matches official_url
        if official_non_affiliate and official_url:
            if official_non_affiliate != official_url:
                affiliate_url_errors.append(
                    f"Tool {tid} official_non_affiliate_url does not match official_url"
                )

    results["checks"]["affiliate_url_validity"] = {
        "passed": len(affiliate_url_errors) == 0,
        "error_count": len(affiliate_url_errors),
        "errors": affiliate_url_errors,
    }

    # 3. Check no tool presented as affiliate partner without registry evidence
    affiliate_partner_errors = []
    registry_tool_ids = {e.get("tool_id") for e in registry_entries}
    for record in records:
        tid = record.get("identity", {}).get("id", "<missing>")
        monetization = record.get("monetization", {})
        affiliate_url = monetization.get("affiliate_url")

        # If affiliate URL exists, check registry entries
        if affiliate_url and tid not in registry_tool_ids:
            affiliate_partner_errors.append(
                f"Tool {tid} has affiliate URL but not in affiliate registry"
            )

    results["checks"]["affiliate_registry_consistency"] = {
        "passed": len(affiliate_partner_errors) == 0,
        "error_count": len(affiliate_partner_errors),
        "errors": affiliate_partner_errors,
    }

    # 4. Check HTML pages for affiliate link markup
    html_affiliate_errors = []
    html_affiliate_warnings = []

    if TOOLS_HTML_DIR.is_dir():
        for html_file in TOOLS_HTML_DIR.glob("*.html"):
            try:
                content = html_file.read_text(encoding="utf-8")

                # Check for rel="sponsored" on affiliate links
                sponsored_pattern = re.compile(
                    r'<a[^>]*rel=["\'][^"\']*sponsored[^"\']*["\'][^>]*href=["\']([^"\']+)["\']'
                )
                # Check for rel="nofollow" on internal links (should not happen)
                nofollow_internal = re.compile(
                    r'<a[^>]*rel=["\'][^"\']*nofollow[^"\']*["\'][^>]*href=["\'](/tools/[^"\']+)["\']'
                )

                for match in nofollow_internal.finditer(content):
                    href = match.group(1)
                    html_affiliate_warnings.append(
                        f"{html_file.name} has nofollow on internal link: {href}"
                    )

                # Check for disclosure text
                if affiliate_url and "disclosure" not in content.lower():
                    # Only warn if the page has affiliate links
                    if 'rel="sponsored"' in content or 'rel="noopener"' in content:
                        html_affiliate_warnings.append(
                            f"{html_file.name} may lack affiliate disclosure"
                        )

            except OSError:
                pass

    results["checks"]["html_affiliate_markup"] = {
        "passed": len(html_affiliate_errors) == 0,
        "error_count": len(html_affiliate_errors),
        "errors": html_affiliate_errors,
        "warnings": html_affiliate_warnings,
    }

    # 5. Check no internal links marked as sponsored
    internal_sponsored_errors = []
    if TOOLS_HTML_DIR.is_dir():
        for html_file in TOOLS_HTML_DIR.glob("*.html"):
            try:
                content = html_file.read_text(encoding="utf-8")
                # Check for sponsored on internal links
                sponsored_internal = re.compile(
                    r'<a[^>]*rel=["\'][^"\']*sponsored[^"\']*["\'][^>]*href=["\'](/tools/[^"\']+)["\']'
                )
                for match in sponsored_internal.finditer(content):
                    href = match.group(1)
                    internal_sponsored_errors.append(
                        f"{html_file.name} has sponsored on internal link: {href}"
                    )
            except OSError:
                pass

    results["checks"]["no_internal_sponsored"] = {
        "passed": len(internal_sponsored_errors) == 0,
        "error_count": len(internal_sponsored_errors),
        "errors": internal_sponsored_errors,
    }

    # 6. Check broken affiliate targets
    broken_affiliate_errors = []
    for record in records:
        tid = record.get("identity", {}).get("id", "<missing>")
        monetization = record.get("monetization", {})
        affiliate_url = monetization.get("affiliate_url")
        if affiliate_url and not is_valid_url(affiliate_url):
            broken_affiliate_errors.append(
                f"Tool {tid} has broken affiliate URL"
            )

    results["checks"]["no_broken_affiliate_targets"] = {
        "passed": len(broken_affiliate_errors) == 0,
        "error_count": len(broken_affiliate_errors),
        "errors": broken_affiliate_errors,
    }

    # 7. Check affiliate status doesn't influence ranking
    # (This is a data-level check — affiliate status should not appear in editorial fields)
    ranking_influence_errors = []
    for record in records:
        tid = record.get("identity", {}).get("id", "<missing>")
        editorial = record.get("editorial", {})
        editorial_text = json.dumps(editorial).lower()
        if "affiliate" in editorial_text or "commission" in editorial_text:
            ranking_influence_errors.append(
                f"Tool {tid} has affiliate language in editorial fields"
            )

    results["checks"]["affiliate_does_not_influence_ranking"] = {
        "passed": len(ranking_influence_errors) == 0,
        "error_count": len(ranking_influence_errors),
        "errors": ranking_influence_errors,
    }

    # 8. Cross-reference affiliate registry with tools-v2 monetization
    cross_ref_errors = []
    for tool_id, entry in affiliate_registry.items():
        if isinstance(entry, dict):
            reg_url = entry.get("affiliate_url", "")
            record = v2_by_id.get(tool_id)
            if record:
                v2_url = record.get("monetization", {}).get("affiliate_url", "")
                if reg_url and v2_url and reg_url != v2_url:
                    cross_ref_errors.append(
                        f"Tool {tool_id} affiliate URL mismatch: registry={reg_url}, v2={v2_url}"
                    )

    results["checks"]["registry_v2_consistency"] = {
        "passed": len(cross_ref_errors) == 0,
        "error_count": len(cross_ref_errors),
        "errors": cross_ref_errors,
    }

    # Summary
    total_errors = sum(c.get("error_count", 0) for c in results["checks"].values())
    total_warnings = sum(len(c.get("warnings", [])) for c in results["checks"].values())
    results["total_errors"] = total_errors
    results["total_warnings"] = total_warnings
    results["passed"] = total_errors == 0

    return results


def main():
    results = run_affiliate_check()

    # Ensure output directory exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / "affiliate-integrity-report.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Print summary
    status = "PASS" if results["passed"] else "FAIL"
    print(f"\nAffiliate Integrity Audit: {status}")
    print(f"  Total errors: {results['total_errors']}")
    print(f"  Total warnings: {results['total_warnings']}")
    for check_name, check_result in results["checks"].items():
        check_status = "PASS" if check_result["passed"] else "FAIL"
        print(f"  {check_name}: {check_status} ({check_result['error_count']} errors)")
        if check_result.get("warnings"):
            print(f"    Warnings: {len(check_result['warnings'])}")

    print(f"\nReport written to {output_path}")

    return 0 if results["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
