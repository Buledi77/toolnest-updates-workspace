#!/usr/bin/env python3
"""Audit repeated-bullet findings across all HTML pages.

Scans every HTML page, extracts repeated <li> bullets, and classifies each
finding into one of the known root causes:

  TEMPLATE_REPETITION  — Generic bullets from alternatives page templates
  GENERATOR_BUG        — Duplicate section blocks causing repeated nav/TOC/trust-strip bullets
  CROSS_SECTION_REDUNDANCY — Same capability bullets in best-for AND pros-cons sections
  NAV_COLLISION        — Navigation <li> elements colliding with content bullets (false positive)

Outputs:
  reports/phase3/repeated-bullet-classification.json
  reports/phase3/repeated-bullet-classification.md
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports" / "phase3"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# The three generic bullets hardcoded in generate_missing_alternatives.py line 80
GENERIC_ALT_BULLETS = {
    "Different pricing structure",
    "Different feature focus",
    "Different workflow fit",
}

# Pages known to have duplicate <section> blocks (generator bug)
DUPLICATE_SECTION_PAGES = {
    "tools/beautifulai.html",
    "tools/close.html",
    "tools/consensus.html",
    "tools/freshdesk.html",
    "tools/manychat.html",
    "tools/netlify.html",
}


def strip_script_style(html: str) -> str:
    """Remove <script> and <style> blocks."""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text


def extract_sections(html: str) -> dict[str, list[str]]:
    """Extract <li> bullets grouped by surrounding section context.

    Returns a dict mapping section identifiers to lists of bullet text.
    Uses section ID when available, otherwise uses the section's header text.
    """
    text = strip_script_style(html)

    sections = {}

    # Find ALL section tags (with or without IDs)
    all_section_tags = re.compile(r'<section[^>]*>', re.IGNORECASE)
    for m in all_section_tags.finditer(text):
        tag = m.group(0)
        start = m.end()
        next_sec = re.search(r'<section\b', text[start:])
        section_content = text[start:start + (next_sec.start() if next_sec else len(text[start:]))]

        # Get section ID if present
        id_match = re.search(r'id=["\']([^"\']+)["\']', tag, re.IGNORECASE)
        sid = id_match.group(1) if id_match else None

        # If no ID, use the first h2/h3 header as the section key
        if sid is None:
            headers = re.findall(r'<h[23][^>]*>(.*?)</h[23]>', section_content, re.DOTALL)
            if headers:
                header_text = re.sub(r"\s+", " ", headers[0].strip()).strip().lower()
                # Create a normalized key from the header
                sid = re.sub(r"[^a-z0-9]+", "-", header_text).strip("-")
            else:
                # Skip sections with no ID and no header — they're structural wrappers
                continue

        bullets = re.findall(r"<li>(.*?)</li>", section_content, re.DOTALL)
        bullets_clean = [re.sub(r"\s+", " ", b.strip()).strip() for b in bullets if b.strip()]
        if bullets_clean:
            sections[sid] = bullets_clean

    # Also check for nav elements (breadcrumbs, TOC, etc.) that contain <li>
    nav_bullets = []
    nav_pattern = re.compile(r'<nav[^>]*>.*?</nav>', re.DOTALL | re.IGNORECASE)
    for m in nav_pattern.finditer(text):
        nav_content = m.group(0)
        bullets = re.findall(r"<li>(.*?)</li>", nav_content, re.DOTALL)
        bullets_clean = [re.sub(r"\s+", " ", b.strip()).strip() for b in bullets if b.strip()]
        nav_bullets.extend(bullets_clean)

    if nav_bullets:
        sections["__nav__"] = nav_bullets

    return sections


def find_repeated_bullets(html: str) -> list[dict]:
    """Find all repeated bullets in an HTML file and return finding dicts."""
    text = strip_script_style(html)
    bullets = re.findall(r"<li>(.*?)</li>", text, re.DOTALL)
    bullets_clean = [re.sub(r"\s+", " ", b.strip()).strip() for b in bullets if b.strip()]
    counts = Counter(bullets_clean)

    findings = []
    for bullet, count in counts.items():
        if count > 1:
            findings.append({
                "bullet": bullet,
                "count": count,
            })
    return findings


def classify_finding(rel_path: str, finding: dict, sections: dict[str, list[str]]) -> dict:
    """Classify a single repeated-bullet finding into a root cause category."""
    bullet = finding["bullet"]
    count = finding["count"]

    # Check for TEMPLATE_REPETITION (alternatives generic bullets)
    if bullet in GENERIC_ALT_BULLETS:
        return {
            "classification": "TEMPLATE_REPETITION",
            "category": "B",
            "root_source": "scripts/generate_missing_alternatives.py (line 80)",
            "generator": "generate_missing_alternatives.py",
            "user_impact": "Low — placeholder bullets with no product-specific value",
            "seo_impact": "Moderate — thin repetitive content across many pages",
            "safe_remediation": "Replace with tool-specific differentiation or remove bullets",
        }

    # Check for GENERATOR_BUG (duplicate section pages)
    if rel_path in DUPLICATE_SECTION_PAGES:
        # These pages have duplicate nav/TOC/trust-strip sections
        # The bullets are from duplicated structural elements
        return {
            "classification": "GENERATOR_BUG",
            "category": "E",
            "root_source": f"{rel_path} — duplicated <section> blocks in HTML source",
            "generator": "HTML generation produced duplicate section blocks",
            "user_impact": "Moderate — users see duplicate navigation and conflicting dates",
            "seo_impact": "Low — duplicate structured content",
            "safe_remediation": "Remove duplicate sections from the affected page",
        }

    # Check for NAV_COLLISION (nav <li> elements)
    if bullet.startswith("<a href=") or bullet.startswith("<svg") or bullet.startswith("<b>"):
        return {
            "classification": "NAV_COLLISION",
            "category": "D",
            "root_source": "Linter normalization treats nav <li> the same as content <li>",
            "generator": "lint_content.py bullet extraction",
            "user_impact": "None — false positive",
            "seo_impact": "None",
            "safe_remediation": "Exclude nav <li> elements from the linter's bullet check",
        }

    # Check for CROSS_SECTION_REDUNDANCY (capabilities in best-for AND pros-cons)
    # If the bullet appears in both best-for and pros-cons sections
    best_for_bullets = sections.get("best-for", [])
    pros_cons_bullets = sections.get("pros-cons", [])

    in_best_for = bullet in best_for_bullets
    in_pros_cons = bullet in pros_cons_bullets

    if in_best_for and in_pros_cons:
        return {
            "classification": "CROSS_SECTION_REDUNDANCY",
            "category": "G",
            "root_source": "Tool HTML template renders factual_profile.capabilities in both best-for and pros sections",
            "generator": "Tool page HTML template",
            "user_impact": "Moderate — readers see the same points twice on one page",
            "seo_impact": "Low — intra-page repetition",
            "safe_remediation": "Keep capabilities in one section only, or differentiate wording",
        }

    # Default: check if it's a tool page with cross-section pattern
    if rel_path.startswith("tools/"):
        # Check if the bullet appears in multiple sections
        section_occurrences = []
        for sid, sbullets in sections.items():
            if sid == "__nav__":
                continue
            if bullet in sbullets:
                section_occurrences.append(sid)

        if len(section_occurrences) >= 2:
            return {
                "classification": "CROSS_SECTION_REDUNDANCY",
                "category": "G",
                "root_source": f"Bullet appears in sections: {', '.join(section_occurrences)}",
                "generator": "Tool page HTML template",
                "user_impact": "Moderate — same point appears in multiple sections",
                "seo_impact": "Low — intra-page repetition",
                "safe_remediation": "Keep the bullet in one section, or reword for each context",
            }

    # Fallback
    return {
        "classification": "TRUE_DUPLICATE_SAME_PAGE",
        "category": "A",
        "root_source": "Unknown — manual review recommended",
        "generator": "Unknown",
        "user_impact": "Low — single page duplicate",
        "seo_impact": "Low",
        "safe_remediation": "Remove the duplicate bullet",
    }


def extract_tool_id(rel_path: str) -> str:
    """Extract tool slug from file path."""
    if rel_path.startswith("tools/"):
        return rel_path.replace("tools/", "").replace(".html", "")
    if rel_path.startswith("alternatives/"):
        return rel_path.replace("alternatives/", "").replace("-alternatives.html", "")
    return ""


def main():
    html_files = list(ROOT.rglob("*.html"))
    html_files = [
        p for p in html_files
        if ".git" not in p.parts
        and p.relative_to(ROOT).as_posix() not in {"404.html", "googlef7f3d54afb5d5344.html"}
    ]

    all_findings = []
    pages_with_findings = set()

    for path in sorted(html_files):
        rel = path.relative_to(ROOT).as_posix()
        content = path.read_text(encoding="utf-8", errors="replace")

        sections = extract_sections(content)
        findings = find_repeated_bullets(content)

        for f in findings:
            classification = classify_finding(rel, f, sections)
            entry = {
                "page": rel,
                "tool_id": extract_tool_id(rel),
                "repeated_text": f["bullet"][:120],
                "occurrence_count": f["count"],
                "sections_involved": list(sections.keys()),
                **classification,
            }
            all_findings.append(entry)
            pages_with_findings.add(rel)

    # Summary statistics
    classification_counts = Counter(f["classification"] for f in all_findings)
    category_counts = Counter(f["category"] for f in all_findings)

    # Group by classification for the report
    by_classification = defaultdict(list)
    for f in all_findings:
        by_classification[f["classification"]].append(f)

    # Build JSON report
    report = {
        "summary": {
            "total_findings": len(all_findings),
            "pages_affected": len(pages_with_findings),
            "total_pages_scanned": len(html_files),
            "classification_breakdown": dict(classification_counts),
            "category_breakdown": dict(category_counts),
        },
        "root_causes": {
            "TEMPLATE_REPETITION": {
                "description": "Generic bullets from alternatives page templates",
                "count": classification_counts.get("TEMPLATE_REPETITION", 0),
                "affected_pages": len(set(f["page"] for f in by_classification.get("TEMPLATE_REPETITION", []))),
                "root_source": "scripts/generate_missing_alternatives.py line 80",
            },
            "GENERATOR_BUG": {
                "description": "Duplicate section blocks in HTML source",
                "count": classification_counts.get("GENERATOR_BUG", 0),
                "affected_pages": len(set(f["page"] for f in by_classification.get("GENERATOR_BUG", []))),
                "root_source": "HTML generation produced duplicate <section> blocks",
            },
            "CROSS_SECTION_REDUNDANCY": {
                "description": "Same capability bullets in best-for AND pros-cons sections",
                "count": classification_counts.get("CROSS_SECTION_REDUNDANCY", 0),
                "affected_pages": len(set(f["page"] for f in by_classification.get("CROSS_SECTION_REDUNDANCY", []))),
                "root_source": "Tool HTML template renders capabilities in multiple sections",
            },
            "NAV_COLLISION": {
                "description": "Navigation <li> elements colliding with content bullets",
                "count": classification_counts.get("NAV_COLLISION", 0),
                "affected_pages": len(set(f["page"] for f in by_classification.get("NAV_COLLISION", []))),
                "root_source": "Linter treats nav <li> the same as content <li>",
            },
        },
        "findings": all_findings,
    }

    # Write JSON report
    json_path = REPORTS_DIR / "repeated-bullet-classification.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Written: {json_path}")

    # Build Markdown report
    md_lines = []
    md_lines.append("# Repeated-Bullet Classification Report\n")
    md_lines.append(f"**Generated:** 2026-11-22\n")
    md_lines.append(f"**Total findings:** {len(all_findings)}\n")
    md_lines.append(f"**Pages affected:** {len(pages_with_findings)} of {len(html_files)} pages scanned\n")
    md_lines.append("## Classification Summary\n")
    md_lines.append("| Classification | Count | Pages Affected |")
    md_lines.append("|---|---|---|")

    for cls_name in ["TEMPLATE_REPETITION", "GENERATOR_BUG", "CROSS_SECTION_REDUNDANCY", "NAV_COLLISION", "TRUE_DUPLICATE_SAME_PAGE"]:
        count = classification_counts.get(cls_name, 0)
        pages = len(set(f["page"] for f in by_classification.get(cls_name, [])))
        if count > 0:
            md_lines.append(f"| {cls_name} | {count} | {pages} |")

    md_lines.append("")
    md_lines.append("## Root Cause Details\n")

    # TEMPLATE_REPETITION
    md_lines.append("### Root Cause 1: TEMPLATE_REPETITION (Category B)\n")
    tr_findings = by_classification.get("TEMPLATE_REPETITION", [])
    tr_pages = sorted(set(f["page"] for f in tr_findings))
    md_lines.append(f"- **Findings:** {len(tr_findings)}")
    md_lines.append(f"- **Pages affected:** {len(tr_pages)}")
    md_lines.append(f"- **Root source:** `scripts/generate_missing_alternatives.py` line 80 hardcodes generic bullets")
    md_lines.append(f"- **Generic bullets:** \"Different pricing structure\", \"Different feature focus\", \"Different workflow fit\"")
    md_lines.append(f"- **User impact:** Low — placeholder bullets with no product-specific value")
    md_lines.append(f"- **SEO impact:** Moderate — thin repetitive content across {len(tr_pages)} pages")
    md_lines.append(f"- **Safe remediation:** Replace with tool-specific differentiation or remove bullets entirely")
    md_lines.append(f"- **Affected pages:**\n")
    for p in tr_pages:
        md_lines.append(f"  - `{p}`")
    md_lines.append("")

    # GENERATOR_BUG
    md_lines.append("### Root Cause 2: GENERATOR_BUG — Duplicate Sections (Category E)\n")
    gb_findings = by_classification.get("GENERATOR_BUG", [])
    gb_pages = sorted(set(f["page"] for f in gb_findings))
    md_lines.append(f"- **Findings:** {len(gb_findings)}")
    md_lines.append(f"- **Pages affected:** {len(gb_pages)}")
    md_lines.append(f"- **Root source:** Duplicated `<section>` blocks in HTML source")
    md_lines.append(f"- **User impact:** Moderate — users see duplicate navigation and conflicting dates")
    md_lines.append(f"- **SEO impact:** Low — duplicate structured content")
    md_lines.append(f"- **Safe remediation:** Remove duplicate sections from each affected page")
    md_lines.append(f"- **Affected pages:**\n")
    for p in gb_pages:
        page_findings = [f for f in gb_findings if f["page"] == p]
        bullets = [f["repeated_text"][:60] for f in page_findings[:3]]
        md_lines.append(f"  - `{p}` ({len(page_findings)} findings: {', '.join(bullets)})")
    md_lines.append("")

    # CROSS_SECTION_REDUNDANCY
    md_lines.append("### Root Cause 3: CROSS_SECTION_REDUNDANCY (Category G)\n")
    cs_findings = by_classification.get("CROSS_SECTION_REDUNDANCY", [])
    cs_pages = sorted(set(f["page"] for f in cs_findings))
    md_lines.append(f"- **Findings:** {len(cs_findings)}")
    md_lines.append(f"- **Pages affected:** {len(cs_pages)}")
    md_lines.append(f"- **Root source:** Tool HTML template renders `factual_profile.capabilities` in both best-for and pros sections")
    md_lines.append(f"- **User impact:** Moderate — readers see the same points twice on one page")
    md_lines.append(f"- **SEO impact:** Low — intra-page repetition")
    md_lines.append(f"- **Safe remediation:** Keep capabilities in one section only, or differentiate the wording")
    md_lines.append(f"- **Affected pages:**\n")
    for p in cs_pages:
        page_findings = [f for f in cs_findings if f["page"] == p]
        bullets = [f["repeated_text"][:50] for f in page_findings[:3]]
        md_lines.append(f"  - `{p}` ({len(page_findings)} findings)")
    md_lines.append("")

    # NAV_COLLISION
    md_lines.append("### Root Cause 4: NAV_COLLISION (Category D) — False Positives\n")
    nc_findings = by_classification.get("NAV_COLLISION", [])
    nc_pages = sorted(set(f["page"] for f in nc_findings))
    md_lines.append(f"- **Findings:** {len(nc_findings)}")
    md_lines.append(f"- **Pages affected:** {len(nc_pages)}")
    md_lines.append(f"- **Root source:** Linter normalization treats nav `<li>` elements the same as content `<li>` elements")
    md_lines.append(f"- **User impact:** None — false positive")
    md_lines.append(f"- **Safe remediation:** Exclude nav `<li>` elements from the linter's bullet check")
    md_lines.append(f"- **Affected pages:**\n")
    for p in nc_pages:
        page_findings = [f for f in nc_findings if f["page"] == p]
        md_lines.append(f"  - `{p}` ({len(page_findings)} findings)")
    md_lines.append("")

    # Other classifications
    other_cls = {k: v for k, v in by_classification.items()
                 if k not in ("TEMPLATE_REPETITION", "GENERATOR_BUG", "CROSS_SECTION_REDUNDANCY", "NAV_COLLISION")}
    if other_cls:
        md_lines.append("### Other Classifications\n")
        for cls_name, findings in other_cls.items():
            pages = sorted(set(f["page"] for f in findings))
            md_lines.append(f"#### {cls_name} — {len(findings)} findings across {len(pages)} pages\n")
            for p in pages:
                page_findings = [f for f in findings if f["page"] == p]
                md_lines.append(f"- `{p}`: {len(page_findings)} findings")
            md_lines.append("")

    # Verification section
    md_lines.append("## Verification\n")
    md_lines.append(f"- Total findings classified: {len(all_findings)}")
    expected = sum(classification_counts.values())
    md_lines.append(f"- Sum of classification counts: {expected}")
    md_lines.append(f"- Classification matches total: {'✓' if expected == len(all_findings) else '✗'}")
    md_lines.append("")

    md_content = "\n".join(md_lines)
    md_path = REPORTS_DIR / "repeated-bullet-classification.md"
    md_path.write_text(md_content, encoding="utf-8")
    print(f"Written: {md_path}")

    # Print summary
    print(f"\n=== Repeated-Bullet Classification Summary ===")
    print(f"Total findings: {len(all_findings)}")
    print(f"Pages affected: {len(pages_with_findings)}")
    print(f"Pages scanned: {len(html_files)}")
    print()
    for cls_name, count in sorted(classification_counts.items(), key=lambda x: -x[1]):
        pages = len(set(f["page"] for f in by_classification[cls_name]))
        print(f"  {cls_name}: {count} findings across {pages} pages")


if __name__ == "__main__":
    main()
