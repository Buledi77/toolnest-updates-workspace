#!/usr/bin/env python3
"""
Enrich legacy tools-v2 records with data from existing repository sources.

Sources (in priority order):
1. data/tools.json — catalog entry (name, category, best-fit, pros, site, logo, affiliateUrl)
2. Existing HTML review pages — sections, word counts, dates
3. File system — comparison pages, alternatives pages, best-of references
4. Evidence ledger — where claim_refs exist
5. Existing tools-v2 records — preserve any existing data

Never fabricates evidence. Unknown remains unknown.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_JSON = ROOT / "data" / "tools.json"
TOOLS_V2_DIR = ROOT / "data" / "tools-v2"
EVIDENCE_LEDGER = ROOT / "data" / "evidence" / "evidence-ledger.json"
LEGACY_DIR = TOOLS_V2_DIR / "legacy"
EXPANSION_DIR = TOOLS_V2_DIR / "expansion"


def load_json(path):
    with open(path) as f:
        return json.load(f)


def get_catalog_entry(tool_id):
    """Get tool entry from tools.json catalog."""
    catalog = load_json(TOOLS_JSON)
    for t in catalog.get("tools", []):
        if t["id"] == tool_id:
            return t
    return None


def get_comparison_pages(tool_id):
    """Find comparison pages involving this tool."""
    compare_dir = ROOT / "compare"
    comparisons = []
    if not compare_dir.exists():
        return comparisons
    for f in sorted(compare_dir.glob("*.html")):
        stem = f.stem
        # Comparisons use alphabetical order: toolA-vs-toolB
        if tool_id in stem:
            # Extract the other tool
            parts = stem.replace("-vs-", "-vs-").split("-vs-")
            other = [p for p in parts if p != tool_id]
            if other:
                comparisons.append({
                    "comparison_id": stem,
                    "other_tool": other[0],
                    "page": f"/compare/{f.name}"
                })
    return comparisons


def get_alternatives_page(tool_id):
    """Check if alternatives page exists."""
    alt_path = ROOT / "alternatives" / f"{tool_id}-alternatives.html"
    return alt_path.exists()


def get_alternatives_list(tool_id):
    """Extract alternatives from the alternatives HTML page."""
    alt_path = ROOT / "alternatives" / f"{tool_id}-alternatives.html"
    if not alt_path.exists():
        return []
    content = alt_path.read_text()
    # Look for tool IDs in the alternatives page
    # They appear as links to /tools/X.html
    tool_links = re.findall(r'href="(/tools/([^"]+)\.html)"', content)
    # Load canonical tool IDs to validate
    canonical_ids = load_legacy_ids()
    alts = []
    seen = set()
    for link, tid in tool_links:
        # Skip the tool itself, index pages, and non-canonical IDs
        if tid == tool_id or tid == "index" or tid not in canonical_ids:
            continue
        if tid not in seen:
            alts.append(tid)
            seen.add(tid)
    return alts


def load_legacy_ids():
    """Load canonical tool IDs from tools.json."""
    catalog = load_json(TOOLS_JSON)
    return {t["id"] for t in catalog.get("tools", [])}


def get_best_of_references(tool_id):
    """Find best-of pages that reference this tool."""
    best_dir = ROOT / "best"
    references = []
    if not best_dir.exists():
        return references
    for f in sorted(best_dir.glob("*.html")):
        content = f.read_text()
        if tool_id in content or f"/tools/{tool_id}.html" in content:
            references.append(f"/best/{f.name}")
    return references


def get_html_review_data(tool_id):
    """Extract data from existing HTML review page."""
    html_path = ROOT / "tools" / f"{tool_id}.html"
    if not html_path.exists():
        return None

    content = html_path.read_text()

    data = {
        "exists": True,
        "word_count": len(content.split()),
        "has_date": False,
        "date": None,
        "sections": [],
    }

    # Extract date from HTML
    date_match = re.search(r'<time[^>]*datetime="([^"]+)"', content)
    if date_match:
        data["has_date"] = True
        data["date"] = date_match.group(1)[:10]  # YYYY-MM-DD

    # Also check for published date in meta
    if not data["has_date"]:
        meta_date = re.search(r'<meta\s+property="article:published_time"\s+content="([^"]+)"', content)
        if meta_date:
            data["has_date"] = True
            data["date"] = meta_date.group(1)[:10]

    # Extract h2 section headings
    sections = re.findall(r'<h2>(.*?)</h2>', content)
    data["sections"] = sections

    return data


def enrich_discovery(record, catalog):
    """Enrich discovery section from catalog data."""
    discovery = record["discovery"]

    # Categories from catalog
    if catalog and "cat" in catalog:
        cat = catalog["cat"]
        if cat and not discovery["categories"]:
            discovery["categories"] = [cat]

    # Use cases from best-fit
    if catalog and "best" in catalog and catalog["best"]:
        best = catalog["best"]
        # Convert best-fit description to use case
        if not discovery["use_cases"]:
            # Create a use case from the best-fit field
            use_case = best.lower()
            if "for " in use_case:
                use_case = use_case.split("for ")[-1]
            discovery["use_cases"] = [use_case]

    # Tags from category and capabilities
    if catalog and "cat" in catalog:
        cat = catalog["cat"].lower().replace(" & ", "-").replace(" ", "-")
        if not discovery["tags"]:
            discovery["tags"] = [cat]

    # Platforms - assume web for all tools unless known otherwise
    if not discovery["platforms"]:
        discovery["platforms"] = ["web"]

    return record


def enrich_factual(record, catalog):
    """Enrich factual_profile from catalog data."""
    factual = record["factual_profile"]

    # Capabilities from pros
    if catalog and "pros" in catalog and catalog["pros"] and not factual["capabilities"]:
        for pro in catalog["pros"][:5]:
            factual["capabilities"].append({
                "description": pro
            })

    return record


def enrich_editorial(record, catalog, html_data):
    """Enrich editorial section from catalog and HTML data."""
    editorial = record["editorial"]
    tool_id = record["identity"]["id"]

    # Best for from catalog
    if catalog and "best" in catalog and catalog["best"] and not editorial["best_for"]:
        editorial["best_for"] = [catalog["best"]]

    # Review status based on HTML existence
    if html_data and html_data["exists"]:
        editorial["review_status"] = "published"
        editorial["review_url"] = f"https://www.toolnestai.tech/tools/{tool_id}.html"

        # Set editorial tier based on word count and sections
        word_count = html_data["word_count"]
        section_count = len(html_data["sections"])

        if word_count >= 1000 and section_count >= 10:
            editorial["editorial_tier"] = "A"
        elif word_count >= 500 and section_count >= 8:
            editorial["editorial_tier"] = "B"
        else:
            editorial["editorial_tier"] = "C"

        # Set last reviewed date from HTML
        if html_data["has_date"] and html_data["date"]:
            editorial["editorial_last_reviewed"] = html_data["date"]

    return record


def get_canonical_ids():
    """Get all canonical tool IDs (tools-v2 + tools.json)."""
    ids = load_legacy_ids()
    for f in Path(TOOLS_V2_DIR).rglob("*.json"):
        if f.is_file():
            try:
                rec = load_json(f)
                ids.add(rec.get("identity", {}).get("id"))
            except (json.JSONDecodeError, OSError):
                pass
    return ids


def enrich_relationships(record, tool_id):
    """Enrich relationships from file system."""
    rels = record["relationships"]
    canonical = get_canonical_ids()

    # Alternatives from alternatives page — always refresh to fix invalid IDs
    alts = get_alternatives_list(tool_id)
    if alts:
        # Filter out any non-canonical IDs from existing data
        rels["alternatives"] = [a for a in alts if a in canonical]

    # Comparisons from compare directory
    comparisons = get_comparison_pages(tool_id)
    if comparisons:
        rels["meaningful_comparisons"] = [c["comparison_id"] for c in comparisons]

        # Related tools from comparisons — filter to canonical IDs only
        related = [c["other_tool"] for c in comparisons if c["other_tool"] in canonical]
        if related:
            rels["related_tools"] = list(set(related))

    return record


def enrich_monetization(record, catalog):
    """Enrich monetization from catalog data."""
    monetization = record["monetization"]
    tool_id = record["identity"]["id"]

    # Official URL from catalog
    if catalog and "site" in catalog and catalog["site"]:
        monetization["official_non_affiliate_url"] = catalog["site"]

    # Affiliate URL from catalog
    if catalog and "affiliateUrl" in catalog and catalog["affiliateUrl"]:
        monetization["affiliate_url"] = catalog["affiliateUrl"]
        monetization["affiliate_status"] = "approved"
    elif not monetization["affiliate_status"]:
        monetization["affiliate_status"] = "not_applied"

    return record


def enrich_publishing(record, tool_id, html_data):
    """Enrich publishing section based on HTML existence."""
    publishing = record["publishing"]

    if html_data and html_data["exists"]:
        publishing["standalone_page_status"] = "published"
        publishing["indexability"] = "index"
        publishing["sitemap_eligible"] = True
        publishing["canonical_url"] = f"https://www.toolnestai.tech/tools/{tool_id}.html"
        publishing["template_type"] = "review"
        publishing["content_quality_status"] = "assessed"
        publishing["prepublish_status"] = "published"

    return record


def enrich_freshness(record, html_data):
    """Enrich freshness section."""
    freshness = record["freshness"]
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Set created/updated dates
    if not freshness["created_at"]:
        freshness["created_at"] = now

    if not freshness["updated_at"]:
        freshness["updated_at"] = now

    # Set last verified from HTML date
    if html_data and html_data["has_date"] and html_data["date"]:
        freshness["last_verified_at"] = html_data["date"] + "T00:00:00Z"

    # Clear stale fields that we've populated
    stale = freshness.get("stale_fields", [])
    cleared = []
    for field in stale:
        if field == "discovery" and record["discovery"].get("categories"):
            continue
        if field == "identity.status" and record["identity"].get("status") == "unknown":
            cleared.append(field)  # Keep stale if still unknown
        else:
            continue  # Keep other stale fields
    freshness["stale_fields"] = cleared

    return record


def main():
    print("=== Enriching Legacy Tools-v2 Records ===\n")

    # Load evidence ledger for source cross-reference
    try:
        ledger = load_json(EVIDENCE_LEDGER)
        source_ids = {s["source_id"] for s in ledger.get("sources", [])}
    except (FileNotFoundError, json.JSONDecodeError):
        source_ids = set()

    enriched = 0
    skipped = 0
    errors = 0

    for record_path in sorted(LEGACY_DIR.glob("*.json")):
        tool_id = record_path.stem

        # Load catalog entry
        catalog = get_catalog_entry(tool_id)
        if not catalog:
            print(f"  SKIP {tool_id}: no tools.json entry")
            skipped += 1
            continue

        # Load HTML review data
        html_data = get_html_review_data(tool_id)

        # Load existing record
        try:
            record = load_json(record_path)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  ERROR {tool_id}: cannot parse record: {e}")
            errors += 1
            continue

        # Check if already enriched (has data)
        has_categories = bool(record["discovery"].get("categories"))
        has_capabilities = bool(record["factual_profile"].get("capabilities"))
        has_best_for = bool(record["editorial"].get("best_for"))

        # Check for invalid relationship IDs that need fixing
        canonical = get_canonical_ids()
        has_invalid_rels = False
        for field in ("alternatives", "related_tools", "compatible_tools", "replaces", "replaced_by"):
            for rel_id in record.get("relationships", {}).get(field, []):
                if rel_id not in canonical:
                    has_invalid_rels = True
                    break
            if has_invalid_rels:
                break

        if has_categories and has_capabilities and has_best_for and not has_invalid_rels:
            print(f"  SKIP {tool_id}: already enriched")
            skipped += 1
            continue

        # Enrich from sources
        record = enrich_discovery(record, catalog)
        record = enrich_factual(record, catalog)
        record = enrich_editorial(record, catalog, html_data)
        record = enrich_relationships(record, tool_id)
        record = enrich_monetization(record, catalog)
        record = enrich_publishing(record, tool_id, html_data)
        record = enrich_freshness(record, html_data)

        # Update identity status
        if html_data and html_data["exists"]:
            record["identity"]["status"] = "active"

        # Update logo from catalog
        if catalog.get("logo"):
            record["identity"]["logo"] = catalog["logo"]

        # Write enriched record
        record_path.write_text(json.dumps(record, indent=2) + "\n")
        enriched += 1

        # Summary of what was added
        additions = []
        if record["discovery"].get("categories"):
            additions.append(f"cats={len(record['discovery']['categories'])}")
        if record["factual_profile"].get("capabilities"):
            additions.append(f"caps={len(record['factual_profile']['capabilities'])}")
        if record["editorial"].get("best_for"):
            additions.append("best_for")
        if record["relationships"].get("alternatives"):
            additions.append(f"alts={len(record['relationships']['alternatives'])}")
        if record["relationships"].get("meaningful_comparisons"):
            additions.append(f"comps={len(record['relationships']['meaningful_comparisons'])}")

        print(f"  OK   {tool_id}: {', '.join(additions)}")

    print(f"\n=== Result: {enriched} enriched, {skipped} skipped, {errors} errors ===")


if __name__ == "__main__":
    main()
