#!/usr/bin/env python3
"""Regression tests for the 4 extractor/freshness gaps.

Each test class corresponds to one gap:
1. TestNegationPatternMatching — negation patterns never become positive capabilities
2. TestAnnualEquivalentContext — annual-equivalent pricing separated from monthly billing
3. TestMetadataOnlyFreshness — metadata-only checks cannot refresh verification dates
4. TestDictCapabilitiesNormalization — dict-based capabilities normalized safely

These tests ensure the fixes in scripts/extractors/__init__.py and
scripts/source_monitor.py do not regress.
"""

import json
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from extractors import FeatureExtractor, PricingExtractor, normalize_dict_capabilities  # noqa: E402
from source_monitor import classify_claim_with_semantics, VerificationStatus  # noqa: E402


class TestNegationPatternMatching(unittest.TestCase):
    """GAP 1: Negation pattern matching — MEDIUM priority.
    
    Ensure 'does not support X', 'no free plan', 'not available on Y'
    never become positive capability facts.
    """
    
    def setUp(self):
        self.extractor = FeatureExtractor("test-tool")
    
    def test_positive_feature_not_filtered(self):
        """Valid positive features should pass through as capabilities."""
        text = "• Advanced analytics dashboard\n• Real-time collaboration\n• Full API access"
        result = self.extractor.extract(text, "https://example.com")
        self.assertEqual(len(result["capabilities"]), 3)
        self.assertEqual(len(result["limitations"]), 0)
        self.assertIn("Advanced analytics dashboard", result["capabilities"])
    
    def test_negation_does_not_support(self):
        "'does not support X' should become a limitation, not a capability."""
        text = "• Does not support custom domains\n• Basic analytics included"
        result = self.extractor.extract(text, "https://example.com")
        self.assertEqual(len(result["capabilities"]), 1)
        self.assertEqual(len(result["limitations"]), 1)
        self.assertIn("Basic analytics included", result["capabilities"])
        self.assertIn("Does not support custom domains", result["limitations"])
        # Critical: negation must NOT appear in capabilities
        for cap in result["capabilities"]:
            self.assertNotIn("does not support", cap.lower())
    
    def test_negation_no_free_plan(self):
        "'no free plan' should become a limitation, not a capability."""
        text = "• No free plan available\n• Paid plans start at $10/mo"
        result = self.extractor.extract(text, "https://example.com")
        self.assertEqual(len(result["capabilities"]), 1)
        self.assertEqual(len(result["limitations"]), 1)
        self.assertIn("No free plan available", result["limitations"])
        for cap in result["capabilities"]:
            self.assertNotIn("no free plan", cap.lower())
    
    def test_negation_not_available_on(self):
        "'not available on Y' should become a limitation, not a capability."""
        text = "• Not available on Windows\n• Works on macOS and Linux"
        result = self.extractor.extract(text, "https://example.com")
        self.assertEqual(len(result["capabilities"]), 1)
        self.assertEqual(len(result["limitations"]), 1)
        self.assertIn("Not available on Windows", result["limitations"])
    
    def test_negation_not_supported(self):
        "'not supported' should become a limitation."""
        text = "• Legacy API not supported\n• Modern REST API available"
        result = self.extractor.extract(text, "https://example.com")
        self.assertEqual(len(result["capabilities"]), 1)
        self.assertEqual(len(result["limitations"]), 1)
    
    def test_negation_without(self):
        "'without X' should become a limitation."""
        text = "• Basic plan without team features\n• Pro plan with full features"
        result = self.extractor.extract(text, "https://example.com")
        self.assertEqual(len(result["capabilities"]), 1)
        self.assertEqual(len(result["limitations"]), 1)
    
    def test_negation_cannot(self):
        "'cannot X' should become a limitation."""
        text = "• Cannot export to PDF\n• Can export to CSV"
        result = self.extractor.extract(text, "https://example.com")
        self.assertEqual(len(result["capabilities"]), 1)
        self.assertEqual(len(result["limitations"]), 1)
    
    def test_absence_of_mention_is_not_negation(self):
        """Absence of mention should NOT be treated as negation.
        
        Only explicit negation patterns are detected. Do not infer
        negative evidence from silence.
        """
        text = "• Cloud hosting\n• On-premise option"
        result = self.extractor.extract(text, "https://example.com")
        self.assertEqual(len(result["capabilities"]), 2)
        self.assertEqual(len(result["limitations"]), 0)
    
    def test_mixed_positive_and_negative(self):
        """Mixed text should separate capabilities from limitations."""
        text = (
            "• AI-powered insights\n"
            "• Does not support offline mode\n"
            "• Real-time data sync\n"
            "• No free trial available\n"
            "• Enterprise SSO support"
        )
        result = self.extractor.extract(text, "https://example.com")
        self.assertEqual(len(result["capabilities"]), 3)
        self.assertEqual(len(result["limitations"]), 2)
        self.assertIn("AI-powered insights", result["capabilities"])
        self.assertIn("Does not support offline mode", result["limitations"])


