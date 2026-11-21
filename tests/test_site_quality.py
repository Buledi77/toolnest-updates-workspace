import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_site_quality import validate  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]


class SiteQualityTests(unittest.TestCase):
    def test_site_quality_has_no_errors(self):
        self.assertEqual(validate(), [])


class AlternativesQualityTests(unittest.TestCase):
    """Quality gates for alternatives pages."""

    def test_empty_alternatives_are_noindexed(self):
        """Alternatives pages with no real content should carry noindex."""
        for alt_file in sorted(ROOT.glob("alternatives/*.html")):
            if alt_file.name == "index.html":
                continue
            content = alt_file.read_text(encoding="utf-8")
            # Pages with only boilerplate and no tool links should be noindex
            tool_links = re.findall(r'href="/tools/[^/]+\.html"', content)
            if len(tool_links) == 0:
                self.assertIn(
                    "noindex",
                    content,
                    f"{alt_file.name}: empty alternatives page should be noindex",
                )

    def test_no_links_to_empty_alternative_stubs(self):
        """No page should link to an alternatives stub with no content."""
        # Build a set of alternatives pages that have real content (tool links)
        # index.html is a valid hub page, not a stub
        populated = {"index.html"}
        for alt_file in sorted(ROOT.glob("alternatives/*.html")):
            if alt_file.name == "index.html":
                continue
            content = alt_file.read_text(encoding="utf-8")
            tool_links = re.findall(r'href="/tools/[^/]+\.html"', content)
            if len(tool_links) > 0:
                populated.add(alt_file.name)

        # Check all HTML pages don't link to empty stubs
        # Only check static HTML links, not JS-generated dynamic links
        all_html = list(ROOT.rglob("*.html"))
        for html_file in all_html:
            if ".git" in html_file.parts:
                continue
            content = html_file.read_text(encoding="utf-8")
            # Strip script blocks to avoid matching JS template strings
            stripped = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
            for match in re.finditer(r'href="/alternatives/([^"]+)"', stripped):
                target = match.group(1)
                if target not in populated:
                    self.fail(
                        f"{html_file.relative_to(ROOT)} links to empty alternatives stub: {target}"
                    )

    def test_alternatives_link_targets_exist(self):
        """All alternatives page links should resolve to existing files."""
        for alt_file in sorted(ROOT.glob("alternatives/*.html")):
            if alt_file.name == "index.html":
                continue
            content = alt_file.read_text(encoding="utf-8")
            for match in re.finditer(r'href="/tools/([^"]+)"', content):
                target = match.group(1)
                target_path = ROOT / "tools" / target
                self.assertTrue(
                    target_path.exists(),
                    f"{alt_file.name}: link target does not exist: {target}",
                )


class PricingRegressionTests(unittest.TestCase):
    """Regression tests for pricing data integrity."""

    def test_pricing_corrections_survive_build(self):
        """The correction registry must remain valid JSON after rebuild."""
        registry_path = ROOT / "data" / "corrections" / "correction-registry.json"
        if registry_path.exists():
            content = registry_path.read_text(encoding="utf-8")
            data = json.loads(content)
            self.assertIn("corrections", data)
            self.assertIsInstance(data["corrections"], list)

    def test_needs_review_claims_not_shown_as_verified(self):
        """Pages marked needs_review must not display verified pricing claims."""
        # Check tools-v2 data for needs_review entries
        v2_dir = ROOT / "data" / "tools-v2"
        if not v2_dir.exists():
            self.skipTest("tools-v2 directory not found")
        for json_file in v2_dir.glob("*.json"):
            data = json.loads(json_file.read_text(encoding="utf-8"))
            quality = data.get("metadata", {}).get("content_quality_status", "")
            if quality == "needs_review":
                tool_name = json_file.stem
                html_path = ROOT / "tools" / f"{tool_name}.html"
                if html_path.exists():
                    content = html_path.read_text(encoding="utf-8")
                    # Should not claim verified pricing
                    self.assertNotIn(
                        "verified",
                        content.lower(),
                        f"{tool_name}.html: needs_review page should not claim verified data",
                    )


if __name__ == "__main__":
    unittest.main()
