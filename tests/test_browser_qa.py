#!/usr/bin/env python3
"""Tests for the browser QA automation."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from browser_qa import (  # noqa: E402
    collect_html_pages,
    check_page_content,
    run_browser_qa,
    VIEWPORTS,
)


class TestCollectPages(unittest.TestCase):
    """Test HTML page collection."""

    def test_finds_pages(self):
        pages = collect_html_pages()
        self.assertGreater(len(pages), 0)

    def test_pages_have_urls(self):
        pages = collect_html_pages()
        for page in pages:
            self.assertIn("path", page)
            self.assertIn("url", page)
            # URLs can be relative paths (when BASE_URL is empty),
            # HTTP URLs (when run_browser_qa() server is active), or file:// URLs
            url = page["url"]
            self.assertTrue(
                url.startswith("http://") or url.startswith("file://") or url.startswith("/"),
                f"URL should be a valid path or URL: {url}"
            )

    def test_excludes_404(self):
        pages = collect_html_pages()
        paths = [p["path"] for p in pages]
        self.assertNotIn("404.html", paths)

    def test_excludes_node_modules(self):
        pages = collect_html_pages()
        paths = [p["path"] for p in pages]
        for path in paths:
            self.assertNotIn("node_modules", path)


class TestViewports(unittest.TestCase):
    """Test viewport configuration."""

    def test_viewport_count(self):
        self.assertEqual(len(VIEWPORTS), 6)

    def test_viewport_names(self):
        names = [v["name"] for v in VIEWPORTS]
        expected = [
            "mobile-small", "mobile-medium", "mobile-large",
            "tablet", "laptop", "desktop",
        ]
        self.assertEqual(names, expected)

    def test_viewport_widths(self):
        widths = [v["width"] for v in VIEWPORTS]
        self.assertEqual(widths, [320, 360, 390, 768, 1024, 1440])


class TestBrowserQaSample(unittest.TestCase):
    """Test browser QA with a small sample."""

    def test_sample_run(self):
        """Run browser QA on a small sample and verify report structure."""
        results = run_browser_qa(sample=2)
        self.assertIn("summary", results)
        self.assertIn("pages", results)
        self.assertEqual(results["total_pages"], 2)
        self.assertEqual(len(results["pages"]), 2)

    def test_report_has_viewport_results(self):
        """Each page should have viewport results."""
        results = run_browser_qa(sample=1)
        page = results["pages"][0]
        self.assertEqual(len(page["viewport_results"]), len(VIEWPORTS))

    def test_summary_counts(self):
        """Summary should have all expected fields."""
        results = run_browser_qa(sample=1)
        summary = results["summary"]
        expected_fields = [
            "total_issues", "high_severity", "medium_severity",
            "low_severity", "pages_with_errors", "console_errors",
            "network_errors",
        ]
        for field in expected_fields:
            self.assertIn(field, summary)


if __name__ == "__main__":
    unittest.main()
