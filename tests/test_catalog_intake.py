import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from ingest_catalog_candidates import make_record, validate_candidates  # noqa: E402


class CatalogIntakeTests(unittest.TestCase):
    def test_candidate_validation_rejects_duplicate_ids(self):
        errors, verified = validate_candidates(
            [{"id": "existing", "official_url": "https://example.com", "source_note": "x"}],
            {"existing"},
            check_network=False,
        )
        self.assertTrue(errors)
        self.assertEqual(verified, {})

    def test_generated_candidate_is_non_publishing_tier_c(self):
        record = make_record(
            {
                "id": "example-tool",
                "name": "Example Tool",
                "official_url": "https://example.com",
                "category": "Research",
                "tags": ["research"],
            },
            "2026-11-14T21:00:00Z",
        )
        self.assertEqual(record["editorial"]["editorial_tier"], "C")
        self.assertEqual(record["publishing"]["indexability"], "noindex")
        self.assertFalse(record["publishing"]["sitemap_eligible"])


if __name__ == "__main__":
    unittest.main()
