#!/usr/bin/env python3
"""Phase 3F consistency tests.

Covers:
- Tier-C tool indexability consistency
- Shell leakage detection
- Metadata quality (truncation, stop-word endings)
- Catalog wording honesty
- P0 orphan contextual links
"""

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestTierCIndexability(unittest.TestCase):
    """Verify Tier-C tools have consistent robots directives."""

    tier_c_tools = ["circle", "deel", "gamma", "nutshell", "quo", "survicate", "tidio"]

    def test_tier_c_tools_have_robots_directive(self):
        """All Tier-C tools must have a robots meta tag."""
        for tool in self.tier_c_tools:
            html_path = ROOT / "tools" / f"{tool}.html"
            self.assertTrue(html_path.exists(), f"{tool}.html missing")
            content = html_path.read_text(encoding="utf-8")
            robots = re.search(
                r'name=["\']robots["\']\s+content=["\']([^"\']+)["\']',
                content, re.IGNORECASE
            )
            self.assertIsNotNone(robots, f"{tool}: missing robots directive")

    def test_tier_c_tools_consistent_with_quality_gate(self):
        """Tier-C tools with index,follow must pass the quality gate (words >= 450)."""
        for tool in self.tier_c_tools:
            html_path = ROOT / "tools" / f"{tool}.html"
            content = html_path.read_text(encoding="utf-8")
            robots = re.search(
                r'name=["\']robots["\']\s+content=["\']([^"\']+)["\']',
                content, re.IGNORECASE
            )
            if robots and "index" in robots.group(1).lower():
                # Indexable pages must have sufficient content
                words = len(content.split())
                self.assertGreaterEqual(
                    words, 450,
                    f"{tool}: indexable but only {words} words (below 450 threshold)"
                )


class TestShellLeakage(unittest.TestCase):
    """Detect shell variable leakage in generated HTML."""

    def _prose_content(self, html):
        """Strip code blocks, tables, and scripts to check only prose."""
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<pre[^>]*>.*?</pre>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<code[^>]*>.*?</code>", "", text, flags=re.DOTALL | re.IGNORECASE)
        # Tables contain pricing data that uses $X patterns — not shell leakage
        text = re.sub(r"<table[^>]*>.*?</table>", "", text, flags=re.DOTALL | re.IGNORECASE)
        return text

    def test_no_bin_bash_in_generated_html(self):
        """No /bin/bash in any generated HTML."""
        for html_file in ROOT.rglob("*.html"):
            if ".git" in html_file.parts:
                continue
            content = html_file.read_text(encoding="utf-8", errors="replace")
            self.assertNotIn(
                "/bin/bash", content,
                f"{html_file.relative_to(ROOT)}: /bin/bash found (shell variable corruption)"
            )

    def test_no_shell_positional_params_in_prose(self):
        """No $1-$9 shell positional parameters in prose (not in code blocks or pricing)."""
        # In this codebase, all $X patterns in prose are pricing ($8 a month, $19, $2.99, etc.)
        # Shell leakage would show as $1-$9 in non-pricing contexts, which is extremely rare.
        # The key indicator: shell variables appear as standalone $1 $2 etc. without pricing context.
        # Pricing is always preceded by a space/punctuation and followed by amount indicators.
        # Exclude: digits, commas, dashes, decimals, slashes, parens, spaces followed by price words
        pattern = re.compile(
            r"(?<!\w)\$([1-9])(?!\d|,|[\u2013\u2014\u2012\u2015\-]|\.\d|/|\)|"
            r"\s*(?:month|mo|yr|year|per|each|usd|seat|user|a\s|for\s|at\s))"
        )
        for html_file in ROOT.rglob("*.html"):
            if ".git" in html_file.parts:
                continue
            content = html_file.read_text(encoding="utf-8", errors="replace")
            prose = self._prose_content(content)
            matches = list(pattern.finditer(prose))
            self.assertEqual(
                len(matches), 0,
                f"{html_file.relative_to(ROOT)}: shell positional parameter found: {matches[0].group() if matches else 'unknown'}"
            )


