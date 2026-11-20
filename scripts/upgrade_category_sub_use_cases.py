#!/usr/bin/env python3
"""
Category Page Sub-Use-Case Upgrades — Phase 6

Add sub-use-case navigation routes to the 5 remaining Grade-B category pages:
- hosting
- image-generation
- marketing
- research
- sales

Each sub-use-case section provides neutral discovery routes without ranking winners.
Uses only existing tools.json data and existing comparison/alternatives/best-of pages.

No fabricated claims. No ranking. Pure navigation.
"""

import json
import re
from pathlib import Path


def load_json(path):
    with open(path) as f:
        return json.load(f)


def get_tools_in_category(category_name):
    """Get tools in a category from tools.json."""
    catalog = load_json("data/tools.json")
    return [t for t in catalog.get("tools", []) if t.get("cat") == category_name]


def get_best_of_page(category_slug):
    """Find best-of page for a category."""
    best_dir = Path("best")
    if not best_dir.exists():
        return None
    for f in best_dir.iterdir():
        if f.suffix == ".html" and f.name != "index.html":
            if category_slug in f.stem:
                return f"/best/{f.name}"
    return None


def get_comparisons_for_category(category_name):
    """Find comparison pages involving tools in this category."""
    catalog = load_json("data/tools.json")
    tool_ids = [t["id"] for t in catalog.get("tools", []) if t.get("cat") == category_name]

    compare_dir = Path("compare")
    comparisons = []
    if compare_dir.exists():
        for f in compare_dir.iterdir():
            if f.suffix == ".html" and f.name != "index.html":
                for tid in tool_ids:
                    if tid in f.stem:
                        comparisons.append(f"/compare/{f.name}")
                        break
    return list(set(comparisons))


def get_alternatives_for_category(category_name):
    """Find alternatives pages for tools in this category."""
    catalog = load_json("data/tools.json")
    tool_ids = [t["id"] for t in catalog.get("tools", []) if t.get("cat") == category_name]

    alternatives = []
    for tid in tool_ids:
        alt_path = Path(f"alternatives/{tid}-alternatives.html")
        if alt_path.exists():
            alternatives.append(f"/alternatives/{tid}-alternatives.html")
    return alternatives


def build_sub_use_cases(category_name):
    """Build sub-use-case HTML for a category based on tool data."""
    tools = get_tools_in_category(category_name)
    if not tools:
        return ""

    # Define sub-use-cases per category
    sub_use_cases = {
        "Hosting": [
            {"title": "Shared hosting for small sites", "description": "Budget-friendly hosting for personal sites and blogs with basic traffic."},
            {"title": "Website builder with hosting", "description": "All-in-one solutions where hosting and site building are bundled."},
            {"title": "Developer-focused hosting", "description": "Hosting with API access, CLI tools, and deployment automation."},
        ],
        "Image Generation": [
            {"title": "AI image creation from text", "description": "Generate images from text prompts for marketing, social media, or concept art."},
            {"title": "Background removal and editing", "description": "Quick background removal and simple image editing for product photos."},
            {"title": "Artistic image generation", "description": "High-quality artistic images for creative projects and design work."},
        ],
        "Marketing": [
            {"title": "Content creation and drafting", "description": "AI-assisted content writing for blogs, social media, and campaigns."},
            {"title": "Email marketing automation", "description": "Automated email campaigns, segmentation, and delivery tracking."},
            {"title": "Marketing analytics and insights", "description": "Track campaign performance and audience engagement."},
        ],
        "Research": [
            {"title": "AI-powered search and answers", "description": "Get sourced answers from AI search engines for quick research."},
            {"title": "Note-taking and knowledge management", "description": "Organize research findings, notes, and references."},
            {"title": "Audio and transcript research", "description": "Transcribe and search meeting recordings, podcasts, and interviews."},
        ],
        "Sales": [
            {"title": "CRM and pipeline management", "description": "Track leads, deals, and customer relationships."},
            {"title": "Email outreach and sequencing", "description": "Automated email sequences for sales outreach."},
            {"title": "Meeting and call recording", "description": "Record and analyze sales calls for insights and coaching."},
        ],
    }

    cases = sub_use_cases.get(category_name, [])
    if not cases:
        return ""

    # Build HTML
    html_parts = []
    html_parts.append('<section class="p-sec category-hub" id="sub-use-cases"><h2>Sub-use cases</h2>')
    html_parts.append('<p>These tools serve different use cases within this category. '
                      'Start with the use case that matches your goal, then compare trade-offs.</p>')
    html_parts.append('<div class="p-feats">')

    for case in cases:
        # Find tools that match this use case
        matching_tools = []
        for t in tools:
            best = t.get("best", "").lower()
            pros = " ".join(t.get("pros", [])).lower()
            # Simple keyword matching
            case_words = set(case["title"].lower().split())
            tool_words = set(best.split()) | set(pros.split())
            if case_words & tool_words:
                matching_tools.append(t)

        # If no keyword match, include all tools (neutral listing)
        if not matching_tools:
            matching_tools = tools[:3]

        tool_links = ""
        for t in matching_tools:
            tool_links += f'<a class="lk" href="/tools/{t["id"]}.html"><span class="lk-tx"><b>{t["name"]}</b><small>{t.get("best", "")}</small></span></a>'

        html_parts.append(f'<div class="p-feat"><h3>{case["title"]}</h3>')
        html_parts.append(f'<p>{case["description"]}</p>')
        html_parts.append(f'<div class="linkgrid">{tool_links}</div></div>')

    html_parts.append('</div></section>')

    return "\n".join(html_parts)


def upgrade_category_page(category_slug, category_name):
    """Add sub-use-case section to a category page."""
    page_path = f"category/{category_slug}.html"
    if not Path(page_path).exists():
        print(f"  Skipping {page_path}: not found")
        return False

    with open(page_path) as f:
        content = f.read()

    # Check if sub-use-cases already exists
    if 'id="sub-use-cases"' in content:
        print(f"  Skipping {page_path}: sub-use-cases already present")
        return False

    # Build sub-use-case HTML
    sub_html = build_sub_use_cases(category_name)
    if not sub_html:
        print(f"  Skipping {page_path}: no sub-use-cases defined")
        return False

    # Insert before the closing </main> tag
    # Find the position just before </main>
    main_close = content.rfind("</main>")
    if main_close == -1:
        print(f"  Skipping {page_path}: no </main> tag found")
        return False

    new_content = content[:main_close] + "\n" + sub_html + "\n" + content[main_close:]

    with open(page_path, "w") as f:
        f.write(new_content)

    print(f"  Upgraded {page_path}")
    return True


def main():
    print("=== Upgrading Category Pages with Sub-Use-Cases ===\n")

    # Map slugs to category names
    slug_to_name = {
        "hosting": "Hosting",
        "image-generation": "Image Generation",
        "marketing": "Marketing",
        "research": "Research",
        "sales": "Sales",
    }

    upgraded = 0
    for slug, name in slug_to_name.items():
        if upgrade_category_page(slug, name):
            upgraded += 1

    print(f"\n=== Upgraded {upgraded} category pages ===")


if __name__ == "__main__":
    main()
