import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_real_catalog import (  # noqa: E402
    check_evidence_consistency,
    check_new_catalog_records,
    check_preserved_evidence,
    validate_real_catalog,
)


class RealCatalogValidationTests(unittest.TestCase):
    """Tests that run against the real catalog data, not synthetic fixtures."""

    def test_real_catalog_validation_passes(self):
        """No structural errors in the real catalog."""
        results = validate_real_catalog()
        self.assertEqual(
            results["total"],
            0,
            f"Real catalog has {results['total']} structural errors: "
            f"HIGH={len(results['high'])}, MEDIUM={len(results['medium'])}, "
            f"LOW={len(results['low'])}",
        )

    def test_no_broken_tool_relationships(self):
        """No missing tool references in relationships."""
        results = validate_real_catalog()
        self.assertEqual(
            len(results["high"]),
            0,
            f"Broken tool relationships: {results['high']}",
        )

    def test_no_missing_evidence_references(self):
        """No missing claim or source references."""
        results = validate_real_catalog()
        missing = [
            e for e in results["medium"]
            if "references missing" in e
        ]
        self.assertEqual(
            len(missing),
            0,
            f"Missing evidence references: {missing}",
        )


class NewCatalogRecordRegressionTests(unittest.TestCase):
    """Regression tests for the 6 new catalog records."""

    def test_six_new_records_exist(self):
        """All 6 new catalog records exist."""
        errors = check_new_catalog_records()
        missing = [e for e in errors if "missing expected" in e]
        self.assertEqual(
            len(missing),
            0,
            f"Missing catalog records: {missing}",
        )

    def test_new_records_are_tier_c(self):
        """All 6 new records are Tier C."""
        errors = check_new_catalog_records()
        tier_errors = [e for e in errors if "should be Tier C" in e]
        self.assertEqual(len(tier_errors), 0, f"Tier errors: {tier_errors}")

    def test_new_records_are_unverified(self):
        """All 6 new records have unverified confidence."""
        errors = check_new_catalog_records()
        conf_errors = [e for e in errors if "unverified confidence" in e]
        self.assertEqual(
            len(conf_errors),
            0,
            f"Confidence errors: {conf_errors}",
        )


class EvidenceConsistencyTests(unittest.TestCase):
    """No record claims moderate/high confidence without backing evidence."""

    def test_no_unsupported_confidence(self):
        """No record claims moderate confidence without backing evidence."""
        errors = check_evidence_consistency()
        self.assertEqual(
            len(errors),
            0,
            f"Unsupported confidence claims: {errors}",
        )


class PreservedEvidenceTests(unittest.TestCase):
    """Hostinger, Semrush, and Moz Pro evidence is preserved."""

    def test_preserved_records_not_cleared(self):
        """Preserved records still have their evidence intact."""
        errors = check_preserved_evidence()
        self.assertEqual(
            len(errors),
            0,
            f"Preserved evidence errors: {errors}",
        )


if __name__ == "__main__":
    unittest.main()
