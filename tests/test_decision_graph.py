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
        # The full dataset has incomplete ledger coverage (172 missing claims, 86 missing sources).
        # This test validates that a minimal synthetic Tier A record passes validation.
        synthetic = [
            {
                "$schema": "https://www.toolnestai.tech/schemas/toolnest-tool-v1.json",
                "schema_version": "toolnest-tool-v1",
                "identity": {"id": "synth-a", "name": "Synth A", "slug": "synth-a", "official_url": "https://synth-a.example", "status": "active", "logo": "/assets/logos/synth-a.png", "aliases": []},
                "discovery": {"categories": ["SEO"], "use_cases": [], "audiences": [], "platforms": ["web"], "integrations": [], "tags": []},
                "factual_profile": {"concise_summary": "Test tool", "primary_purpose": "Test", "capabilities": [], "limitations": [], "free_plan_status": [], "trial_status": [], "pricing_status": [], "pricing_regions": [], "availability_regions": []},
                "editorial": {"editorial_tier": "A", "best_for": [], "not_recommended_for": [], "editorial_summary": "Test", "review_status": "published", "review_url": "https://www.toolnestai.tech/tools/synth-a.html", "review_owner": "Test", "editorial_last_reviewed": "2026-11-14"},
                "relationships": {"alternatives": [], "meaningful_comparisons": [], "related_tools": [], "compatible_tools": [], "replaces": [], "replaced_by": []},
                "evidence": {"claim_refs": [], "source_ids": []},
                "monetization": {"affiliate_status": "not_applied", "affiliate_network": None, "affiliate_url": None, "official_non_affiliate_url": "https://synth-a.example", "approved_regions": [], "restrictions": [], "disclosure_required": True, "last_link_check": "2026-11-14"},
                "publishing": {"directory_visibility": "public", "standalone_page_status": "published", "indexability": "index", "sitemap_eligible": True, "canonical_url": "https://www.toolnestai.tech/tools/synth-a.html", "template_type": "review", "content_quality_status": "assessed", "prepublish_status": "published"},
                "freshness": {"created_at": "2026-11-14T00:00:00Z", "updated_at": "2026-11-14T00:00:00Z", "last_verified_at": "2026-11-14T00:00:00Z", "next_review_at": "2026-12-14T00:00:00Z", "stale_fields": [], "change_history_reference": None},
            }
        ]
        self.assertEqual(self.errors(records=synthetic), [])

    def test_valid_tier_b_record(self):
        # Tier B record with no evidence requirements
        synthetic = [
            {
                "$schema": "https://www.toolnestai.tech/schemas/toolnest-tool-v1.json",
                "schema_version": "toolnest-tool-v1",
                "identity": {"id": "synth-b", "name": "Synth B", "slug": "synth-b", "official_url": "https://synth-b.example", "status": "active", "logo": "/assets/logos/synth-b.png", "aliases": []},
                "discovery": {"categories": ["SEO"], "use_cases": [], "audiences": [], "platforms": ["web"], "integrations": [], "tags": []},
                "factual_profile": {"concise_summary": "Test tool", "primary_purpose": "Test", "capabilities": [], "limitations": [], "free_plan_status": [], "trial_status": [], "pricing_status": [], "pricing_regions": [], "availability_regions": []},
                "editorial": {"editorial_tier": "B", "best_for": [], "not_recommended_for": [], "editorial_summary": "Test", "review_status": "published", "review_url": "https://www.toolnestai.tech/tools/synth-b.html", "review_owner": "Test", "editorial_last_reviewed": "2026-11-14"},
                "relationships": {"alternatives": [], "meaningful_comparisons": [], "related_tools": [], "compatible_tools": [], "replaces": [], "replaced_by": []},
                "evidence": {"claim_refs": [], "source_ids": []},
                "monetization": {"affiliate_status": "not_applied", "affiliate_network": None, "affiliate_url": None, "official_non_affiliate_url": "https://synth-b.example", "approved_regions": [], "restrictions": [], "disclosure_required": True, "last_link_check": "2026-11-14"},
                "publishing": {"directory_visibility": "public", "standalone_page_status": "published", "indexability": "index", "sitemap_eligible": True, "canonical_url": "https://www.toolnestai.tech/tools/synth-b.html", "template_type": "review", "content_quality_status": "assessed", "prepublish_status": "published"},
                "freshness": {"created_at": "2026-11-14T00:00:00Z", "updated_at": "2026-11-14T00:00:00Z", "last_verified_at": "2026-11-14T00:00:00Z", "next_review_at": "2026-12-14T00:00:00Z", "stale_fields": [], "change_history_reference": None},
            }
        ]
        self.assertEqual(self.errors(records=synthetic), [])

    def test_valid_tier_c_record(self):
        # Tier C record with noindex and no standalone page
        synthetic = [
            {
                "$schema": "https://www.toolnestai.tech/schemas/toolnest-tool-v1.json",
                "schema_version": "toolnest-tool-v1",
                "identity": {"id": "synth-c", "name": "Synth C", "slug": "synth-c", "official_url": "https://synth-c.example", "status": "active", "logo": "/assets/logos/synth-c.png", "aliases": []},
                "discovery": {"categories": ["SEO"], "use_cases": [], "audiences": [], "platforms": ["web"], "integrations": [], "tags": []},
                "factual_profile": {"concise_summary": "Test tool", "primary_purpose": "Test", "capabilities": [], "limitations": [], "free_plan_status": [], "trial_status": [], "pricing_status": [], "pricing_regions": [], "availability_regions": []},
                "editorial": {"editorial_tier": "C", "best_for": [], "not_recommended_for": [], "editorial_summary": "Test", "review_status": "none", "review_url": None, "review_owner": "Test", "editorial_last_reviewed": "2026-11-14"},
                "relationships": {"alternatives": [], "meaningful_comparisons": [], "related_tools": [], "compatible_tools": [], "replaces": [], "replaced_by": []},
                "evidence": {"claim_refs": [], "source_ids": []},
                "monetization": {"affiliate_status": "not_applied", "affiliate_network": None, "affiliate_url": None, "official_non_affiliate_url": "https://synth-c.example", "approved_regions": [], "restrictions": [], "disclosure_required": True, "last_link_check": "2026-11-14"},
                "publishing": {"directory_visibility": "public", "standalone_page_status": "none", "indexability": "noindex", "sitemap_eligible": False, "canonical_url": None, "template_type": "review", "content_quality_status": "unassessed", "prepublish_status": "not_ready"},
                "freshness": {"created_at": "2026-11-14T00:00:00Z", "updated_at": "2026-11-14T00:00:00Z", "last_verified_at": "2026-11-14T00:00:00Z", "next_review_at": "2026-12-14T00:00:00Z", "stale_fields": [], "change_history_reference": None},
            }
        ]
        self.assertEqual(self.errors(records=synthetic), [])

    def test_missing_evidence(self):
        # Use hostinger, whose claims exist in the ledger, so clearing claim_refs triggers "omits claim"
        records = copy.deepcopy(self.records)
        record = next(r for r in records if r["identity"]["id"] == "hostinger")
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
        # Use records[1] (adcreative) which has an "alternatives" key
        records = copy.deepcopy(self.records)
        records[1]["relationships"]["alternatives"].append("missing-tool")
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
        # Updated after expanding migration manifest from 50 to 153 tools
        self.assertEqual(manifest["source_count"], 153)
        self.assertEqual(len(manifest["records"]), 153)


if __name__ == "__main__":
    unittest.main()
