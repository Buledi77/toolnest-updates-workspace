import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from decision_graph_common import (  # noqa: E402
    LEDGER_PATH,
    ROOT,
    load_json,
    load_records,
    validate_affiliate_separation,
    validate_freshness,
    validate_tool_records,
)


class DecisionGraphValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load_records()
        cls.ledger = load_json(LEDGER_PATH)

    def errors(self, records=None, ledger=None):
        return validate_tool_records(
            records if records is not None else copy.deepcopy(self.records),
            ledger if ledger is not None else copy.deepcopy(self.ledger),
        )

    def test_valid_tier_a_record(self):
        self.assertEqual(self.errors(), [])

    def test_valid_tier_b_record(self):
        records = copy.deepcopy(self.records)
        records[0]["editorial"]["editorial_tier"] = "B"
        self.assertEqual(self.errors(records), [])

    def test_valid_tier_c_record(self):
        records = copy.deepcopy(self.records)
        records[0]["editorial"]["editorial_tier"] = "C"
        records[0]["publishing"].update(
            {
                "standalone_page_status": "none",
                "indexability": "noindex",
                "sitemap_eligible": False,
                "canonical_url": None,
                "content_quality_status": "unassessed",
                "prepublish_status": "not_ready",
            }
        )
        self.assertEqual(self.errors(records), [])

    def test_missing_evidence(self):
        records = copy.deepcopy(self.records)
        record = next(record for record in records if record["evidence"]["claim_refs"])
        record["evidence"]["claim_refs"] = []
        errors = self.errors(records)
        self.assertTrue(any("omits claim" in error for error in errors))

    def test_stale_evidence_requires_status(self):
        ledger = copy.deepcopy(self.ledger)
        ledger["claims"][0]["status"] = "verified"
        ledger["claims"][0]["stale_after"] = "2026-01-01"
        errors = validate_freshness("2026-11-14", ledger=ledger, records=self.records)
        self.assertTrue(any("expired" in error for error in errors))

    def test_duplicate_slug(self):
        records = copy.deepcopy(self.records)
        records[1]["identity"]["slug"] = records[0]["identity"]["slug"]
        errors = self.errors(records)
        self.assertTrue(any("duplicate tool slugs" in error for error in errors))

    def test_broken_relationship(self):
        records = copy.deepcopy(self.records)
        records[0]["relationships"]["alternatives"].append("missing-tool")
        errors = self.errors(records)
        self.assertTrue(any("references missing tool" in error for error in errors))

    def test_invalid_affiliate_separation(self):
        records = copy.deepcopy(self.records)
        records[0]["monetization"]["official_non_affiliate_url"] = "https://affiliate.example"
        errors = validate_affiliate_separation(records)
        self.assertTrue(any("official_non_affiliate_url" in error for error in errors))

    def test_invalid_indexability_sitemap_combination(self):
        records = copy.deepcopy(self.records)
        records[0]["publishing"]["indexability"] = "noindex"
        records[0]["publishing"]["sitemap_eligible"] = True
        errors = self.errors(records)
        self.assertTrue(any("sitemap eligible but not indexable" in error for error in errors))

    def test_affiliate_validator_passes(self):
        self.assertEqual(validate_affiliate_separation(), [])

    def test_legacy_shadow_migration_manifest(self):
        manifest = load_json(ROOT / "data" / "migrations" / "legacy-to-v2-map.json")
        self.assertEqual(manifest["source_count"], 50)
        self.assertEqual(manifest["generated_shadow_record_count"], 47)
        self.assertEqual(len(manifest["benchmark_records_preserved"]), 3)
        self.assertEqual(len(manifest["records"]), 50)


if __name__ == "__main__":
    unittest.main()