class TestMetadataQuality(unittest.TestCase):
    """Check title and description quality."""

    weak_stop_words = {"and", "or", "for", "to", "the", "with", "your", "a", "an", "of", "in", "is", "on", "at", "by"}

    def _parse_meta(self, html_file):
        content = html_file.read_text(encoding="utf-8", errors="replace")
        title = re.search(r"<title>([^<]+)</title>", content, re.IGNORECASE)
        desc = re.search(
            r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']',
            content, re.IGNORECASE
        )
        return (title.group(1) if title else None, desc.group(1) if desc else None)

    def test_no_truncated_titles(self):
        """Titles must not end with weak stop words."""
        for html_file in ROOT.rglob("*.html"):
            if ".git" in html_file.parts:
                continue
            title, _ = self._parse_meta(html_file)
            if not title:
                continue
            clean = title.rstrip(" |:-,")
            words = clean.split()
            if words:
                last = words[-1].lower().rstrip(".,;:")
                self.assertNotIn(
                    last, self.weak_stop_words,
                    f"{html_file.relative_to(ROOT)}: title ends with stop word '{last}'"
                )

    def test_no_truncated_descriptions(self):
        """Descriptions must not end with weak stop words."""
        for html_file in ROOT.rglob("*.html"):
            if ".git" in html_file.parts:
                continue
            _, desc = self._parse_meta(html_file)
            if not desc:
                continue
            clean = desc.rstrip(" |:-,")
            words = clean.split()
            if words:
                last = words[-1].lower().rstrip(".,;:")
                self.assertNotIn(
                    last, self.weak_stop_words,
                    f"{html_file.relative_to(ROOT)}: description ends with stop word '{last}'"
                )

    def test_description_length(self):
        """Descriptions should not exceed 160 characters (soft limit, allow 165 for edge cases)."""
        for html_file in ROOT.rglob("*.html"):
            if ".git" in html_file.parts:
                continue
            _, desc = self._parse_meta(html_file)
            if desc and len(desc) > 165:
                self.fail(
                    f"{html_file.relative_to(ROOT)}: description too long ({len(desc)} chars)"
                )

    def test_no_ellipsis_truncation(self):
        """Titles and descriptions must not have ellipsis from truncation."""
        for html_file in ROOT.rglob("*.html"):
            if ".git" in html_file.parts:
                continue
            title, desc = self._parse_meta(html_file)
            if title:
                self.assertFalse(
                    title.endswith("...") or title.endswith("&hellip;"),
                    f"{html_file.relative_to(ROOT)}: title has ellipsis"
                )
            if desc:
                self.assertFalse(
                    desc.endswith("...") or desc.endswith("&hellip;"),
                    f"{html_file.relative_to(ROOT)}: description has ellipsis"
                )


class TestCatalogWording(unittest.TestCase):
    """Verify honest directory wording."""

    def test_tools_index_no_reviewed_claim(self):
        """tools/index.html must not claim 'Reviewed Tools' for the catalog."""
        path = ROOT / "tools" / "index.html"
        if not path.exists():
            self.skipTest("tools/index.html not found")
        content = path.read_text(encoding="utf-8")
        # Check title
        title = re.search(r"<title>([^<]+)</title>", content, re.IGNORECASE)
        if title:
            self.assertNotIn(
                "Reviewed Tools", title.group(1),
                "tools/index.html title should use 'Researched Tools'"
            )
        # Check H1
        h1 = re.search(r"<h1>([^<]+)</h1>", content, re.IGNORECASE)
        if h1:
            self.assertNotIn(
                "we have reviewed", h1.group(1).lower(),
                "tools/index.html H1 should not claim hands-on review"
            )


class TestP0Orphans(unittest.TestCase):
    """Verify P0 orphan tools have contextual links."""

    orphans = {
        "ueni": ["synthesia", "murf", "runway"],
        "trainual": ["notion", "connecteam", "deel"],
        "meetgeek": ["otter", "fireflies", "descript"],
    }

    def test_orphans_linked_from_alternatives(self):
        """Each orphan must be linked from at least one alternative's tool page."""
        for orphan, alternatives in self.orphans.items():
            found_link = False
            for alt in alternatives:
                alt_path = ROOT / "tools" / f"{alt}.html"
                if not alt_path.exists():
                    continue
                content = alt_path.read_text(encoding="utf-8")
                if f"/tools/{orphan}.html" in content:
                    found_link = True
                    break
            self.assertTrue(
                found_link,
                f"{orphan}: no contextual link found from any alternative ({alternatives})"
            )


if __name__ == "__main__":
    unittest.main()
