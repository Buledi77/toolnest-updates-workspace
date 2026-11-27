#!/usr/bin/env python3
"""Regression tests for the strict parser-based head validator."""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_head_strict import validate  # noqa: E402

HEAD = """<head>
<title>Test</title>
<meta name="description" content="A test page description that is long enough.">
<link rel="canonical" href="https://www.toolnestai.tech/test.html">
<meta property="og:url" content="https://www.toolnestai.tech/test.html">
<meta property="og:title" content="Test">
</head>"""


def page(head: str) -> str:
    return f"<!doctype html><html lang=\"en\">{head}<body>ok</body></html>"


class StrictHeadTests(unittest.TestCase):
    def test_real_site_passes(self):
        self.assertEqual(validate(ROOT), [])

    def _errors(self, html: str):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "test.html").write_text(html, encoding="utf-8")
            return validate(tmp)

    def test_valid_page_passes(self):
        self.assertEqual(self._errors(page(HEAD)), [])

    def test_missing_canonical_reported(self):
        errors = self._errors(page(HEAD.replace('<link rel="canonical"', '<link rel="alternate"')))
        self.assertTrue(any("exactly 1 canonical" in e for e in errors), errors)

    def test_wrong_host_reported(self):
        bad = HEAD.replace("https://www.toolnestai.tech/test.html", "https://example.com/test.html")
        errors = self._errors(page(bad))
        self.assertTrue(any("canonical must be" in e for e in errors), errors)

    def test_og_url_mismatch_reported(self):
        bad = HEAD.replace('<meta property="og:url" content="https://www.toolnestai.tech/test.html">',
                           '<meta property="og:url" content="https://www.toolnestai.tech/other.html">')
        errors = self._errors(page(bad))
        self.assertTrue(any("og:url" in e and "canonical" in e for e in errors), errors)

    def test_unclosed_meta_reported(self):
        bad = HEAD.replace('content="A test page description that is long enough.">',
                           'content="A test page description that is long enough."')
        errors = self._errors(page(bad))
        # html5lib swallows the following <link> into the unclosed meta, so the
        # missing-canonical error is the correct observable symptom.
        self.assertTrue(any("canonical" in e for e in errors), errors)

    def test_noindex_page_exempt_from_canonical(self):
        noindex = HEAD.replace("<title>", '<meta name="robots" content="noindex,follow"><title>')
        noindex = noindex.replace('<link rel="canonical"', '<link rel="alternate"')
        errors = self._errors(page(noindex))
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
