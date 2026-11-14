import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_stack import build_stack  # noqa: E402


class StackBuilderTests(unittest.TestCase):
    def test_stack_builder_returns_explainable_existing_tools(self):
        result = build_stack("website-launch")
        self.assertEqual(result["requirement_id"], "website-launch")
        self.assertLessEqual(len(result["tools"]), 3)
        self.assertTrue(all(item["tool_id"] for item in result["tools"]))
        self.assertIn("structured discovery", result["explanation"])

    def test_stack_builder_rejects_unknown_requirement(self):
        with self.assertRaises(ValueError):
            build_stack("unknown")


if __name__ == "__main__":
    unittest.main()
