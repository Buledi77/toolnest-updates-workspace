#!/usr/bin/env python3
"""Sitemap must contain exactly the indexable pages (no more, no less)."""

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_site import (  # noqa: E402
    MIN_INDEXABLE_WORDS, ROOT as SCRIPT_ROOT, SKIP_PAGES, page_route,
)
from content_metrics import measure, unique_marked_sections  # noqa: E402

NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def sitemap_paths() -> set[str]:
    tree = ET.parse(ROOT / "sitemap.xml")
    paths = set()
    for el in tree.findall(".//s:loc", NS):
        url = el.text.strip()
        path = url.replace("https://www.toolnestai.tech/", "")
        paths.add(path if path else "index.html")
    return paths


def indexable_paths() -> set[str]:
    allow = json.loads((ROOT / "data" / "index-allowlist.json").read_text(encoding="utf-8"))
    allow_set = set(allow.get("paths", [])) if isinstance(allow, dict) else set(allow)
    metrics = {}
    for path in SCRIPT_ROOT.rglob("*.html"):
        rel = path.relative_to(SCRIPT_ROOT).as_posix()
        if ".git" not in path.parts and rel not in {"404.html", *SKIP_PAGES}:
            metrics[rel] = measure(path.read_text(encoding="utf-8"))
    unique = unique_marked_sections(metrics)
    result = set()
    for rel, item in metrics.items():
        text = (SCRIPT_ROOT / rel).read_text(encoding="utf-8")
        if re.search(r'name=["\']robots["\'][^>]*noindex', text, re.I):
            continue
        if page_route(rel) in allow_set or (item.words >= MIN_INDEXABLE_WORDS and unique[rel]):
            result.add(rel)
    return result


def test_sitemap_equals_indexable_set():
    sitemap = sitemap_paths()
    indexable = indexable_paths()
    missing = sorted(indexable - sitemap)
    extra = sorted(sitemap - indexable)
    assert not missing and not extra, (
        f"sitemap/indexable mismatch: missing={len(missing)} {missing[:10]} "
        f"extra={len(extra)} {extra[:10]}"
    )
