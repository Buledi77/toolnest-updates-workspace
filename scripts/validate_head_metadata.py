#!/usr/bin/env python3
"""Deterministic validation of <head> metadata for ToolNest rendered HTML.

This validator exists because a P0 defect shipped nine unclosed ``<meta>``
tags (description, og:description, twitter:description) on three pages. An
unclosed tag can swallow the following canonical link and corrupt every
downstream crawler/social signal, so the checks here are intentionally
strict and deterministic.

For every indexable HTML page it enforces:

* exactly one ``<link rel="canonical">``
* the canonical is an absolute ``https://www.toolnestai.tech`` URL whose path
  matches the page's own path
* exactly one ``og:url`` and it matches the canonical
* exactly one non-empty ``description`` meta (50-160 characters)
* the required Open Graph and Twitter card tags
* no duplicate ``name``/``property`` meta keys
* no unclosed ``<meta>`` tags

``noindex`` pages are exempt from the canonical/description requirements but
still must not contain unclosed meta tags.

Usage:
    python scripts/validate_head_metadata.py
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE_HOST = "www.toolnestai.tech"
SITE_ORIGIN = f"https://{SITE_HOST}"

SKIP_DIRS = {
    ".git",
    ".github",
    ".junie",
    "backups",
    "data",
    "docs",
    "node_modules",
    "reports",
    "scripts",
    "tests",
    "__pycache__",
}

REQUIRED_OG = ("og:title", "og:description", "og:url", "og:image")
REQUIRED_TWITTER = (
    "twitter:card",
    "twitter:title",
    "twitter:description",
    "twitter:image",
)
DESCRIPTION_MIN = 50
DESCRIPTION_MAX = 160


class HeadParser(HTMLParser):
    """Collect ``<head>`` meta/link/title data without third-party deps."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_head = False
        self.metas: list[dict[str, str]] = []
        self.links: list[dict[str, str]] = []
        self.title: str | None = None
        self._in_title = False
        self._title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag == "head":
            self.in_head = True
            return
        if tag == "body":
            self.in_head = False
            return
        if not self.in_head:
            return
        if tag == "meta":
            self.metas.append({k.lower(): (v or "") for k, v in attrs})
        elif tag == "link":
            self.links.append({k.lower(): (v or "") for k, v in attrs})
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False
            self.title = "".join(self._title_parts).strip()

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)


def find_unclosed_meta(text: str) -> list[str]:
    """Return snippets for every ``<meta`` that never closes with ``>``."""
    unclosed: list[str] = []
    for match in re.finditer(r"<meta\b", text, re.IGNORECASE):
        rest = text[match.start():]
        close = rest.find(">")
        next_tag = rest.find("<", 1)
        if close == -1 or (next_tag != -1 and next_tag < close):
            snippet = " ".join(rest[:80].split())
            unclosed.append(snippet)
    return unclosed


def expected_path(relative: Path) -> str:
    posix = relative.as_posix()
    return "/" if posix == "index.html" else f"/{posix}"


def _meta_by_key(metas: list[dict[str, str]], key: str, value: str) -> list[dict[str, str]]:
    return [m for m in metas if m.get(key, "").lower() == value.lower()]


def _is_absolute_https(url: str) -> bool:
    parts = urlsplit(url)
    return parts.scheme == "https" and bool(parts.netloc)


def validate_file(path: Path, root: Path) -> list[str]:
    errors: list[str] = []
    rel = path.relative_to(root)
    label = rel.as_posix()
    text = path.read_text(encoding="utf-8", errors="replace")

    for snippet in find_unclosed_meta(text):
        errors.append(f"{label}: unclosed <meta> tag: {snippet}")

    parser = HeadParser()
    parser.feed(text)
    metas = parser.metas
    links = parser.links

    robots = _meta_by_key(metas, "name", "robots")
    noindex = any("noindex" in m.get("content", "").lower() for m in robots)

    # Duplicate detection applies to every page, indexable or not.
    for key in ("name", "property"):
        seen: dict[str, int] = {}
        for meta in metas:
            value = meta.get(key, "").strip().lower()
            if value:
                seen[value] = seen.get(value, 0) + 1
        for value, count in sorted(seen.items()):
            if count > 1:
                errors.append(
                    f"{label}: duplicate meta {key}=\"{value}\" ({count} occurrences)"
                )

    if noindex:
        return errors

    if not parser.title:
        errors.append(f"{label}: missing or empty <title>")

    canonicals = [l for l in links if "canonical" in l.get("rel", "").lower().split()]
    if len(canonicals) != 1:
        errors.append(
            f"{label}: expected exactly 1 canonical link, found {len(canonicals)}"
        )
    else:
        href = canonicals[0].get("href", "").strip()
        if not _is_absolute_https(href):
            errors.append(f"{label}: canonical is not an absolute https URL: {href!r}")
        else:
            parts = urlsplit(href)
            if parts.netloc.lower() != SITE_HOST:
                errors.append(
                    f"{label}: canonical host is {parts.netloc!r}, expected {SITE_HOST!r}"
                )
            if parts.query or parts.fragment:
                errors.append(
                    f"{label}: canonical must not contain a query or fragment: {href!r}"
                )
            want = expected_path(rel)
            if parts.path != want:
                errors.append(
                    f"{label}: canonical path {parts.path!r} does not match page path {want!r}"
                )

    og_urls = _meta_by_key(metas, "property", "og:url")
    if len(og_urls) != 1:
        errors.append(f"{label}: expected exactly 1 og:url, found {len(og_urls)}")
    else:
        og_url = og_urls[0].get("content", "").strip()
        if not _is_absolute_https(og_url):
            errors.append(f"{label}: og:url is not an absolute https URL: {og_url!r}")
        elif len(canonicals) == 1:
            href = canonicals[0].get("href", "").strip()
            if og_url != href:
                errors.append(f"{label}: og:url does not match canonical ({og_url!r} != {href!r})")

    descriptions = _meta_by_key(metas, "name", "description")
    if len(descriptions) != 1:
        errors.append(
            f"{label}: expected exactly 1 description meta, found {len(descriptions)}"
        )
    else:
        description = descriptions[0].get("content", "").strip()
        if not description:
            errors.append(f"{label}: description meta is empty")
        elif not (DESCRIPTION_MIN <= len(description) <= DESCRIPTION_MAX):
            errors.append(
                f"{label}: description length {len(description)} is outside "
                f"{DESCRIPTION_MIN}-{DESCRIPTION_MAX} characters"
            )

    for prop in REQUIRED_OG:
        if len(_meta_by_key(metas, "property", prop)) != 1:
            errors.append(f"{label}: missing or duplicate {prop} meta")

    for name in REQUIRED_TWITTER:
        if len(_meta_by_key(metas, "name", name)) != 1:
            errors.append(f"{label}: missing or duplicate {name} meta")

    return errors


def iter_html_files(root: Path):
    for path in sorted(root.rglob("*.html")):
        if set(path.relative_to(root).parts) & SKIP_DIRS:
            continue
        yield path


def validate(root: Path | str = ROOT) -> list[str]:
    """Return a list of human-readable errors (empty means the site passes)."""
    root = Path(root)
    errors: list[str] = []
    for path in iter_html_files(root):
        errors.extend(validate_file(path, root))
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Head metadata validation: FAIL")
        for message in errors:
            print(f"- {message}")
        return 1
    print("Head metadata validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
