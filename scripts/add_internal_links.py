#!/usr/bin/env python3
"""Add contextual internal links to under-linked indexable pages.

Uses the catalog's category/alternatives/comparisons relationships so links
are genuinely relevant. Idempotent: skips links already present.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "tools-v1.json"


def load_tools() -> dict[str, dict]:
    d = json.loads(CATALOG.read_text(encoding="utf-8"))
    tools = d.get("tools", d) if isinstance(d, dict) else d
    return {t["id"]: t for t in tools}


def insert_links(path: Path, links: list[tuple[str, str]]) -> int:
    if not path.is_file() or not links:
        return 0
    text = path.read_text(encoding="utf-8")
    new = []
    for href, label in links:
        if href in text:
            continue
        new.append(f'<a href="{href}">{label}</a>')
    if not new:
        return 0
    block = ('<section class="p-sec" data-tn-related><h2>Related decisions</h2><p>'
             + " &middot; ".join(new) + ".</p></section>\n")
    idx = text.rfind("</main>")
    if idx < 0:
        idx = text.rfind("</footer>")
    if idx < 0:
        return 0
    path.write_text(text[:idx] + block + text[idx:], encoding="utf-8")
    return len(new)


def main() -> None:
    tools = load_tools()
    by_cat: dict[str, list[str]] = defaultdict(list)
    for tid, t in tools.items():
        by_cat[t.get("category", {}).get("slug") or t.get("cat", "").lower().replace(" ", "-")].append(tid)

    to_add: dict[str, list[tuple[str, str]]] = defaultdict(list)

    # 1. Every tool page: link from its category hub and best-of hub.
    for tid, t in tools.items():
        cat = t.get("category", {}).get("slug") or t.get("cat", "").lower().replace(" ", "-")
        label = t["name"]
        for source in (f"category/{cat}.html", "tools/index.html"):
            if (ROOT / source).is_file():
                to_add[source].append((f"/tools/{tid}.html", label))
        # alternatives hub for this tool
        alt = ROOT / "alternatives" / f"{tid}-alternatives.html"
        if alt.is_file():
            to_add[f"tools/{tid}.html"].append(
                (f"/alternatives/{tid}-alternatives.html", f"{label} alternatives")
            )
        # comparisons where this tool appears
        for other in (t.get("comparisons") or []):
            slug = other if isinstance(other, str) else other.get("id", "")
            for fwd, rev in ((f"{tid}-vs-{slug}", f"{slug}-vs-{tid}"),):
                for name in (fwd, rev):
                    p = ROOT / "compare" / f"{name}.html"
                    if p.is_file():
                        to_add[f"tools/{tid}.html"].append(
                            (f"/compare/{name}.html", f"{label} compared")
                        )

    # 2. Alternatives pages: link from their tool profile and category hub.
    for p in sorted((ROOT / "alternatives").glob("*-alternatives.html")):
        tid = p.stem.replace("-alternatives", "")
        if tid not in tools:
            continue
        t = tools[tid]
        cat = t.get("category", {}).get("slug") or t.get("cat", "").lower().replace(" ", "-")
        to_add[f"tools/{tid}.html"].append(
            (f"/alternatives/{tid}-alternatives.html", f"{t['name']} alternatives")
        )
        if (ROOT / "category" / f"{cat}.html").is_file():
            to_add[f"category/{cat}.html"].append(
                (f"/alternatives/{tid}-alternatives.html", f"{t['name']} alternatives")
            )

    # 3. Best-of pages: link from category hub and tools index.
    for p in sorted((ROOT / "best").glob("best-*.html")):
        if p.name == "index.html":
            continue
        title = re.search(r"<title>([^<]+)</title>", p.read_text(encoding="utf-8"), re.S)
        label = re.sub(r"\s*\|.*", "", title.group(1)).strip() if title else p.stem
        for source in ("tools/index.html", "index.html", "category/index.html"):
            to_add[source].append((f"/best/{p.name}", label))

    # 4. Utility + editorial pages from footer nav (sitewide already) plus explicit hubs.
    for src in ("index.html", "tools/index.html", "about.html"):
        to_add[src].append(("/tools/overlap-checker.html", "tool overlap checker"))
        to_add[src].append(("/tools/workflow-explorer.html", "workflow explorer"))
        to_add[src].append(("/corrections.html", "corrections log"))

    total = 0
    for source, links in sorted(to_add.items()):
        total += insert_links(ROOT / source, links)
    print(f"inserted {total} contextual links across {len(to_add)} hub pages")


if __name__ == "__main__":
    main()
