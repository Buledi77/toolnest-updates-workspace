#!/usr/bin/env python3
"""Tests for the logo asset validator."""

import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_logos import validate  # noqa: E402


def png_bytes(width: int, height: int) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">II", width, height) + b"\x08\x06\x00\x00\x00"
    return signature + struct.pack(">I", len(ihdr)) + b"IHDR" + ihdr


def page(body: str) -> str:
    return f"<!doctype html><html><head><title>t</title></head><body>{body}</body></html>"


class LogoValidationTests(unittest.TestCase):
    def test_real_site_has_no_logo_errors(self):
        errors, _warnings = validate(ROOT)
        self.assertEqual(errors, [])

    def test_missing_logo_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "page.html"
            path.write_text(page('<img src="/assets/logos/nope.png" alt="">'), encoding="utf-8")
            errors, _ = validate(tmp)
            self.assertTrue(any("missing logo asset" in e for e in errors), errors)

    def test_empty_tile_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            category = Path(tmp) / "category"
            category.mkdir()
            (category / "dev.html").write_text(
                page('<div class="tile" aria-hidden="true"></div>'), encoding="utf-8"
            )
            errors, _ = validate(tmp)
            self.assertTrue(any("empty logo tile" in e for e in errors), errors)

    def test_small_logo_is_a_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            logos = Path(tmp) / "assets" / "logos"
            logos.mkdir(parents=True)
            (logos / "small.png").write_bytes(png_bytes(48, 48))
            (Path(tmp) / "page.html").write_text(
                page('<img src="/assets/logos/small.png" alt="">'), encoding="utf-8"
            )
            errors, warnings = validate(tmp)
            self.assertEqual(errors, [])
            self.assertTrue(any("below the 96px guideline" in w for w in warnings), warnings)

    def test_comparison_without_logo_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            compare = Path(tmp) / "compare"
            compare.mkdir()
            (compare / "a-vs-b.html").write_text(page("<h1>A vs B</h1>"), encoding="utf-8")
            errors, _ = validate(tmp)
            self.assertTrue(any("no tool logos" in e for e in errors), errors)

    def test_noindex_comparison_may_omit_logos(self):
        with tempfile.TemporaryDirectory() as tmp:
            compare = Path(tmp) / "compare"
            compare.mkdir()
            (compare / "a-vs-b.html").write_text(
                page('<meta name="robots" content="noindex,follow"><h1>A vs B</h1>'),
                encoding="utf-8",
            )
            errors, _ = validate(tmp)
            self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
