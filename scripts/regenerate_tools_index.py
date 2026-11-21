#!/usr/bin/env python3
"""Regenerate tools/index.html from the catalog so that:
- The noscript fallback lists ALL tools (not just 50)
- All hardcoded '50' counts are replaced with the actual catalog count
- JSON-LD, meta description, OG tags, and Article JSON-LD reflect the real count
- The catalog source (data/tools.json) is the single source of truth
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS_JSON = ROOT / "data" / "tools.json"
TOOLS_INDEX = ROOT / "tools" / "index.html"


def load_catalog():
    with open(TOOLS_JSON) as f:
        data = json.load(f)
    return data["tools"]


def html_escape(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def generate_noscript_list(tools):
    """Generate alphabetically sorted <li> items for the noscript fallback."""
    sorted_tools = sorted(tools, key=lambda t: t["name"].lower())
    items = []
    for t in sorted_tools:
        name = html_escape(t["name"])
        cat = html_escape(t["cat"])
        slug = t["id"]
        items.append(f'      <li><a href="/tools/{slug}.html">{name}</a> &mdash; {cat}</li>')
    return "\n".join(items)


def main():
    tools = load_catalog()
    count = len(tools)
    print(f"Catalog contains {count} tools")

    with open(TOOLS_INDEX) as f:
        html = f.read()

    # 1. Replace the noscript <ul> content (lines 124-175 area)
    # The noscript section has: <h2>All 50 tool reviews</h2> followed by <ul>...</ul>
    noscript_h2 = re.search(r'<h2>All \d+ tool reviews</h2>', html)
    if noscript_h2:
        html = html.replace(
            noscript_h2.group(0),
            f'<h2>All {count} tool reviews</h2>'
        )
        print(f"Updated noscript h2 to '{count} tool reviews'")

    # Replace the <ul>...</ul> block inside noscript with all tools
    ul_match = re.search(
        r'(<nav class="catlinks" aria-label="All tool reviews">.*?<ul>)\s*(.*?)\s*(</ul>)',
        html,
        re.DOTALL
    )
    if ul_match:
        new_list = generate_noscript_list(tools)
        replacement = f'{ul_match.group(1)}\n{new_list}\n{ul_match.group(3)}'
        html = html.replace(ul_match.group(0), replacement)
        print(f"Replaced noscript <ul> with {count} tool links")

    # 2. Fix JSON-LD SoftwareApplication - "AI Tools Directory: 50"
    html = re.sub(
        r'("name":\s*)"AI Tools Directory: \d+"',
        rf'\g<1>"AI Tools Directory: {count}"',
        html
    )
    print(f"Updated JSON-LD SoftwareApplication name to '{count}'")

    # 3. Fix meta description - "Search 50 AI and business tools"
    html = re.sub(
        r'("name="description" content=")Search \d+ AI and business tools',
        rf'\g<1>Search {count} AI and business tools',
        html
    )
    print(f"Updated meta description to '{count}'")

    # 4. Fix OG title - "50 Reviewed Tools"
    html = re.sub(
        r'("og:title" content="Software Tools Directory: )\d+ Reviewed Tools',
        rf'\g<1>{count} Reviewed Tools',
        html
    )
    print(f"Updated OG title to '{count}'")

    # 5. Fix OG description - "Search 50 AI and business tools"
    html = re.sub(
        r'("og:description" content=")Search \d+ AI and business tools',
        rf'\g<1>Search {count} AI and business tools',
        html
    )
    print(f"Updated OG description to '{count}'")

    # 6. Fix Twitter title - "50 Reviewed Tools"
    html = re.sub(
        r'("twitter:title" content="Software Tools Directory: )\d+ Reviewed Tools',
        rf'\g<1>{count} Reviewed Tools',
        html
    )
    print(f"Updated Twitter title to '{count}'")

    # 7. Fix Twitter description - "Search 50 AI and business tools"
    html = re.sub(
        r'("twitter:description" content=")Search \d+ AI and business tools',
        rf'\g<1>Search {count} AI and business tools',
        html
    )
    print(f"Updated Twitter description to '{count}'")

    # 8. Fix Article JSON-LD headline - "50 Reviewed Tools"
    html = re.sub(
        r'("headline":"Software Tools Directory: )\d+ Reviewed Tools',
        rf'\g<1>{count} Reviewed Tools',
        html
    )
    print(f"Updated Article JSON-LD headline to '{count}'")

    # 9. Fix Article JSON-LD description - "Search 50 AI and business tools"
    html = re.sub(
        r'("description":"Search )\d+ AI and business tools',
        rf'\g<1>{count} AI and business tools',
        html
    )
    print(f"Updated Article JSON-LD description to '{count}'")

    # 10. Fix <title> tag - "50 Reviewed Tools"
    html = re.sub(
        r'(<title>Software Tools Directory: )\d+ Reviewed Tools',
        rf'\g<1>{count} Reviewed Tools',
        html
    )
    print(f"Updated <title> tag to '{count}'")

    # Write the updated file
    with open(TOOLS_INDEX, "w") as f:
        f.write(html)

    print(f"\nDone. tools/index.html updated with {count} tools.")

    # Verify no remaining hardcoded "50" references that should be dynamic
    remaining = re.findall(r'50\s*(?:tool|Tool|Reviewed)', html)
    if remaining:
        print(f"WARNING: {len(remaining)} remaining '50 tool' references found:")
        for r in remaining:
            print(f"  - {r}")
    else:
        print("No remaining hardcoded '50 tool' references.")


if __name__ == "__main__":
    main()
