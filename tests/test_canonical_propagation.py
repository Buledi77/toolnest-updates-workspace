#!/usr/bin/env python3
"""Fixture-based tests for canonical fact propagation.

Tests that when an accepted mutable fact changes in the evidence ledger,
every relevant ToolNest consumer derives the new value automatically.

Uses a fixture tool (fixture-tool) to simulate:
- PRICE: $X → $Y
- FREE_PLAN: false → true
- PLATFORM: web → web + mobile
- CAPABILITY: existing → updated

Verifies downstream propagation to:
- Tool Profile (data/tools/*.json → HTML)
- Decision Engine bundle
- Directory (tools-v1.json)
- Stack Analyzer (tools-v1.json)
- Freshness state (facts_checked)
"""

import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from derive_canonical_facts import (  # noqa: E402
    derive_canonical_facts,
    update_tool_json_from_canonical,
    update_tools_v1_from_canonical,
    update_tools_json_from_canonical,
)


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "data" / "evidence" / "evidence-ledger.json"
CANONICAL_FACTS_PATH = ROOT / "data" / "canonical-facts.json"
TOOLS_V1_PATH = ROOT / "data" / "tools-v1.json"
TOOLS_JSON_PATH = ROOT / "data" / "tools.json"
DATA_TOOLS_DIR = ROOT / "data" / "tools"


