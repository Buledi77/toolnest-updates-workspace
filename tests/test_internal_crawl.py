#!/usr/bin/env python3
"""Every indexable page must have >=5 crawlable inbound links and be reachable."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from growth_metrics import measure_all  # noqa: E402


class InternalCrawlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = measure_all()

    def test_no_orphans(self):
        orphans = self.report["orphans_under_5_inbound"]
        self.assertEqual(orphans, [], f"pages with <5 inbound links: {orphans[:15]}")

    def test_sitemap_urls_reachable_from_homepage(self):
        self.assertEqual(self.report["unreachable_from_home"], [],
                         "sitemap URLs not reachable by internal crawl")

    def test_sitemap_equals_indexable(self):
        self.assertEqual(self.report["sitemap_missing_indexable"], [])
        self.assertEqual(self.report["sitemap_extra"], [])

    def test_titles_under_60_chars(self):
        self.assertEqual(self.report["titles_over_60"], [],
                         f"titles over 60 chars: {self.report['titles_over_60'][:10]}")

    def test_descriptions_under_155_chars(self):
        self.assertEqual(self.report["descs_over_155"], [],
                         f"descriptions over 155 chars: {self.report['descs_over_155'][:10]}")

    def test_h2s_unique(self):
        self.assertEqual(self.report["pages_with_duplicate_h2"], 0)


if __name__ == "__main__":
    unittest.main()
