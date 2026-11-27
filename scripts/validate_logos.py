#!/usr/bin/env python3
"""Validate logo assets referenced by ToolNest HTML.

Checks:
* every ``/assets/logos/...`` reference resolves to a real file (error)
* category cards do not ship empty logo tiles (error)
* referenced raster logos are at least 96px on their shortest side (warning)

The 96px threshold is a warning rather than an error because a small number
of legacy logos predate the rule. New or replaced logos should meet it.
"""

from __future__ import annotations

import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGO_MIN_PX = 96

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

LOGO_REF_RE = re.compile(r"/assets/logos/[^\"'\s>]+")
TILE_RE = re.compile(r'<div class="tile"[^>]*>(.*?)</div>', re.DOTALL)


def image_dimensions(path: Path) -> tuple[int, int] | None:
    """Return (width, height) for common raster/SVG formats, else None."""
    suffix = path.suffix.lower()
    try:
        data = path.read_bytes()
    except OSError:
        return None

    if suffix == ".png" and len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n":
        width, height = struct.unpack(">II", data[16:24])
        return width, height

    if suffix == ".gif" and len(data) >= 10 and data[:6] in (b"GIF87a", b"GIF89a"):
        width, height = struct.unpack("<HH", data[6:10])
        return width, height

    if suffix in {".jpg", ".jpeg"}:
        index = 2
        while index + 9 < len(data):
            if data[index] != 0xFF:
                index += 1
                continue
            marker = data[index + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                height, width = struct.unpack(">HH", data[index + 5:index + 9])
                return width, height
            if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                index += 2
                continue
            length = struct.unpack(">H", data[index + 2:index + 4])[0]
            index += 2 + length
        return None

    if suffix == ".svg":
        text = data.decode("utf-8", errors="replace")
        viewbox = re.search(r'viewBox=["\']\s*[-\d.]+\s+[-\d.]+\s+([\d.]+)\s+([\d.]+)', text)
        if viewbox:
            return int(float(viewbox.group(1))), int(float(viewbox.group(2)))
        width = re.search(r'\bwidth=["\']([\d.]+)', text)
        height = re.search(r'\bheight=["\']([\d.]+)', text)
        if width and height:
            return int(float(width.group(1))), int(float(height.group(1)))
        return None

    return None


def iter_html_files(root: Path):
    for path in sorted(root.rglob("*.html")):
        if set(path.relative_to(root).parts) & SKIP_DIRS:
            continue
        yield path


def validate(root: Path | str = ROOT) -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    root = Path(root)
    errors: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()

    for path in iter_html_files(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(root).as_posix()

        for ref in sorted(set(LOGO_REF_RE.findall(text))):
            if ref in seen:
                continue
            seen.add(ref)
            asset = root / ref.lstrip("/")
            if not asset.exists():
                errors.append(f"{rel}: missing logo asset {ref}")
                continue
            dimensions = image_dimensions(asset)
            if dimensions and min(dimensions) < LOGO_MIN_PX:
                warnings.append(
                    f"{ref}: {dimensions[0]}x{dimensions[1]} is below the "
                    f"{LOGO_MIN_PX}px guideline"
                )

        if path.parent.name == "category":
            for match in TILE_RE.finditer(text):
                inner = match.group(1).strip()
                if "<img" not in inner and not re.search(r"[A-Za-z0-9]", inner):
                    errors.append(f"{rel}: empty logo tile")

    return errors, sorted(set(warnings))


def main() -> int:
    errors, warnings = validate()
    for warning in warnings:
        print(f"warning: {warning}")
    if errors:
        print("Logo validation: FAIL")
        for message in errors:
            print(f"- {message}")
        return 1
    print(f"Logo validation: PASS ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
