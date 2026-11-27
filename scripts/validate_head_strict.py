#!/usr/bin/env python3
"""Strict, parser-based validation of ToolNest <head> metadata.

Uses html5lib with the lxml treebuilder (not regex) so malformed markup,
unclosed tags and duplicate elements are handled the way a browser sees them.

Checks for every indexable page:
  * exactly one canonical, one og:url, one og:title, one description
  * canonical is an absolute https://www.toolnestai.tech URL matching own path
  * og:url equals the canonical
  * no <meta> content attribute contains a literal '<'
For every page (including noindex):
  * no <meta> content attribute contains a literal '<'

Usage: python scripts/validate_head_strict.py
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit
import warnings

import html5lib
from lxml import etree  # noqa: F401  (lxml treebuilder backend for html5lib)

warnings.filterwarnings("ignore", category=html5lib.constants.DataLossWarning)

ROOT = Path(__file__).resolve().parents[1]
HOST = "www.toolnestai.tech"
ORIGIN = f"https://{HOST}"
SKIP_DIRS = {
    ".git", ".github", ".junie", "backups", "data", "docs", "node_modules",
    "reports", "scripts", "tests", "__pycache__",
}
# Plain-text verification files are not pages.
SKIP_FILES = {"googlef7f3d54afb5d5344.html"}


def parse(text: str):
    return html5lib.parse(text, treebuilder="lxml", namespaceHTMLElements=False)


def meta_values(doc, key_attr: str, key: str) -> list[str]:
    hits = []
    for el in doc.xpath("//meta"):
        if (el.get(key_attr) or "").strip().lower() == key.lower():
            hits.append(el.get("content") or "")
    return hits


def is_noindex(doc) -> bool:
    return any("noindex" in value.lower() for value in meta_values(doc, "name", "robots"))


def expected_path(rel: Path) -> str:
    posix = rel.as_posix()
    return "/" if posix == "index.html" else f"/{posix}"


def validate_file(path: Path, root: Path) -> list[str]:
    errors: list[str] = []
    rel = path.relative_to(root)
    label = rel.as_posix()
    text = path.read_text(encoding="utf-8", errors="replace")
    doc = parse(text)

    for el in doc.xpath("//meta"):
        content = el.get("content")
        if content and "<" in content:
            errors.append(f"{label}: meta content contains a literal '<': {content[:60]!r}")

    if is_noindex(doc):
        return errors

    canonicals = [
        (el.get("href") or "").strip()
        for el in doc.xpath("//link")
        if "canonical" in (el.get("rel") or "").lower().split()
    ]
    if len(canonicals) != 1:
        errors.append(f"{label}: expected exactly 1 canonical, found {len(canonicals)}")
    else:
        href = canonicals[0]
        parts = urlsplit(href)
        if parts.scheme != "https" or parts.netloc != HOST:
            errors.append(f"{label}: canonical must be {ORIGIN} absolute URL, got {href!r}")
        if parts.query or parts.fragment:
            errors.append(f"{label}: canonical has query/fragment: {href!r}")
        want = expected_path(rel)
        if parts.path != want:
            errors.append(f"{label}: canonical path {parts.path!r} != {want!r}")

    for attr, key, label_text in (
        ("property", "og:url", "og:url"),
        ("property", "og:title", "og:title"),
        ("name", "description", "meta description"),
    ):
        values = meta_values(doc, attr, key)
        if len(values) != 1:
            errors.append(f"{label}: expected exactly 1 {label_text}, found {len(values)}")
        elif key == "og:url" and len(canonicals) == 1 and values[0].strip() != canonicals[0]:
            errors.append(f"{label}: og:url {values[0].strip()!r} != canonical {canonicals[0]!r}")
        elif not values[0].strip():
            errors.append(f"{label}: empty {label_text}")

    return errors


def iter_html(root: Path):
    for path in sorted(root.rglob("*.html")):
        if path.name in SKIP_FILES or set(path.relative_to(root).parts) & SKIP_DIRS:
            continue
        yield path


def validate(root: Path | str = ROOT) -> list[str]:
    root = Path(root)
    errors: list[str] = []
    for path in iter_html(root):
        errors.extend(validate_file(path, root))
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Strict head validation: FAIL")
        for e in errors:
            print(f"- {e}")
        return 1
    print(f"Strict head validation: PASS ({len(list(iter_html(ROOT)))} pages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
