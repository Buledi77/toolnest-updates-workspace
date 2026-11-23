import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from decision_graph_common import load_records  # noqa: E402
from directory_adapter import public_page_candidates, query, search  # noqa: E402


class DirectoryAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load_records()

    def test_search_finds_structured_expansion_record(self):
        result = search(self.records, "coding editor")
        self.assertIn("cursor", [record["identity"]["id"] for record in result])

    def test_query_filters_sorts_and_paginates(self):
        result = query(self.records, category="Developer Tools", sort="name", page=1, per_page=2)
        self.assertEqual(result["page"], 1)
        self.assertLessEqual(len(result["items"]), 2)
        self.assertEqual(result["items"], sorted(result["items"], key=lambda record: record["identity"]["name"].lower()))

    def test_public_candidates_exclude_tier_c_expansion(self):
        ids = {record["identity"]["id"] for record in public_page_candidates(self.records)}
        # cursor is Tier B with full publishing, not Tier C
        self.assertIn("cursor", ids)
        self.assertIn("hostinger", ids)
        # Batch A Tier C tools should be excluded
        self.assertNotIn("circle", ids)
        self.assertNotIn("deel", ids)

    def test_query_rejects_invalid_paging(self):
        with self.assertRaises(ValueError):
            query(self.records, page=0)


if __name__ == "__main__":
    unittest.main()