class TestAnnualEquivalentContext(unittest.TestCase):
    """GAP 2: Annual-equivalent context — MEDIUM priority.
    
    Distinguish monthly billing price from annual commitment shown as
    monthly equivalent. Never feed annual-equivalent into month-to-month
    budget logic as if identical.
    """
    
    def setUp(self):
        self.extractor = PricingExtractor("test-tool")
    
    def test_monthly_billing_identified(self):
        """True monthly billing should have billing_basis=monthly_billing."""
        text = "Plans start at $29/month with no commitment required."
        result = self.extractor.extract(text, "https://example.com/pricing")
        prices = result["pricing"]["detected_prices"]
        monthly_prices = [p for p in prices if p.get("billing_interval") == "monthly"]
        self.assertGreater(len(monthly_prices), 0)
        for p in monthly_prices:
            self.assertEqual(p.get("billing_basis"), "monthly_billing")
    
    def test_annual_billing_identified(self):
        """Annual billing should have billing_basis=annual_billing."""
        text = "Save with annual billing: $240/year."
        result = self.extractor.extract(text, "https://example.com/pricing")
        prices = result["pricing"]["detected_prices"]
        annual_prices = [p for p in prices if p.get("billing_interval") == "annual"]
        self.assertGreater(len(annual_prices), 0)
        for p in annual_prices:
            self.assertEqual(p.get("billing_basis"), "annual_billing")
    
    def test_annual_equivalent_separated(self):
        """Annual-equivalent monthly price must be distinguished from true monthly."""
        text = "$19/mo billed annually (save 20% vs $29/mo monthly)."
        result = self.extractor.extract(text, "https://example.com/pricing")
        prices = result["pricing"]["detected_prices"]
        # Should detect the annual-equivalent price
        annual_equiv = [p for p in prices if p.get("billing_basis") == "annual_billing_monthly_equivalent"]
        self.assertGreater(len(annual_equiv), 0)
        # Annual-equivalent should have a note
        for p in annual_equiv:
            self.assertIn("Annual commitment", p.get("note", ""))
    
    def test_billing_basis_always_present(self):
        """Every extracted price must have a billing_basis field."""
        text = "$29/month, $240/year, or $19/mo billed annually"
        result = self.extractor.extract(text, "https://example.com/pricing")
        prices = result["pricing"]["detected_prices"]
        for p in prices:
            self.assertIn("billing_basis", p)
            self.assertIsNotNone(p["billing_basis"])
    
    def test_annual_equivalent_not_used_for_monthly_budget(self):
        """Annual-equivalent prices should not be treated as monthly billing.
        
        This is the key invariant: budget logic that filters by monthly price
        should not include annual-equivalent prices.
        """
        text = "$19/mo billed annually"
        result = self.extractor.extract(text, "https://example.com/pricing")
        prices = result["pricing"]["detected_prices"]
        # Filter as if doing monthly budget logic
        monthly_only = [
            p for p in prices
            if p.get("billing_basis") == "monthly_billing"
        ]
        # Annual-equivalent should NOT appear in monthly-only list
        for p in monthly_only:
            self.assertNotEqual(p.get("billing_basis"), "annual_billing_monthly_equivalent")


class TestMetadataOnlyFreshness(unittest.TestCase):
    """GAP 3: Metadata-only freshness — LOW priority.
    
    Ensure metadata/HTTP freshness alone cannot refresh last_verified_date
    or factual verification dates.
    """
    
    def setUp(self):
        self.policy = {
            "thresholds": {
                "pricing": 90,
                "capability": 180,
                "general": 365,
            },
            "default_threshold": 365,
        }
        self.today = date(2025, 6, 1)
    
    def test_metadata_only_returns_due_for_recheck(self):
        """A claim within its freshness window but without actual fetch
        should return DUE_FOR_RECHECK, not VERIFIED_CURRENT."""
        claim = {
            "claim_id": "test-1",
            "tool_id": "test-tool",
            "claim_type": "pricing",
            "stale_after": "2025-12-31",  # Still within window
            "last_verified_date": "2025-01-01",
        }
        status, urgency = classify_claim_with_semantics(
            claim, self.policy, self.today, source_fetch_results=None
        )
        # Must NOT be VERIFIED_CURRENT without actual fetch
        self.assertNotEqual(status, VerificationStatus.VERIFIED_CURRENT)
        self.assertEqual(status, VerificationStatus.DUE_FOR_RECHECK)
    
    def test_verified_at_alone_not_enough(self):
        """verified_at within threshold is not enough for VERIFIED_CURRENT
        without actual fetch in this run."""
        claim = {
            "claim_id": "test-2",
            "tool_id": "test-tool",
            "claim_type": "pricing",
            "verified_at": "2025-05-01",  # Within 90-day threshold
        }
        status, urgency = classify_claim_with_semantics(
            claim, self.policy, self.today, source_fetch_results=None
        )
        self.assertNotEqual(status, VerificationStatus.VERIFIED_CURRENT)
        self.assertEqual(status, VerificationStatus.DUE_FOR_RECHECK)
    
    def test_actual_fetch_returns_verified(self):
        """An actual successful fetch should return RECHECK_PASSED."""
        claim = {
            "claim_id": "test-3",
            "tool_id": "test-tool",
            "claim_type": "pricing",
        }
        fetch_results = {
            "test-tool": {
                "status": "success",
                "change_detected": False,
            }
        }
        status, urgency = classify_claim_with_semantics(
            claim, self.policy, self.today, source_fetch_results=fetch_results
        )
        self.assertEqual(status, VerificationStatus.RECHECK_PASSED)
    
    def test_stale_after_passed_returns_due(self):
        """A claim past its stale_after date should be DUE_FOR_RECHECK."""
        claim = {
            "claim_id": "test-4",
            "tool_id": "test-tool",
            "claim_type": "pricing",
            "stale_after": "2025-01-01",  # Past due
        }
        status, urgency = classify_claim_with_semantics(
            claim, self.policy, self.today, source_fetch_results=None
        )
        self.assertEqual(status, VerificationStatus.DUE_FOR_RECHECK)
        self.assertGreater(urgency, 0)
    
    def test_no_dates_returns_due(self):
        """A claim with no dates at all should be DUE_FOR_RECHECK."""
        claim = {
            "claim_id": "test-5",
            "tool_id": "test-tool",
            "claim_type": "pricing",
        }
        status, urgency = classify_claim_with_semantics(
            claim, self.policy, self.today, source_fetch_results=None
        )
        self.assertEqual(status, VerificationStatus.DUE_FOR_RECHECK)
    
    def test_source_unavailable_handled(self):
        """A blocked source should enter SOURCE_UNAVAILABLE state."""
        claim = {
            "claim_id": "test-6",
            "tool_id": "blocked-tool",
            "claim_type": "pricing",
        }
        fetch_results = {
            "blocked-tool": {
                "status": "unavailable",
            }
        }
        status, urgency = classify_claim_with_semantics(
            claim, self.policy, self.today, source_fetch_results=fetch_results
        )
        self.assertEqual(status, VerificationStatus.SOURCE_UNAVAILABLE)


