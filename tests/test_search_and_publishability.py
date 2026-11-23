import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_search_index import build  # noqa: E402
from decision_graph_common import load_records  # noqa: E402
from recommend_tasks import recommend  # noqa: E402


class SearchAndPublishingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load_records()

    def test_search_index_is_deterministic_and_complete(self):
        index = build(self.records)
        # Search index includes only records that have an HTML page in tools/
        # 162 total v2 records, 15 are pipeline-only without HTML = 147 indexed
        from pathlib import Path
        tools_html_dir = Path(__file__).resolve().parents[1] / "tools"
        records_with_html = [
            r for r in self.records
            if (tools_html_dir / f"{r['identity'].get('slug', r['identity']['id'])}.html").is_file()
        ]
        self.assertEqual(
            len(index["documents"]),
            len(records_with_html),
            f"Search index should contain only records with HTML pages "
            f"(expected {len(records_with_html)}, got {len(index['documents'])})",
        )
        self.assertEqual(index["documents"], sorted(index["documents"], key=lambda item: item["id"]))
        self.assertIn("hostinger", {doc["id"] for doc in index["documents"]})

    def test_task_recommendation_returns_existing_tool(self):
        result = recommend("I need to launch a website", self.records)
        self.assertTrue(result)
        self.assertIn("hostinger", result[0]["tool_ids"])

    def test_task_recommendation_does_not_invent_tools(self):
        result = recommend("something with no matching task", self.records)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