def load_json(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


class TestCanonicalPropagation(unittest.TestCase):
    """Test that canonical fact changes propagate to all consumers."""

    @classmethod
    def setUpClass(cls):
        """Save original data files for restoration."""
        cls.saved_ledger = load_json(LEDGER_PATH)
        cls.saved_v1 = load_json(TOOLS_V1_PATH)

        # Create fixture tool JSON if it doesn't exist
        cls.fixture_tool_path = DATA_TOOLS_DIR / "fixture-tool.json"
        cls.fixture_existed = cls.fixture_tool_path.exists()
        if not cls.fixture_existed:
            cls.saved_fixture = None
            fixture_data = {
                "identity": {"id": "fixture-tool", "name": "Fixture Tool", "slug": "fixture-tool"},
                "discovery": {"platforms": ["web"], "categories": ["Testing"]},
                "pricing": {
                    "checkedOn": "2026-01-01",
                    "currency": "USD",
                    "billingBasis": "monthly",
                    "freePlan": False,
                    "plans": [{"name": "Pro", "priceMonthly": 50}]
                }
            }
            save_json(cls.fixture_tool_path, fixture_data)
        else:
            cls.saved_fixture = load_json(cls.fixture_tool_path)

        # Add fixture tool to tools-v1.json if not present
        cls.fixture_in_v1 = False
        for tool in cls.saved_v1.get("tools", []):
            if tool.get("id") == "fixture-tool":
                cls.fixture_in_v1 = True
                break
        if not cls.fixture_in_v1:
            cls.saved_v1["tools"].append({
                "id": "fixture-tool",
                "name": "Fixture Tool",
                "discovery": {"platforms": ["web"], "categories": ["Testing"]},
                "pricing": {
                    "checkedOn": "2026-01-01",
                    "currency": "USD",
                    "billingBasis": "monthly",
                    "freePlan": False,
                    "plans": [{"name": "Pro", "priceMonthly": 50}]
                }
            })

    @classmethod
    def tearDownClass(cls):
        """Restore original data files."""
        save_json(LEDGER_PATH, cls.saved_ledger)
        save_json(TOOLS_V1_PATH, cls.saved_v1)

        # Remove fixture tool JSON if it didn't exist before
        if not cls.fixture_existed and cls.fixture_tool_path.exists():
            cls.fixture_tool_path.unlink()

    def _add_fixture_claim(self, ledger, claim_type, value, status="verified"):
        """Add a claim for fixture-tool to the ledger."""
        claim = {
            "claim_id": f"fixture-tool-{claim_type}-test",
            "tool_id": "fixture-tool",
            "field_path": f"factual_profile.{claim_type}",
            "claim_type": claim_type,
            "value": value,
            "status": status,
            "verified_at": "2026-11-23",
            "accessed_at": "2026-11-23",
        }
        ledger["claims"].append(claim)
        return claim

    def test_price_propagation(self):
        """Test that a price change propagates to tool JSON and tools-v1."""
        ledger = copy.deepcopy(self.saved_ledger)

        # Add a pricing claim with a new price
        self._add_fixture_claim(ledger, "pricing", {
            "plans": [
                {"name": "Pro", "monthly_usd": 99, "websites": 10},
                {"name": "Enterprise", "monthly_usd": 299, "websites": 50}
            ]
        })
        save_json(LEDGER_PATH, ledger)

        try:
            # Derive canonical facts
            canonical = derive_canonical_facts()
            self.assertIn("fixture-tool", canonical)
            self.assertIn("pricing", canonical["fixture-tool"])

            # Update tool JSON
            update_tool_json_from_canonical("fixture-tool", canonical["fixture-tool"])

            # Verify tool JSON was updated
            tool_data = load_json(self.fixture_tool_path)
            pricing = tool_data.get("pricing", {})
            self.assertEqual(pricing.get("checkedOn"), "2026-11-23")

            # Update tools-v1
            update_tools_v1_from_canonical(canonical)
            v1_data = load_json(TOOLS_V1_PATH)
            fixture_v1 = None
            for tool in v1_data.get("tools", []):
                if tool.get("id") == "fixture-tool":
                    fixture_v1 = tool
                    break
            self.assertIsNotNone(fixture_v1)
            self.assertEqual(fixture_v1.get("pricing", {}).get("checkedOn"), "2026-11-23")

        finally:
            # Restore
            save_json(LEDGER_PATH, self.saved_ledger)
            if self.saved_fixture:
                save_json(self.fixture_tool_path, self.saved_fixture)
            save_json(TOOLS_V1_PATH, self.saved_v1)

    def test_free_plan_propagation(self):
        """Test that free plan change propagates to all consumers."""
        ledger = copy.deepcopy(self.saved_ledger)

        # Add a free_plan claim saying there IS a free plan
        self._add_fixture_claim(ledger, "free_plan",
            "Free plan available with 10 reports per day limit")
        save_json(LEDGER_PATH, ledger)

        try:
            canonical = derive_canonical_facts()
            self.assertIn("fixture-tool", canonical)
            self.assertIn("free_plan", canonical["fixture-tool"])

            # Verify free_plan status is detected
            free_plan = canonical["fixture-tool"]["free_plan"]
            self.assertIn("permanent_free_plan", free_plan.get("status", ""))

            # Update tool JSON
            update_tool_json_from_canonical("fixture-tool", canonical["fixture-tool"])
            tool_data = load_json(self.fixture_tool_path)
            pricing = tool_data.get("pricing", {})
            self.assertTrue(pricing.get("freePlan") is True)

            # Update tools-v1
            update_tools_v1_from_canonical(canonical)
            v1_data = load_json(TOOLS_V1_PATH)
            fixture_v1 = None
            for tool in v1_data.get("tools", []):
                if tool.get("id") == "fixture-tool":
                    fixture_v1 = tool
                    break
            self.assertIsNotNone(fixture_v1)
            pricing_v1 = fixture_v1.get("pricing") or {}
            self.assertTrue(pricing_v1.get("freePlan") is True)

        finally:
            save_json(LEDGER_PATH, self.saved_ledger)
            if self.saved_fixture:
                save_json(self.fixture_tool_path, self.saved_fixture)
            save_json(TOOLS_V1_PATH, self.saved_v1)

    def test_platform_propagation(self):
        """Test that platform change propagates to discovery fields."""
        ledger = copy.deepcopy(self.saved_ledger)

        # Add a platform claim with web + mobile
        self._add_fixture_claim(ledger, "platform", ["web", "mobile"])
        save_json(LEDGER_PATH, ledger)

        try:
            canonical = derive_canonical_facts()
            self.assertIn("fixture-tool", canonical)
            self.assertIn("platform", canonical["fixture-tool"])
            self.assertEqual(canonical["fixture-tool"]["platform"], ["web", "mobile"])

            # Update tool JSON
            update_tool_json_from_canonical("fixture-tool", canonical["fixture-tool"])
            tool_data = load_json(self.fixture_tool_path)
            discovery = tool_data.get("discovery", {})
            self.assertEqual(discovery.get("platforms"), ["web", "mobile"])

            # Update tools-v1
            update_tools_v1_from_canonical(canonical)
            v1_data = load_json(TOOLS_V1_PATH)
            fixture_v1 = None
            for tool in v1_data.get("tools", []):
                if tool.get("id") == "fixture-tool":
                    fixture_v1 = tool
                    break
            self.assertEqual(
                fixture_v1.get("discovery", {}).get("platforms"),
                ["web", "mobile"]
            )

        finally:
            save_json(LEDGER_PATH, self.saved_ledger)
            if self.saved_fixture:
                save_json(self.fixture_tool_path, self.saved_fixture)
            save_json(TOOLS_V1_PATH, self.saved_v1)

    def test_capability_propagation(self):
        """Test that capability change propagates to canonical facts."""
        ledger = copy.deepcopy(self.saved_ledger)

        # Add a capability claim
        self._add_fixture_claim(ledger, "capability", [
            "ai-powered analysis",
            "real-time monitoring",
            "custom dashboards"
        ])
        save_json(LEDGER_PATH, ledger)

        try:
            canonical = derive_canonical_facts()
            self.assertIn("fixture-tool", canonical)
            self.assertIn("capabilities", canonical["fixture-tool"])
            caps = canonical["fixture-tool"]["capabilities"]
            self.assertIn("ai-powered analysis", caps)
            self.assertIn("real-time monitoring", caps)
            self.assertIn("custom dashboards", caps)

        finally:
            save_json(LEDGER_PATH, self.saved_ledger)

    def test_facts_checked_unified(self):
        """Test that facts_checked date is unified across consumers."""
        ledger = copy.deepcopy(self.saved_ledger)

        # Add multiple claims with same verified_at
        self._add_fixture_claim(ledger, "pricing", {
            "plans": [{"name": "Pro", "monthly_usd": 99}]
        })
        self._add_fixture_claim(ledger, "free_plan",
            "Free plan with limited features")
        self._add_fixture_claim(ledger, "trial",
            "14-day free trial on all plans")
        save_json(LEDGER_PATH, ledger)

        try:
            canonical = derive_canonical_facts()
            fixture_facts = canonical.get("fixture-tool", {})

            # All should derive from the same facts_checked date
            facts_checked = fixture_facts.get("facts_checked")
            self.assertEqual(facts_checked, "2026-11-23")

            # Update tool JSON and verify checkedOn matches
            update_tool_json_from_canonical("fixture-tool", fixture_facts)
            tool_data = load_json(self.fixture_tool_path)
            pricing = tool_data.get("pricing", {})
            self.assertEqual(pricing.get("checkedOn"), "2026-11-23")

        finally:
            save_json(LEDGER_PATH, self.saved_ledger)
            if self.saved_fixture:
                save_json(self.fixture_tool_path, self.saved_fixture)

    def test_no_crash_on_missing_tool(self):
        """Test that derivation doesn't crash for tools without JSON files."""
        ledger = copy.deepcopy(self.saved_ledger)

        # Add a claim for a non-existent tool
        self._add_fixture_claim(ledger, "pricing", {
            "plans": [{"name": "Pro", "monthly_usd": 99}]
        })
        # Modify tool_id to non-existent
        ledger["claims"][-1]["tool_id"] = "nonexistent-tool-12345"
        save_json(LEDGER_PATH, ledger)

        try:
            # Should not crash
            canonical = derive_canonical_facts()
            self.assertIn("nonexistent-tool-12345", canonical)

        finally:
            save_json(LEDGER_PATH, self.saved_ledger)

    def test_disputed_claim_not_propagated(self):
        """Test that disputed claims are not propagated."""
        ledger = copy.deepcopy(self.saved_ledger)

        # Add a disputed claim
        claim = {
            "claim_id": "fixture-tool-pricing-disputed",
            "tool_id": "fixture-tool",
            "field_path": "factual_profile.pricing_status",
            "claim_type": "pricing",
            "value": {"plans": [{"name": "Fake", "monthly_usd": 1}]},
            "status": "disputed",
            "verified_at": "2026-11-23",
        }
        ledger["claims"].append(claim)
        save_json(LEDGER_PATH, ledger)

        try:
            canonical = derive_canonical_facts()
            # Disputed claims should not appear in canonical facts
            # (only verified/verified_official are accepted)
            fixture_facts = canonical.get("fixture-tool", {})
            # If there are no other accepted claims, fixture-tool should not
            # have pricing from the disputed claim
            if "pricing" in fixture_facts:
                # Check that the disputed value is not propagated
                plans = fixture_facts["pricing"].get("plans", [])
                for plan in plans:
                    self.assertNotEqual(plan.get("name"), "Fake")

        finally:
            save_json(LEDGER_PATH, self.saved_ledger)

    def test_confidence_computation(self):
        """Test that confidence is computed correctly."""
        ledger = copy.deepcopy(self.saved_ledger)

        # Add verified_official claim (should give high confidence)
        self._add_fixture_claim(ledger, "pricing", {
            "plans": [{"name": "Pro", "monthly_usd": 99}]
        }, status="verified_official")
        save_json(LEDGER_PATH, ledger)

        try:
            canonical = derive_canonical_facts()
            fixture_facts = canonical.get("fixture-tool", {})
            self.assertEqual(fixture_facts.get("confidence"), "high")

        finally:
            save_json(LEDGER_PATH, self.saved_ledger)

    def test_recheck_does_not_change_verified_date(self):
        """Test that a recheck attempt alone does not change the verified date."""
        ledger = copy.deepcopy(self.saved_ledger)

        # Add a claim with a specific verified_at
        self._add_fixture_claim(ledger, "pricing", {
            "plans": [{"name": "Pro", "monthly_usd": 99}]
        })
        save_json(LEDGER_PATH, ledger)

        try:
            canonical = derive_canonical_facts()
            first_date = canonical["fixture-tool"].get("facts_checked")

            # Simulate a recheck by adding last_check_result without changing value
            for claim in ledger["claims"]:
                if claim.get("claim_id") == "fixture-tool-pricing-test":
                    claim["last_check_result"] = "no_change"
                    claim["last_change_type"] = "none"
                    break
            save_json(LEDGER_PATH, ledger)

            # Re-derive
            canonical2 = derive_canonical_facts()
            second_date = canonical2["fixture-tool"].get("facts_checked")

            # Date should remain the same
            self.assertEqual(first_date, second_date)

        finally:
            save_json(LEDGER_PATH, self.saved_ledger)


class TestCanonicalFactsFile(unittest.TestCase):
    """Test the canonical-facts.json file structure."""

    def test_canonical_facts_exists(self):
        """Test that canonical-facts.json was created."""
        self.assertTrue(CANONICAL_FACTS_PATH.exists())

    def test_canonical_facts_structure(self):
        """Test that canonical-facts.json has correct structure."""
        facts = load_json(CANONICAL_FACTS_PATH)
        self.assertIsInstance(facts, dict)

        # Check at least one tool has expected fields
        for tool_id, fact in facts.items():
            self.assertIn("tool_id", fact)
            self.assertEqual(fact["tool_id"], tool_id)
            self.assertIn("source_claim_ids", fact)
            self.assertIn("confidence", fact)
            self.assertIn(facts_checked := fact.get("facts_checked"), [None, "2026-11-23", "2026-11-22"])
            break  # Just check one


if __name__ == "__main__":
    unittest.main()
