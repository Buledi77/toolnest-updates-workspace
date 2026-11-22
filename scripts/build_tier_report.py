#!/usr/bin/env python3
"""Build tier report — classify every page as gold/medium/thin using objective gate criteria.

Outputs /reports/tier-report.csv with columns:
  url, type, protected, tier, missing_items, gscImpressions

Gate-based tiering (C1 rewrite):
  Tool pages use 8 objective criteria from v2 JSON and rendered HTML:
    1. best_for (editorial.best_for non-empty)
    2. not_best_for (editorial.not_recommended_for non-empty)
    3. capabilities (factual_profile.capabilities non-empty)
    4. limitations (factual_profile.limitations key exists)
    5. source_ids (evidence.source_ids non-empty)
    6. alternatives_or_comparisons (relationships has alternatives or meaningful_comparisons)
    7. pricing_plans_with_sources (HTML pricing section has ≥2 plan rows)
    8. unique_body_words (HTML main content has ≥600 unique words)
  Gold: all 8 pass. Medium: 5-7 pass. Thin: 0-4 pass.

  Other page types use simplified criteria (unique body words + structural checks).

PROTECTED pages (never noindexed):
  - All tools in tools.json catalog
  - All URLs currently in sitemap.xml
  - Static pages: home, about, how-we-test, editorial-policy, privacy, terms,
    contact, affiliate-disclosure, corrections, all hub/index pages

Priority order:
  1. Pages with GSC impressions (if /data/gsc exists)
  2. Original catalog tools
  3. Other tools by category size
  4. Compare, alternatives, best, category, goals, static pages
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from content_metrics import measure, unique_marked_sections
from page_quality_gate import (
    load_catalog,
    load_v2,
    check_gate_criteria,
    gate_criteria_to_tier,
    QualitySignals,
)

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Static pages that are always protected
STATIC_PROTECTED = {
    "index.html",
    "about.html",
    "how-we-test.html",
    "editorial-policy.html",
    "privacy.html",
    "terms.html",
    "contact.html",
    "affiliate-disclosure.html",
    "corrections.html",
}

# Hub/index pages
HUB_PROTECTED_PATTERNS = {
    "tools/index.html",
    "compare/index.html",
    "alternatives/index.html",
    "best/index.html",
    "category/index.html",
    "goals/index.html",
}


def load_sitemap_urls() -> set[str]:
    """Load all URLs from sitemap.xml as relative paths."""
    sitemap = ROOT / "sitemap.xml"
    if not sitemap.exists():
        return set()
    content = sitemap.read_text(encoding="utf-8")
    urls = set()
    for match in re.finditer(r"<loc>(https://www\.toolnestai\.tech[^<]+)</loc>", content):
        path = match.group(1).replace("https://www.toolnestai.tech", "")
        # Normalize: remove trailing slash, handle .html
        if path == "/" or path == "":
            path = "/index.html"
        urls.add(path.lstrip("/"))
    return urls


def is_protected(relative_path: str, sitemap_urls: set[str], catalog_ids: set[str]) -> bool:
    """Check if a page is PROTECTED (never noindexed)."""
    # Static pages
    base = Path(relative_path).name
    if relative_path in STATIC_PROTECTED:
        return True
    # Hub/index pages
    if relative_path in HUB_PROTECTED_PATTERNS:
        return True
    # In sitemap
    if relative_path in sitemap_urls:
        return True
    # Original catalog tools (all 147 tools in tools.json are protected per R10)
    if relative_path.startswith("tools/") and base.endswith(".html"):
        slug = base[:-5]
        if slug in catalog_ids:
            return True
    return False


def grade_category_page(sig: QualitySignals) -> tuple[str, int, list[str]]:
    """Grade a category page."""
    score = 0
    missing = []
    if sig.words >= 500:
        score += 2
    elif sig.words >= 300:
        score += 1
    else:
        missing.append("low_word_count")
    if sig.has_sub_use_cases:
        score += 2
    else:
        missing.append("no_sub_use_cases")
    if sig.has_navigation_routes:
        score += 1
    else:
        missing.append("no_navigation_routes")
    if sig.unique_marked_sections >= 2:
        score += 1
    if score >= 4:
        grade = "A"
    elif score >= 2:
        grade = "B"
    else:
        grade = "C"
    return grade, score, missing


def grade_static_page(content: str, sig: QualitySignals) -> tuple[str, int, list[str]]:
    """Grade a static page."""
    score = 0
    missing = []
    if sig.words >= 400:
        score += 2
    elif sig.words >= 200:
        score += 1
    else:
        missing.append("low_word_count")
    if sig.unique_marked_sections >= 2:
        score += 1
    else:
        missing.append("no_unique_sections")
    if sig.sections >= 3:
        score += 1
    else:
        missing.append("too_few_sections")
    if score >= 3:
        grade = "A"
    elif score >= 2:
        grade = "B"
    else:
        grade = "C"
    return grade, score, missing


def grade_goals_page(sig: QualitySignals) -> tuple[str, int, list[str]]:
    """Grade a goals page."""
    score = 0
    missing = []
    if sig.words >= 500:
        score += 2
    elif sig.words >= 300:
        score += 1
    else:
        missing.append("low_word_count")
    if sig.unique_marked_sections >= 2:
        score += 1
    else:
        missing.append("no_unique_sections")
    if sig.sections >= 4:
        score += 1
    else:
        missing.append("too_few_sections")
    if score >= 3:
        grade = "A"
    elif score >= 2:
        grade = "B"
    else:
        grade = "C"
    return grade, score, missing


def grade_index_page(sig: QualitySignals) -> tuple[str, int, list[str]]:
    """Grade an index/hub page."""
    score = 0
    missing = []
    if sig.words >= 400:
        score += 2
    elif sig.words >= 200:
        score += 1
    else:
        missing.append("low_word_count")
    if sig.unique_marked_sections >= 2:
        score += 1
    else:
        missing.append("no_unique_sections")
    if sig.sections >= 3:
        score += 1
    else:
        missing.append("too_few_sections")
    if score >= 3:
        grade = "A"
    elif score >= 2:
        grade = "B"
    else:
        grade = "C"
    return grade, score, missing


def main() -> None:
    catalog = load_catalog()
    catalog_ids = set(catalog.keys())
    sitemap_urls = load_sitemap_urls()

    # Load all HTML content
    html_files = {}
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT).as_posix()
        if ".git" not in path.parts and rel not in {"404.html", "googlef7f3d54afb5d5344.html"}:
            html_files[rel] = path.read_text()

    results = []

    # Tool reviews — use gate criteria
    for slug in sorted(catalog_ids):
        rel = f"tools/{slug}.html"
        html_content = html_files.get(rel, "")
        v2 = load_v2(slug)
        criteria = check_gate_criteria(slug, "tool", v2, html_content)
        tier = gate_criteria_to_tier(criteria)
        missing = [k for k, v in criteria.items() if v is not True]
        protected = is_protected(rel, sitemap_urls, catalog_ids)
        results.append({
            "url": f"/tools/{slug}.html",
            "type": "tool",
            "protected": protected,
            "tier": tier,
            "missing_items": ";".join(missing) if missing else "",
            "gscImpressions": "",
        })

    # Compare pages
    compare_dir = ROOT / "compare"
    if compare_dir.exists():
        for path in sorted(compare_dir.glob("*.html")):
            slug = path.stem
            rel = f"compare/{slug}.html"
            html_content = html_files.get(rel, "")
            v2 = None
            criteria = check_gate_criteria(slug, "compare", v2, html_content)
            tier = gate_criteria_to_tier(criteria)
            missing = [k for k, v in criteria.items() if v is not True]
            protected = is_protected(rel, sitemap_urls, catalog_ids)
            results.append({
                "url": f"/compare/{slug}.html",
                "type": "compare",
                "protected": protected,
                "tier": tier,
                "missing_items": ";".join(missing) if missing else "",
                "gscImpressions": "",
            })

    # Alternatives pages
    alt_dir = ROOT / "alternatives"
    if alt_dir.exists():
        for path in sorted(alt_dir.glob("*.html")):
            slug = path.stem
            rel = f"alternatives/{slug}.html"
            html_content = html_files.get(rel, "")
            v2 = None
            criteria = check_gate_criteria(slug, "alternatives", v2, html_content)
            tier = gate_criteria_to_tier(criteria)
            missing = [k for k, v in criteria.items() if v is not True]
            protected = is_protected(rel, sitemap_urls, catalog_ids)
            results.append({
                "url": f"/alternatives/{slug}.html",
                "type": "alternatives",
                "protected": protected,
                "tier": tier,
                "missing_items": ";".join(missing) if missing else "",
                "gscImpressions": "",
            })

    # Best-of pages
    best_dir = ROOT / "best"
    if best_dir.exists():
        for path in sorted(best_dir.glob("*.html")):
            slug = path.stem
            rel = f"best/{slug}.html"
            html_content = html_files.get(rel, "")
            v2 = None
            criteria = check_gate_criteria(slug, "best", v2, html_content)
            tier = gate_criteria_to_tier(criteria)
            missing = [k for k, v in criteria.items() if v is not True]
            protected = is_protected(rel, sitemap_urls, catalog_ids)
            results.append({
                "url": f"/best/{slug}.html",
                "type": "best",
                "protected": protected,
                "tier": tier,
                "missing_items": ";".join(missing) if missing else "",
                "gscImpressions": "",
            })

    # Category pages
    cat_dir = ROOT / "category"
    if cat_dir.exists():
        for path in sorted(cat_dir.glob("*.html")):
            slug = path.stem
            rel = f"category/{slug}.html"
            html_content = html_files.get(rel, "")
            v2 = None
            criteria = check_gate_criteria(slug, "category", v2, html_content)
            tier = gate_criteria_to_tier(criteria)
            missing = [k for k, v in criteria.items() if v is not True]
            protected = is_protected(rel, sitemap_urls, catalog_ids)
            results.append({
                "url": f"/category/{slug}.html",
                "type": "category",
                "protected": protected,
                "tier": tier,
                "missing_items": ";".join(missing) if missing else "",
                "gscImpressions": "",
            })

    # Goals pages
    goals_dir = ROOT / "goals"
    if goals_dir.exists():
        for path in sorted(goals_dir.glob("*.html")):
            slug = path.stem
            rel = f"goals/{slug}.html"
            html_content = html_files.get(rel, "")
            v2 = None
            criteria = check_gate_criteria(slug, "goals", v2, html_content)
            tier = gate_criteria_to_tier(criteria)
            missing = [k for k, v in criteria.items() if v is not True]
            protected = is_protected(rel, sitemap_urls, catalog_ids)
            results.append({
                "url": f"/goals/{slug}.html",
                "type": "goals",
                "protected": protected,
                "tier": tier,
                "missing_items": ";".join(missing) if missing else "",
                "gscImpressions": "",
            })

    # Static pages
    for static_page in sorted(STATIC_PROTECTED):
        rel = static_page
        html_content = html_files.get(rel, "")
        v2 = None
        criteria = check_gate_criteria(static_page, "static", v2, html_content)
        tier = gate_criteria_to_tier(criteria)
        missing = [k for k, v in criteria.items() if v is not True]
        url = "/" if static_page == "index.html" else f"/{static_page}"
        results.append({
            "url": url,
            "type": "static",
            "protected": True,
            "tier": tier,
            "missing_items": ";".join(missing) if missing else "",
            "gscImpressions": "",
        })

    # Load GSC data if available
    gsc_file = ROOT / "data" / "gsc"
    gsc_data = {}
    if gsc_file.exists() and gsc_file.is_file():
        try:
            gsc_data = json.loads(gsc_file.read_text())
        except Exception:
            pass
    elif (ROOT / "data" / "gsc.json").exists():
        try:
            gsc_data = json.loads((ROOT / "data" / "gsc.json").read_text())
        except Exception:
            pass

    # Fill in GSC impressions
    for r in results:
        url = r["url"]
        if url in gsc_data:
            r["gscImpressions"] = str(gsc_data[url].get("impressions", ""))

    # Sort by priority: GSC impressions first, then protected, then by type priority
    type_priority = {
        "tool": 0, "compare": 1, "alternatives": 2, "best": 3,
        "category": 4, "goals": 5, "static": 6
    }

    def sort_key(r):
        has_gsc = 0 if r["gscImpressions"] else 1
        is_prot = 0 if r["protected"] else 1
        tp = type_priority.get(r["type"], 9)
        return (has_gsc, is_prot, tp)

    results.sort(key=sort_key)

    # Write CSV
    csv_path = REPORTS_DIR / "tier-report.csv"
    fieldnames = ["url", "type", "protected", "tier", "missing_items", "gscImpressions"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    # Print summary
    print(f"Tier report: {csv_path}")
    print(f"Total pages: {len(results)}")
    print()

    # Tier distribution
    tier_counts = {}
    type_tier_counts = {}
    for r in results:
        tier = r["tier"]
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        key = f"{r['type']}:{tier}"
        type_tier_counts[key] = type_tier_counts.get(key, 0) + 1

    print("Tier distribution:")
    for tier in ["gold", "medium", "thin"]:
        print(f"  {tier}: {tier_counts.get(tier, 0)}")
    print()

    print("By type and tier:")
    for key in sorted(type_tier_counts.keys()):
        print(f"  {key}: {type_tier_counts[key]}")
    print()

    # Per page type: ready (gold) vs not ready (medium + thin)
    print("Per type — ready / not ready:")
    for ptype in ["tool", "compare", "alternatives", "best", "category", "goals", "static"]:
        gold = type_tier_counts.get(f"{ptype}:gold", 0)
        medium = type_tier_counts.get(f"{ptype}:medium", 0)
        thin = type_tier_counts.get(f"{ptype}:thin", 0)
        not_ready = medium + thin
        print(f"  {ptype}: {gold} ready, {not_ready} not ready (medium={medium}, thin={thin})")
    print()

    # Protected vs non-protected
    protected_count = sum(1 for r in results if r["protected"])
    print(f"Protected pages: {protected_count}/{len(results)}")
    print(f"Non-protected pages: {len(results) - protected_count}/{len(results)}")
    print()

    # Flagged pages — print which criteria fail
    print("Flagged pages — gate criteria detail:")
    flagged_slugs = ["activecampaign", "pipedrive", "mozpro"]
    for slug in flagged_slugs:
        r = next((x for x in results if f"/tools/{slug}.html" in x["url"]), None)
        if r:
            print(f"  {r['url']}: tier={r['tier']}, missing={r['missing_items']}")
    # Compare page
    r = next((x for x in results if "mozpro-vs-semrush" in x["url"]), None)
    if r:
        print(f"  {r['url']}: tier={r['tier']}, missing={r['missing_items']}")
    print()

    # Thin pages that are NOT protected (candidates for noindex)
    thin_non_protected = [r for r in results if r["tier"] == "thin" and not r["protected"]]
    print(f"Thin non-protected pages (noindex candidates): {len(thin_non_protected)}")
    for r in thin_non_protected[:10]:
        print(f"  {r['url']} ({r['type']}, missing={r['missing_items']})")
    if len(thin_non_protected) > 10:
        print(f"  ... and {len(thin_non_protected) - 10} more")
    print()

    # Protected pages that are thin (need upgrade priority)
    thin_protected = [r for r in results if r["tier"] == "thin" and r["protected"]]
    print(f"Protected thin pages (upgrade priority): {len(thin_protected)}")
    for r in thin_protected[:10]:
        print(f"  {r['url']} ({r['type']}, missing={r['missing_items']})")
    if len(thin_protected) > 10:
        print(f"  ... and {len(thin_protected) - 10} more")

    print()
    print(f"Full CSV: {csv_path}")


if __name__ == "__main__":
    main()
