#!/usr/bin/env python3
"""Tests for the deterministic head-metadata validator.

Covers the P0 defect class (unclosed meta tags) plus missing, multiple and
malformed canonicals, og:url mismatches and description problems.
"""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_head_metadata import validate  # noqa: E402

DESCRIPTION = (
    "A deterministic test description that is comfortably longer than the "
    "fifty character minimum and shorter than the maximum."
)

CANONICAL = "https://www.toolnestai.tech/test.html"


def page(
    *,
    title: str = "Test page",
    description: str = DESCRIPTION,
    canonical: str | None = CANONICAL,
    og_url: str | None = CANONICAL,
    robots: str | None = None,
    lang: str | None = "en",
    extra_head: str = "",
) -> str:
    html_open = f'<html lang="{lang}">' if lang else "<html>"
    parts = [
        f"<!doctype html>{html_open}<head>",
        f"<title>{title}</title>",
    ]
    if description is not None:
        parts.append(f'<meta name="description" content="{description}">')
    if robots:
        parts.append(f'<meta name="robots" content="{robots}">')
    if canonical is not None:
        parts.append(f'<link rel="canonical" href="{canonical}">')
    parts.extend(
        [
            '<meta property="og:title" content="Test page">',
            f'<meta property="og:description" content="{DESCRIPTION}">',
        ]
    )
    if og_url is not None:
        parts.append(f'<meta property="og:url" content="{og_url}">')
    parts.extend(
        [
            '<meta property="og:image" content="https://www.toolnestai.tech/assets/og-default.png">',
            '<meta name="twitter:card" content="summary_large_image">',
            '<meta name="twitter:title" content="Test page">',
            f'<meta name="twitter:description" content="{DESCRIPTION}">',
            '<meta name="twitter:image" content="https://www.toolnestai.tech/assets/og-default.png">',
            extra_head,
            "</head><body></body></html>",
        ]
    )
    return "\n".join(parts)


class HeadMetadataTests(unittest.TestCase):
    def test_real_site_passes(self):
        self.assertEqual(validate(ROOT), [])

    def _errors_for(self, html: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.html"
            path.write_text(html, encoding="utf-8")
            return validate(tmp)

    def test_valid_page_passes(self):
        self.assertEqual(self._errors_for(page()), [])

    def test_missing_canonical_is_reported(self):
        errors = self._errors_for(page(canonical=None))
        self.assertTrue(any("canonical" in e for e in errors), errors)

    def test_multiple_canonicals_are_reported(self):
        html = page(extra_head=f'<link rel="canonical" href="{CANONICAL}">')
        errors = self._errors_for(html)
        self.assertTrue(any("exactly 1 canonical" in e for e in errors), errors)

    def test_relative_canonical_is_reported(self):
        errors = self._errors_for(page(canonical="/test.html"))
        self.assertTrue(any("absolute https" in e for e in errors), errors)

    def test_wrong_host_canonical_is_reported(self):
        errors = self._errors_for(page(canonical="https://example.com/test.html"))
        self.assertTrue(any("canonical host" in e for e in errors), errors)

    def test_canonical_path_mismatch_is_reported(self):
        errors = self._errors_for(page(canonical="https://www.toolnestai.tech/other.html"))
        self.assertTrue(any("does not match page path" in e for e in errors), errors)

    def test_og_url_mismatch_is_reported(self):
        errors = self._errors_for(
            page(og_url="https://www.toolnestai.tech/other.html")
        )
        self.assertTrue(any("og:url does not match canonical" in e for e in errors), errors)

    def test_unclosed_meta_is_reported(self):
        html = page().replace(
            f'<meta name="description" content="{DESCRIPTION}">',
            f'<meta name="description" content="{DESCRIPTION}"',
        )
        errors = self._errors_for(html)
        self.assertTrue(any("unclosed <meta>" in e for e in errors), errors)

    def test_missing_description_is_reported(self):
        errors = self._errors_for(page(description=None))
        self.assertTrue(any("description meta" in e for e in errors), errors)

    def test_short_description_is_reported(self):
        errors = self._errors_for(page(description="Too short."))
        self.assertTrue(any("description length" in e for e in errors), errors)

    def test_noindex_page_may_omit_canonical(self):
        errors = self._errors_for(page(canonical=None, robots="noindex,follow"))
        self.assertEqual(errors, [])

    def test_noindex_page_still_rejects_unclosed_meta(self):
        html = page(canonical=None, robots="noindex,follow").replace(
            f'<meta name="description" content="{DESCRIPTION}">',
            f'<meta name="description" content="{DESCRIPTION}"',
        )
        errors = self._errors_for(html)
        self.assertTrue(any("unclosed <meta>" in e for e in errors), errors)

    def test_missing_lang_is_reported(self):
        errors = self._errors_for(page(lang=None))
        self.assertTrue(any("<html lang>" in e for e in errors), errors)

    def test_noindex_page_still_requires_lang(self):
        errors = self._errors_for(page(canonical=None, robots="noindex,follow", lang=None))
        self.assertTrue(any("<html lang>" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
