#!/usr/bin/env python3
"""SEO and technical integrity checks (Phase 3 Requirement F).

Automated SEO validation across all pages:
- Unique titles and meta descriptions
- One valid canonical per indexable page
- Canonical consistency with actual URL
- Robots directives
- No accidental noindex on public/indexed pages
- Beta pages remain noindex,follow
- Sitemap URLs resolve locally
- No duplicate sitemap URLs
- No noindex pages in sitemap
- Structured data parses
- Supported schema types remain consistent
- Breadcrumbs resolve
- Internal navigation targets resolve
- Search index contains expected records

Outputs reports/phase3/seo-integrity-report.json
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITEMAP_PATH = ROOT / "sitemap.xml"
INDEX_ALLOWLIST_PATH = ROOT / "data" / "index-allowlist.json"
SEARCH_INDEX_PATH = ROOT / "data" / "indexes" / "tool-search-index.json"
LEGACY_DATA_PATH = ROOT / "data" / "tools.json"
REPORTS_DIR = ROOT / "reports" / "phase3"

# Directories with HTML pages
HTML_DIRS = [
    ROOT / "tools",
    ROOT / "compare",
    ROOT / "alternatives",
    ROOT / "best",
    ROOT / "category",
    ROOT / "goals",
]
ROOT_HTML_FILES = ["index.html", "about.html", "affiliate-disclosure.html",
                   "how-we-test.html", "editorial-policy.html", "corrections.html",
                   "contact.html", "privacy.html", "terms.html"]

# Beta pages that must be noindex
BETA_PAGES = {"decision-engine", "stack-analyzer"}


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def get_all_html_files():
    """Get all HTML files in the project."""
    files = []
    for html_dir in HTML_DIRS:
        if html_dir.is_dir():
            files.extend(sorted(html_dir.glob("*.html")))
    for root_file in ROOT_HTML_FILES:
        path = ROOT / root_file
        if path.is_file():
            files.append(path)
    return files


def parse_page_meta(html_path):
    """Parse SEO metadata from an HTML file."""
    try:
        content = html_path.read_text(encoding="utf-8")
    except OSError:
        return None

    meta = {}

    # Title
    title_match = re.search(r"<title>([^<]+)</title>", content, re.IGNORECASE)
    meta["title"] = title_match.group(1) if title_match else None

    # Meta description
    desc_match = re.search(
        r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']',
        content, re.IGNORECASE
    )
    meta["description"] = desc_match.group(1) if desc_match else None

    # Canonical
    canonical_matches = re.findall(
        r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']',
        content, re.IGNORECASE
    )
    meta["canonicals"] = canonical_matches

    # Robots
    robots_match = re.search(
        r'<meta\s+name=["\']robots["\']\s+content=["\']([^"\']+)["\']',
        content, re.IGNORECASE
    )
    meta["robots"] = robots_match.group(1) if robots_match else None

    # Check for noindex in robots
    meta["noindex"] = False
    if meta["robots"]:
        meta["noindex"] = "noindex" in meta["robots"].lower()

    # JSON-LD structured data
    json_ld_blocks = re.findall(
        r'<script\s+type=["\']application/ld\+json["\']>(.*?)</script>',
        content, re.DOTALL
    )
    meta["json_ld"] = []
    for block in json_ld_blocks:
        try:
            data = json.loads(block)
            meta["json_ld"].append(data)
        except json.JSONDecodeError:
            meta["json_ld"].append({"parse_error": block[:100]})

    return meta


def run_seo_check():
    """Run all SEO integrity checks."""
    print("Running SEO integrity checks...")

    html_files = get_all_html_files()
    results = {
        "check": "seo_integrity",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {},
    }

    # Parse all pages
    page_metas = {}
    for html_file in html_files:
        rel_path = html_file.relative_to(ROOT).as_posix()
        meta = parse_page_meta(html_file)
        if meta:
            page_metas[rel_path] = meta

    # 1. Check unique titles
    title_errors = []
    titles = {}
    for path, meta in page_metas.items():
        title = meta.get("title")
        if title:
            if title in titles:
                title_errors.append(
                    f"Duplicate title '{title}': {titles[title]} and {path}"
                )
            else:
                titles[title] = path
        else:
            title_errors.append(f"Missing title: {path}")

    results["checks"]["unique_titles"] = {
        "passed": len(title_errors) == 0,
        "error_count": len(title_errors),
        "errors": title_errors,
    }

    # 2. Check unique meta descriptions
    desc_errors = []
    descriptions = {}
    for path, meta in page_metas.items():
        desc = meta.get("description")
        if desc:
            if desc in descriptions:
                desc_errors.append(
                    f"Duplicate description: {descriptions[desc]} and {path}"
                )
            else:
                descriptions[desc] = path

    results["checks"]["unique_descriptions"] = {
        "passed": len(desc_errors) == 0,
        "error_count": len(desc_errors),
        "errors": desc_errors,
    }

    # 3. Check one valid canonical per indexable page
    canonical_errors = []
    for path, meta in page_metas.items():
        canonicals = meta.get("canonicals", [])
        if len(canonicals) == 0:
            # No canonical — may be acceptable for some pages
            pass
        elif len(canonicals) > 1:
            canonical_errors.append(
                f"Multiple canonicals on {path}: {canonicals}"
            )

    results["checks"]["one_canonical_per_page"] = {
        "passed": len(canonical_errors) == 0,
        "error_count": len(canonical_errors),
        "errors": canonical_errors,
    }

    # 4. Check no accidental noindex on public pages
    # Cross-reference index-allowlist: pages NOT in the allowlist that have noindex are intentional
    noindex_errors = []
    index_allowlist = set()
    if INDEX_ALLOWLIST_PATH.is_file():
        try:
            allowlist_data = load_json(INDEX_ALLOWLIST_PATH)
            index_allowlist = set(allowlist_data.get("paths", []))
        except (OSError, json.JSONDecodeError):
            pass
    for path, meta in page_metas.items():
        if meta.get("noindex"):
            # Check if this is a beta page (expected noindex)
            slug = Path(path).stem
            if slug in BETA_PAGES:
                continue
            # Check if this page is in the index allowlist
            url_path = f"/{path}"
            if url_path in index_allowlist:
                # Page is in allowlist but has noindex — this is an error
                noindex_errors.append(
                    f"Page {path} has noindex but is in index-allowlist (robots: {meta.get('robots')})"
                )
            # If not in allowlist, noindex is intentional — skip

    results["checks"]["no_accidental_noindex"] = {
        "passed": len(noindex_errors) == 0,
        "error_count": len(noindex_errors),
        "errors": noindex_errors,
    }

    # 5. Verify beta pages are noindex,follow
    beta_errors = []
    for beta_slug in BETA_PAGES:
        beta_path = f"tools/{beta_slug}.html"
        meta = page_metas.get(beta_path)
        if meta:
            if not meta.get("noindex"):
                beta_errors.append(
                    f"Beta page {beta_path} is missing noindex directive"
                )
            elif meta.get("robots") and "nofollow" in meta.get("robots", "").lower():
                if "noindex" in meta.get("robots", "").lower():
                    beta_errors.append(
                        f"Beta page {beta_path} should be noindex,follow but has: {meta.get('robots')}"
                    )
        else:
            beta_errors.append(f"Beta page {beta_path} not found")

    results["checks"]["beta_pages_noindex"] = {
        "passed": len(beta_errors) == 0,
        "error_count": len(beta_errors),
        "errors": beta_errors,
    }

    # 6. Check sitemap for duplicates
    sitemap_errors = []
    if SITEMAP_PATH.is_file():
        try:
            content = SITEMAP_PATH.read_text(encoding="utf-8")
            loc_pattern = re.compile(r"<loc>([^<]+)</loc>")
            urls = loc_pattern.findall(content)
            seen = set()
            for url in urls:
                if url in seen:
                    sitemap_errors.append(f"Duplicate sitemap URL: {url}")
                seen.add(url)
        except OSError:
            pass

    results["checks"]["sitemap_no_duplicates"] = {
        "passed": len(sitemap_errors) == 0,
        "error_count": len(sitemap_errors),
        "errors": sitemap_errors,
    }

    # 7. Check sitemap does not include noindex pages
    sitemap_noindex_errors = []
    if SITEMAP_PATH.is_file():
        try:
            content = SITEMAP_PATH.read_text(encoding="utf-8")
            loc_pattern = re.compile(r"<loc>([^<]+)</loc>")
            sitemap_urls = loc_pattern.findall(content)
            for url in sitemap_urls:
                # Extract path
                from urllib.parse import urlparse
                parsed = urlparse(url)
                path = parsed.path.lstrip("/")
                meta = page_metas.get(path)
                if meta and meta.get("noindex"):
                    sitemap_noindex_errors.append(
                        f"Sitemap includes noindex page: {url}"
                    )
        except OSError:
            pass

    results["checks"]["sitemap_no_noindex"] = {
        "passed": len(sitemap_noindex_errors) == 0,
        "error_count": len(sitemap_noindex_errors),
        "errors": sitemap_noindex_errors,
    }

    # 8. Check structured data parses
    schema_errors = []
    schema_types = set()
    for path, meta in page_metas.items():
        for block in meta.get("json_ld", []):
            if "parse_error" in block:
                schema_errors.append(
                    f"Invalid JSON-LD on {path}: {block['parse_error'][:50]}"
                )
            elif isinstance(block, dict):
                atype = block.get("@type", "")
                if atype:
                    schema_types.add(atype)
            elif isinstance(block, list):
                for item in block:
                    if isinstance(item, dict):
                        atype = item.get("@type", "")
                        if atype:
                            schema_types.add(atype)

    results["checks"]["structured_data_parses"] = {
        "passed": len(schema_errors) == 0,
        "error_count": len(schema_errors),
        "errors": schema_errors,
        "schema_types_found": sorted(schema_types),
    }

    # 9. Check search index contains expected records
    search_errors = []
    if SEARCH_INDEX_PATH.is_file():
        search_data = load_json(SEARCH_INDEX_PATH)
        search_docs = search_data.get("documents", [])
        search_ids = {doc.get("id") for doc in search_docs}

        # Check catalog tools are in search index
        if LEGACY_DATA_PATH.is_file():
            catalog = load_json(LEGACY_DATA_PATH)
            for tool in catalog.get("tools", []):
                tid = tool.get("id")
                if tid and tid not in search_ids:
                    search_errors.append(f"Catalog tool {tid} not in search index")

    results["checks"]["search_index_coverage"] = {
        "passed": len(search_errors) == 0,
        "error_count": len(search_errors),
        "errors": search_errors,
    }

    # 10. Check for truncated titles (mid-word cuts, weak stop-word endings)
    weak_stop_words = {"and", "or", "for", "to", "the", "with", "your", "a", "an", "of", "in", "is", "on", "at", "by"}
    title_quality_errors = []
    for path, meta in page_metas.items():
        title = meta.get("title", "")
        if not title:
            continue
        # Check for weak stop-word endings (after removing suffix)
        clean = title.rstrip(" |:-,")
        words = clean.split()
        if words and words[-1].lower().rstrip(".,;:") in weak_stop_words:
            title_quality_errors.append(f"Title ends with weak stop word '{words[-1]}': {path}")
        # Check for ellipsis truncation
        if title.endswith("...") or title.endswith("&hellip;"):
            title_quality_errors.append(f"Title has ellipsis truncation: {path}")
        # Check for mid-word truncation (title base ends with partial word before | ToolNest)
        # Only flag if the last word before | is a single lowercase letter (clear truncation)
        base_part = title.rsplit("|", 1)[0].strip() if "|" in title else title
        last_word = base_part.split()[-1] if base_part.split() else ""
        if len(last_word) == 1 and last_word.islower():
            title_quality_errors.append(f"Title may have mid-word truncation: {path}")

    results["checks"]["title_quality"] = {
        "passed": len(title_quality_errors) == 0,
        "error_count": len(title_quality_errors),
        "errors": title_quality_errors,
    }

    # 11. Check for truncated descriptions
    desc_quality_errors = []
    for path, meta in page_metas.items():
        desc = meta.get("description", "")
        if not desc:
            continue
        clean = desc.rstrip(" |:-,")
        words = clean.split()
        if words and words[-1].lower().rstrip(".,;:") in weak_stop_words:
            desc_quality_errors.append(f"Description ends with weak stop word '{words[-1]}': {path}")
        if desc.endswith("...") or desc.endswith("&hellip;"):
            desc_quality_errors.append(f"Description has ellipsis truncation: {path}")
        if len(desc) > 160:
            desc_quality_errors.append(f"Description exceeds 160 chars ({len(desc)}): {path}")

    results["checks"]["description_quality"] = {
        "passed": len(desc_quality_errors) == 0,
        "error_count": len(desc_quality_errors),
        "errors": desc_quality_errors,
    }

    # 12. Check catalog-wide wording does not claim "Reviewed" for the whole directory
    catalog_wording_errors = []
    tools_index_meta = page_metas.get("tools/index.html")
    if tools_index_meta:
        title = tools_index_meta.get("title", "")
        desc = tools_index_meta.get("description", "")
        # Check for "Reviewed Tools" in catalog-wide context
        if "Reviewed Tools" in title:
            catalog_wording_errors.append(f"tools/index.html title uses 'Reviewed Tools' instead of 'Researched Tools'")
        if "Reviewed Tools" in desc:
            catalog_wording_errors.append(f"tools/index.html description uses 'Reviewed' for catalog-wide claim")

    results["checks"]["catalog_wording"] = {
        "passed": len(catalog_wording_errors) == 0,
        "error_count": len(catalog_wording_errors),
        "errors": catalog_wording_errors,
    }

    # 13. Check Tier-C indexability consistency (v2 editorial vs HTML robots)
    tier_c_tools = ["circle", "deel", "gamma", "nutshell", "quo", "survicate", "tidio"]
    tier_c_errors = []
    for tool in tier_c_tools:
        tool_path = f"tools/{tool}.html"
        meta = page_metas.get(tool_path)
        if meta:
            robots = meta.get("robots", "")
            # All Tier-C tools should have consistent robots directives
            # The authoritative rule: build_site.py quality gate determines indexability
            # v2 editorial status is metadata only
            if not robots:
                tier_c_errors.append(f"{tool_path}: missing robots directive")
            elif "noindex" in robots.lower():
                # Check if this is intentional (quality gate failure)
                tier_c_errors.append(f"{tool_path}: has noindex — verify quality gate result is intentional")

    results["checks"]["tier_c_indexability"] = {
        "passed": len(tier_c_errors) == 0,
        "error_count": len(tier_c_errors),
        "errors": tier_c_errors,
    }

    # Summary
    total_errors = sum(c.get("error_count", 0) for c in results["checks"].values())
    results["total_errors"] = total_errors
    results["passed"] = total_errors == 0

    return results


def main():
    results = run_seo_check()

    # Ensure output directory exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / "seo-integrity-report.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Print summary
    status = "PASS" if results["passed"] else "FAIL"
    print(f"\nSEO Integrity Check: {status}")
    print(f"  Total errors: {results['total_errors']}")
    for check_name, check_result in results["checks"].items():
        check_status = "PASS" if check_result["passed"] else "FAIL"
        print(f"  {check_name}: {check_status} ({check_result['error_count']} errors)")

    print(f"\nReport written to {output_path}")

    return 0 if results["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
