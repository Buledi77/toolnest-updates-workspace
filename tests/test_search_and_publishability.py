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
        self.assertEqual(len(index["documents"]), len(self.records))
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
