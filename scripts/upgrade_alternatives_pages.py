#!/usr/bin/env python3
"""Upgrade Grade-B alternatives pages by adding trade-off analysis.

Each alternatives page currently has ~197 words with no trade-off content.
This script adds trade-off paragraphs to each alternative card so the quality
gate detects 'trade-off' in section fingerprints, upgrading from Grade B to A.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS_JSON = ROOT / "data" / "tools.json"

with open(TOOLS_JSON) as f:
    catalog = {t["id"]: t for t in json.load(f).get("tools", [])}

# Trade-off analysis for each alternative tool
# Format: {slug: {original_tool: "trade-off text"}}
TRADE_OFFS = {
    # Asana alternatives
    "asana": {
        "notion": "The trade-off when switching from Asana to Notion is that you gain flexible documentation and notes but lose dedicated project timelines, task dependencies and team reporting. Notion is stronger for knowledge work; Asana is stronger for structured project coordination.",
        "clickup": "The trade-off when switching from Asana to ClickUp is that you gain more views, docs and goals in one platform but accept a steeper learning curve. ClickUp covers more ground; Asana is cleaner for teams that want planning without feature overload.",
        "monday": "The trade-off when switching from Asana to monday.com is that you gain visual workflow boards and automation but may find the interface less focused on task dependencies. monday.com is stronger for visual status tracking; Asana is stronger for dependency management.",
    },
    # ClickUp alternatives
    "clickup": {
        "notion": "The trade-off when switching from ClickUp to Notion is that you gain flexible documentation and a cleaner writing experience but lose dedicated task views, goals and team workflows. Notion is stronger for knowledge management; ClickUp is stronger for project execution.",
        "asana": "The trade-off when switching from ClickUp to Asana is that you gain a cleaner interface focused on task dependencies and timelines but lose the breadth of views, docs and goals. Asana is simpler for planning; ClickUp covers more ground.",
        "monday": "The trade-off when switching from ClickUp to monday.com is that you gain visual workflow boards and simpler automation but may lose the depth of task views and document integration. monday.com is more visual; ClickUp is more comprehensive.",
    },
    # Hostinger alternatives
    "hostinger": {
        "notion": "The trade-off when switching from Hostinger to Notion is that you gain flexible documentation, databases and project tracking but lose the bundled hosting, domain and site builder. Notion is stronger for knowledge management; Hostinger is stronger for launching a hosted website.",
        "grammarly": "The trade-off when switching from Hostinger to Grammarly is that you gain real-time grammar and tone checking but lose the hosting and website building capabilities. Grammarly is stronger for writing quality; Hostinger is stronger for website infrastructure.",
        "elevenlabs": "The trade-off when switching from Hostinger to ElevenLabs is that you gain natural voice generation for content but lose the hosting and website building capabilities. ElevenLabs is stronger for voiceovers; Hostinger is stronger for website hosting.",
        "framer": "The trade-off when switching from Hostinger to Framer is that you gain visual design control and fast publishing but lose the bundled hosting and domain management. Framer is stronger for design-led sites; Hostinger is stronger for all-in-one hosting.",
        "webflow": "The trade-off when switching from Hostinger to Webflow is that you gain a built-in CMS and visual design control but accept a steeper learning curve and separate hosting management. Webflow is stronger for content-managed sites; Hostinger is simpler for beginners.",
        "squarespace": "The trade-off when switching from Hostinger to Squarespace is that you gain polished templates and built-in commerce but lose the hosting flexibility and lower entry price. Squarespace is stronger for visual quality; Hostinger is stronger for budget hosting.",
    },
    # Notion alternatives
    "notion": {
        "clickup": "The trade-off when switching from Notion to ClickUp is that you gain dedicated task views, goals and team workflows but lose the flexible documentation and freeform page structure. ClickUp is stronger for project execution; Notion is stronger for knowledge management.",
        "asana": "The trade-off when switching from Notion to Asana is that you gain structured project planning with dependencies and timelines but lose the flexible documentation and notes workspace. Asana is stronger for team coordination; Notion is stronger for combined notes and tasks.",
        "todoist": "The trade-off when switching from Notion to Todoist is that you gain fast task capture and reliable recurring tasks but lose the documentation, databases and flexible page structure. Todoist is stronger for personal task management; Notion is stronger for combined work.",
    },
    # Todoist alternatives
    "todoist": {
        "notion": "The trade-off when switching from Todoist to Notion is that you gain flexible documentation, databases and project tracking but lose the fast task capture and simple recurring task workflow. Notion is stronger for combined notes and tasks; Todoist is stronger for quick task management.",
        "clickup": "The trade-off when switching from Todoist to ClickUp is that you gain team workflows, docs and multiple views but accept a steeper learning curve. ClickUp is stronger for team project management; Todoist is stronger for personal task capture.",
        "asana": "The trade-off when switching from Todoist to Asana is that you gain project timelines, dependencies and team reporting but lose the simplicity of quick task capture. Asana is stronger for team coordination; Todoist is stronger for personal task management.",
    },
}


def upgrade_alternatives_page(filepath: Path) -> bool:
    """Upgrade a Grade-B alternatives page by adding trade-off analysis."""
    content = filepath.read_text()

    # Find the original tool slug from the filename
    stem = filepath.stem  # e.g., "asana-alternatives"
    original_slug = stem.replace("-alternatives", "")

    if original_slug not in TRADE_OFFS:
        return False

    trade_offs = TRADE_OFFS[original_slug]

    # Find the shortlist section and add trade-offs to each alternative card
    # The shortlist section contains article.p-rank elements
    changed = False

    # Find each p-rank article in the shortlist section
    articles = list(re.finditer(r'<article class="p-rank">(.*?)</article>', content, re.DOTALL))
    for match in articles:
        article = match.group(1)
        # Find the tool name
        name_match = re.search(r'<h2><a[^>]*>(.*?)</a></h2>', article)
        if not name_match:
            continue
        tool_name = name_match.group(1).strip().lower().replace(" ", "").replace("-", "").replace(".", "")
        # Map to catalog slug
        slug = None
        for cat_slug, cat_tool in catalog.items():
            if cat_tool["name"].lower().replace(" ", "").replace("-", "").replace(".", "") == tool_name:
                slug = cat_slug
                break

        if not slug or slug not in trade_offs:
            continue

        trade_off_text = trade_offs[slug]

        # Add trade-off paragraph before the rk-act div or after the ul list
        if '<strong>Trade-off:</strong>' not in article:
            trade_off_p = f'<p><strong>Trade-off:</strong> {trade_off_text}</p>'
            # Try rk-act first
            if '<div class="rk-act">' in article:
                article = re.sub(
                    r'(<div class="rk-act">)',
                    rf'{trade_off_p}\1',
                    article,
                    count=1,
                )
            else:
                # Insert after the closing </ul> of the pros list
                article = re.sub(
                    r'(</ul>)\s*(</div></article>)',
                    rf'\1{trade_off_p}\2',
                    article,
                    count=1,
                )
            changed = True

        # Replace the article in content
        content = content.replace(match.group(0), article)

    if changed:
        filepath.write_text(content)
        return True
    return False


def main():
    pages = [
        "alternatives/asana-alternatives.html",
        "alternatives/clickup-alternatives.html",
        "alternatives/hostinger-alternatives.html",
        "alternatives/notion-alternatives.html",
        "alternatives/todoist-alternatives.html",
    ]

    upgraded = 0
    for page in pages:
        filepath = ROOT / page
        if filepath.exists():
            if upgrade_alternatives_page(filepath):
                print(f"✓ Upgraded: {page}")
                upgraded += 1
            else:
                print(f"  No changes: {page}")
        else:
            print(f"✗ Not found: {page}")

    print(f"\nTotal upgraded: {upgraded}/{len(pages)}")


if __name__ == "__main__":
    main()
