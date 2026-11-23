"""Regression test: no page with noindex may appear in sitemap.xml.

This test verifies the architectural invariant that any page whose HTML
contains a <meta name="robots" content="...noindex..."> tag must NOT
be listed in sitemap.xml.

Failing this test means a search engine could be told to index a page
that the page itself asks search engines not to index.
"""

import glob
import os
import re
import xml.etree.ElementTree as ET

import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _find_noindex_pages():
    """Return a set of relative paths (e.g. 'tools/foo.html') that contain noindex."""
    noindex = set()
    pattern = re.compile(r'<meta\s+name="robots"[^>]*content="[^"]*noindex', re.IGNORECASE)
    for root, _dirs, files in os.walk(BASE_DIR):
        for fname in files:
            if not fname.endswith('.html'):
                continue
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, BASE_DIR)
            try:
                content = open(fpath, encoding='utf-8').read()
            except (OSError, UnicodeDecodeError):
                continue
            if pattern.search(content):
                noindex.add(rel)
    return noindex


def _sitemap_urls():
    """Return a set of path strings from sitemap.xml (e.g. '/tools/foo.html')."""
    sitemap_path = os.path.join(BASE_DIR, 'sitemap.xml')
    urls = set()
    if not os.path.exists(sitemap_path):
        return urls
    tree = ET.parse(sitemap_path)
    root = tree.getroot()
    ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    for loc_elem in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
        full_url = loc_elem.text or ''
        # Strip domain to get path
        m = re.search(r'https?://[^/]*(/.*)', full_url)
        if m:
            urls.add(m.group(1).rstrip('/'))
    return urls


class TestNoindexNotInSitemap:
    """No page marked noindex should appear in sitemap.xml."""

    def test_noindex_pages_exist(self):
        """Sanity check: at least one noindex page exists (beta pages)."""
        noindex = _find_noindex_pages()
        # We expect at least the beta pages to be noindex
        assert len(noindex) >= 1, "Expected at least one noindex page (e.g. beta pages)"

    def test_sitemap_exists(self):
        """Sanity check: sitemap.xml is present."""
        assert os.path.exists(os.path.join(BASE_DIR, 'sitemap.xml'))

    def test_noindex_not_in_sitemap(self):
        """Core invariant: no noindex page URL appears in sitemap.xml."""
        noindex_pages = _find_noindex_pages()
        sitemap_urls = _sitemap_urls()

        violations = []
        for page in noindex_pages:
            # Convert 'tools/foo.html' to '/tools/foo.html'
            url_path = '/' + page
            if url_path in sitemap_urls:
                violations.append(page)

        assert not violations, (
            f"The following noindex pages are incorrectly listed in sitemap.xml: "
            f"{', '.join(sorted(violations))}"
        )

    def test_beta_pages_are_noindex(self):
        """Beta pages (decision-engine, stack-analyzer) must remain noindex."""
        noindex = _find_noindex_pages()
        expected_beta = {'tools/decision-engine.html', 'tools/stack-analyzer.html'}
        missing = expected_beta - noindex
        assert not missing, (
            f"Expected these beta pages to be noindex, but they are not: "
            f"{', '.join(sorted(missing))}"
        )

    def test_batch_a_tools_are_indexable(self):
        """Batch A tools should NOT have noindex (they are indexable)."""
        noindex = _find_noindex_pages()
        batch_a = {
            'tools/cursor.html',
            'tools/github-copilot.html',
            'tools/lovable.html',
            'tools/bolt.html',
            'tools/heygen.html',
            'tools/ideogram.html',
        }
        wrongly_noindex = batch_a & noindex
        assert not wrongly_noindex, (
            f"Batch A tools should be indexable but have noindex: "
            f"{', '.join(sorted(wrongly_noindex))}"
        )

    def test_developer_tools_category_is_indexable(self):
        """Developer Tools category should NOT have noindex."""
        noindex = _find_noindex_pages()
        assert 'category/developer-tools.html' not in noindex, (
            "Developer Tools category should be indexable"
        )

    def test_comparison_pages_are_indexable(self):
        """New comparison pages should NOT have noindex."""
        noindex = _find_noindex_pages()
        comparisons = {
            'compare/cursor-vs-github-copilot.html',
            'compare/lovable-vs-bolt.html',
            'compare/heygen-vs-synthesia.html',
            'compare/ideogram-vs-midjourney.html',
        }
        wrongly_noindex = comparisons & noindex
        assert not wrongly_noindex, (
            f"Comparison pages should be indexable but have noindex: "
            f"{', '.join(sorted(wrongly_noindex))}"
        )

    def test_batch_a_in_sitemap(self):
        """Batch A tools should be listed in sitemap.xml."""
        sitemap_urls = _sitemap_urls()
        batch_a_paths = {
            '/tools/cursor.html',
            '/tools/github-copilot.html',
            '/tools/lovable.html',
            '/tools/bolt.html',
            '/tools/heygen.html',
            '/tools/ideogram.html',
        }
        missing = batch_a_paths - sitemap_urls
        assert not missing, (
            f"Batch A tools missing from sitemap.xml: "
            f"{', '.join(sorted(missing))}"
        )

    def test_developer_tools_category_in_sitemap(self):
        """Developer Tools category should be in sitemap.xml."""
        sitemap_urls = _sitemap_urls()
        assert '/category/developer-tools.html' in sitemap_urls, (
            "Developer Tools category missing from sitemap.xml"
        )

    def test_comparison_pages_in_sitemap(self):
        """New comparison pages should be in sitemap.xml."""
        sitemap_urls = _sitemap_urls()
        comparisons = {
            '/compare/cursor-vs-github-copilot.html',
            '/compare/lovable-vs-bolt.html',
            '/compare/heygen-vs-synthesia.html',
            '/compare/ideogram-vs-midjourney.html',
        }
        missing = comparisons - sitemap_urls
        assert not missing, (
            f"Comparison pages missing from sitemap.xml: "
            f"{', '.join(sorted(missing))}"
        )
