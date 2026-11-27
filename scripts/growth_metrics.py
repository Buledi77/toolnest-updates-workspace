#!/usr/bin/env python3
"""Measure crawl/indexation quality of the built HTML corpus.

Outputs a JSON report with: indexable set, sitemap coverage, thin pages,
orphan pages, inbound-link counts, duplicate H2s, and title/description
lengths. Used for before/after growth-sprint reporting.

Usage: python scripts/growth_metrics.py [output.json]
"""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from content_metrics import measure, unique_marked_sections  # noqa: E402
from build_site import (  # noqa: E402
    MIN_INDEXABLE_WORDS, ROOT as SCRIPT_ROOT, SKIP_PAGES, page_route,
)

SKIP = {"scripts", "tests", "data", "reports", "docs", "node_modules", ".git"}
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
ORIGIN = "https://www.toolnestai.tech"


def html_files() -> list[Path]:
    return [p for p in sorted(ROOT.rglob("*.html"))
            if not set(p.relative_to(ROOT).parts) & SKIP
            and p.name != "googlef7f3d54afb5d5344.html"]


def sitemap_paths() -> set[str]:
    tree = ET.parse(ROOT / "sitemap.xml")
    return {el.text.strip().replace(ORIGIN + "/", "") or "index.html"
            for el in tree.findall(".//s:loc", NS)}


def internal_targets(text: str, source: str) -> set[str]:
    out = set()
    for href in re.findall(r'href="([^"]+)"', text):
        href = href.split("#", 1)[0].split("?", 1)[0]
        if not href or href.startswith(("http:", "https:", "mailto:", "javascript:", "data:")):
            continue
        path = href.lstrip("/") or "index.html"
        if path.endswith("/"):
            path += "index.html"
        out.add(path)
    return out


def measure_all() -> dict:
    pages = html_files()
    docs: dict[str, str] = {}
    metrics_map: dict[str, object] = {}
    words: dict[str, int] = {}
    noindex: set[str] = set()
    titles: dict[str, str] = {}
    descs: dict[str, str] = {}
    h2s: dict[str, list[str]] = {}
    links: dict[str, set[str]] = {}
    for p in pages:
        rel = p.relative_to(ROOT).as_posix()
        text = p.read_text(encoding="utf-8", errors="replace")
        docs[rel] = text
        metrics_map[rel] = measure(text)
        words[rel] = metrics_map[rel].words
        if re.search(r'name="robots"[^>]*noindex', text, re.I):
            noindex.add(rel)
        m = re.search(r"<title>([^<]+)</title>", text)
        titles[rel] = m.group(1).strip() if m else ""
        m = re.search(r'<meta name="description" content="([^"]*)"', text)
        descs[rel] = m.group(1).strip() if m else ""
        h2s[rel] = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h)).strip()
                    for h in re.findall(r"<h2[^>]*>(.*?)</h2>", text, re.S)]
        links[rel] = internal_targets(text, rel)

    allow = json.loads((ROOT / "data" / "index-allowlist.json").read_text(encoding="utf-8"))
    allow_set = set(allow.get("paths", []))
    unique = unique_marked_sections(metrics_map)
    indexable = {
        r for r in docs
        if r not in noindex
        and (page_route(r) in allow_set or (words[r] >= MIN_INDEXABLE_WORDS and unique[r]))
    }
    sitemap = sitemap_paths()

    inbound: dict[str, set[str]] = defaultdict(set)
    for src, targets in links.items():
        for tgt in targets:
            if tgt in docs:
                inbound[tgt].add(src)

    # crawlability: BFS from homepage over crawlable links (http 200 assumed local files)
    reachable = {"index.html"}
    q = deque(["index.html"])
    while q:
        cur = q.popleft()
        for tgt in links.get(cur, ()):
            if tgt in docs and tgt not in reachable:
                reachable.add(tgt)
                q.append(tgt)

    h2_counter = Counter(h for hs in h2s.values() for h in hs if h)
    dup_h2_pages = {r for r, hs in h2s.items() if any(h2_counter[h] > 1 for h in hs)}

    return {
        "html_pages": len(pages),
        "indexable": len(indexable),
        "noindex": len(noindex),
        "sitemap_urls": len(sitemap),
        "sitemap_missing_indexable": sorted(indexable - sitemap),
        "sitemap_extra": sorted(sitemap - indexable),
        "thin_under_300": sorted([r for r in indexable if words[r] < 300]),
        "orphans_under_5_inbound": sorted([r for r in indexable if len(inbound[r]) < 5]),
        "zero_inbound": sorted([r for r in indexable if not inbound[r]]),
        "unreachable_from_home": sorted([r for r in sitemap if r in docs and r not in reachable]),
        "titles_over_60": sorted([(r, len(titles[r])) for r in indexable if len(titles[r]) > 60]),
        "descs_over_155": sorted([(r, len(descs[r])) for r in indexable if len(descs[r]) > 155]),
        "pages_with_duplicate_h2": len(dup_h2_pages),
        "duplicate_h2_values": len([h for h, c in h2_counter.items() if c > 1]),
        "cat_links": sorted([r for r in docs if "/tools/index.html?cat=" in docs[r]]),
        "redirected_author_links": sorted([r for r in docs if "authors/abdul-muswir" in docs[r]]),
        "inbound_counts": {r: len(inbound[r]) for r in sorted(indexable)},
    }


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "quality" / "growth-metrics.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    report = measure_all()
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out}")
    for k in ("html_pages", "indexable", "noindex", "sitemap_urls", "thin_under_300",
              "orphans_under_5_inbound", "zero_inbound", "unreachable_from_home",
              "titles_over_60", "descs_over_155", "pages_with_duplicate_h2"):
        v = report[k]
        print(f"  {k}: {len(v) if isinstance(v, list) else v}")


if __name__ == "__main__":
    main()
