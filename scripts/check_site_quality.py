#!/usr/bin/env python3
"""Read-only checks for local links, assets, canonicals, sitemap, and encoding."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from decision_graph_common import ROOT, print_result

HTML_DIRS = [ROOT]
SKIP_DIRS = {".git", ".github", "node_modules", "data", "reports", "docs", "scripts", "tests"}
SITEMAP_PATH = ROOT / "sitemap.xml"
URL_RE = re.compile(r"<loc>([^<]+)</loc>")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.assets = []
        self.canonicals = []
        self.h1_count = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag in {"img", "script", "source"} and attrs.get("src"):
            self.assets.append(attrs["src"])
        if tag == "link" and attrs.get("rel", "").lower() == "canonical":
            self.canonicals.append(attrs.get("href", ""))
        if tag == "h1":
            self.h1_count += 1


def html_files():
    for path in ROOT.rglob("*.html"):
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        yield path


def local_target(value, page):
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc or value.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    raw = parsed.path
    if not raw:
        return None
    if raw.startswith("/"):
        target = ROOT / raw.lstrip("/")
    else:
        target = page.parent / raw
    if target.is_dir():
        target = target / "index.html"
    return target


def validate():
    errors = []
    sitemap_urls = set(URL_RE.findall(SITEMAP_PATH.read_text(encoding="utf-8")))
    for page in html_files():
        try:
            parser = PageParser()
            parser.feed(page.read_text(encoding="utf-8"))
        except UnicodeDecodeError as exc:
            errors.append(f"{page.relative_to(ROOT)}: invalid UTF-8 ({exc})")
            continue
        if len(parser.canonicals) > 1:
            errors.append(f"{page.relative_to(ROOT)}: multiple canonical tags")
        for value in parser.links + parser.assets:
            target = local_target(value, page)
            if target is not None and not target.exists():
                errors.append(f"{page.relative_to(ROOT)}: missing local target {value}")
        relative = page.relative_to(ROOT).as_posix()
        verification_file = page.name.startswith("google") and page.name.endswith(".html")
        if relative != "404.html" and not verification_file and parser.h1_count != 1:
            errors.append(f"{page.relative_to(ROOT)}: expected one H1, found {parser.h1_count}")
        if parser.canonicals and not parser.canonicals[0].startswith(("https://", "http://")):
            errors.append(f"{page.relative_to(ROOT)}: canonical is not absolute")
    if not sitemap_urls:
        errors.append("sitemap.xml contains no URLs")
    return errors


if __name__ == "__main__":
    raise SystemExit(print_result("Site quality validation", validate()))