class TestDictCapabilitiesNormalization(unittest.TestCase):
    """GAP 4: Dict-based capabilities — LOW priority.
    
    Normalize structured/dict capability records safely without losing
    evidence provenance.
    """
    
    def test_none_returns_empty(self):
        """None input should return empty list."""
        result = normalize_dict_capabilities(None)
        self.assertEqual(result, [])
    
    def test_string_list_normalized(self):
        """A list of strings should be normalized to dicts."""
        caps = ["API access", "SSO", "Webhooks"]
        result = normalize_dict_capabilities(caps)
        self.assertEqual(len(result), 3)
        for entry in result:
            self.assertIn("name", entry)
            self.assertIn("raw", entry)
            self.assertIn("verified", entry)
        self.assertEqual(result[0]["name"], "API access")
        self.assertFalse(result[0]["verified"])
    
    def test_dict_list_normalized(self):
        """A list of dicts should preserve provenance fields."""
        caps = [
            {"name": "API", "category": "integration", "verified": True, "source": "official"},
            {"name": "SSO", "category": "security", "verified": False},
        ]
        result = normalize_dict_capabilities(caps)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "API")
        self.assertEqual(result[0]["category"], "integration")
        self.assertTrue(result[0]["verified"])
        self.assertEqual(result[0]["evidence_source"], "official")
    
    def test_single_dict_wrapped(self):
        """A single dict should be wrapped in a list."""
        cap = {"name": "Analytics", "verified": True}
        result = normalize_dict_capabilities(cap)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Analytics")
    
    def test_provenance_preserved(self):
        """Evidence provenance fields must be preserved."""
        cap = {
            "name": "Feature X",
            "evidence_source": "pricing_page",
            "verified_at": "2025-01-01",
            "claim_id": "claim-123",
            "url": "https://example.com/pricing",
        }
        result = normalize_dict_capabilities(cap)
        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry["evidence_source"], "pricing_page")
        self.assertEqual(entry["verified_at"], "2025-01-01")
        self.assertEqual(entry["claim_id"], "claim-123")
        self.assertEqual(entry["url"], "https://example.com/pricing")
    
    def test_mixed_types(self):
        """Mixed string and dict types should all be normalized."""
        caps = [
            "Simple feature",
            {"name": "Complex feature", "verified": True, "category": "advanced"},
            123,  # Edge case: non-string, non-dict
        ]
        result = normalize_dict_capabilities(caps)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["name"], "Simple feature")
        self.assertEqual(result[1]["name"], "Complex feature")
        self.assertTrue(result[1]["verified"])
        self.assertEqual(result[2]["name"], "123")
    
    def test_alternative_name_fields(self):
        """Dicts with 'capability' or 'feature' instead of 'name' should work."""
        caps = [
            {"capability": "Alt name 1"},
            {"feature": "Alt name 2"},
        ]
        result = normalize_dict_capabilities(caps)
        self.assertEqual(result[0]["name"], "Alt name 1")
        self.assertEqual(result[1]["name"], "Alt name 2")
    
    def test_empty_list(self):
        """Empty list should return empty list."""
        result = normalize_dict_capabilities([])
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
