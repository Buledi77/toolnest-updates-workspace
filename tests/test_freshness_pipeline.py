#!/usr/bin/env python3
"""Tests for the freshness recheck pipeline."""

import copy
import json
import sys
import unittest
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from freshness_recheck_pipeline import (  # noqa: E402
    classify_claim,
    generate_recheck_tasks,
    get_priority_score,
    load_freshness_policy,
    run_recheck_pipeline,
    update_ledger_for_recheck,
    update_v2_freshness,
)


class TestClassifyClaim(unittest.TestCase):
    """Test claim classification logic."""

    def setUp(self):
        self.policy = load_freshness_policy()
        self.today = date(2026, 11, 23)

    def test_currently_verified_claim(self):
        claim = {
            "claim_id": "test-pricing",
            "claim_type": "pricing",
            "stale_after": "2027-01-01",
            "verified_at": "2026-10-01",
        }
        status, urgency = classify_claim(claim, self.policy, self.today)
        self.assertEqual(status, "VERIFIED_CURRENTLY")
        self.assertLess(urgency, 0)  # negative = days until stale

    def test_stale_claim(self):
        claim = {
            "claim_id": "test-pricing-stale",
            "claim_type": "pricing",
            "stale_after": "2026-01-01",
            "verified_at": "2025-10-01",
        }
        status, urgency = classify_claim(claim, self.policy, self.today)
        self.assertEqual(status, "NEEDS_RECHECK")
        self.assertGreater(urgency, 0)

    def test_claim_without_dates(self):
        claim = {
            "claim_id": "test-no-dates",
            "claim_type": "general",
        }
        status, urgency = classify_claim(claim, self.policy, self.today)
        self.assertEqual(status, "UNKNOWN")
        self.assertEqual(urgency, 0)

    def test_pricing_threshold(self):
        """Pricing claims expire after 90 days."""
        verified = self.today - timedelta(days=100)
        claim = {
            "claim_id": "test-pricing-old",
            "claim_type": "pricing",
            "verified_at": verified.isoformat(),
        }
        status, urgency = classify_claim(claim, self.policy, self.today)
        self.assertEqual(status, "NEEDS_RECHECK")

    def test_capability_threshold(self):
        """Capability claims expire after 180 days."""
        verified = self.today - timedelta(days=200)
        claim = {
            "claim_id": "test-capability-old",
            "claim_type": "capabilities",
            "verified_at": verified.isoformat(),
        }
        status, urgency = classify_claim(claim, self.policy, self.today)
        self.assertEqual(status, "NEEDS_RECHECK")

    def test_capability_within_threshold(self):
        """Capability claims within 180 days are current."""
        verified = self.today - timedelta(days=100)
        claim = {
            "claim_id": "test-capability-fresh",
            "claim_type": "capability",
            "verified_at": verified.isoformat(),
        }
        status, urgency = classify_claim(claim, self.policy, self.today)
        self.assertEqual(status, "VERIFIED_CURRENTLY")


class TestPriorityScoring(unittest.TestCase):
    """Test claim priority scoring."""

    def test_pricing_is_highest_priority(self):
        self.assertEqual(get_priority_score("pricing"), 1)

    def test_plan_limit_is_high_priority(self):
        self.assertEqual(get_priority_score("plan_limit"), 2)

    def test_capability_is_medium_priority(self):
        self.assertEqual(get_priority_score("capability"), 5)

    def test_general_is_lowest_priority(self):
        self.assertEqual(get_priority_score("general"), 10)

    def test_unknown_type_defaults_to_lowest(self):
        self.assertEqual(get_priority_score("unknown_type"), 10)


class TestRecheckTasks(unittest.TestCase):
    """Test recheck task generation."""

    def setUp(self):
        self.sources = {
            "source-1": {"source_id": "source-1", "url": "https://example.com/pricing", "source_type": "official_pricing"},
            "source-2": {"source_id": "source-2", "url": "https://example.com/features", "source_type": "official_product"},
        }

    def test_generates_tasks_for_stale_claims(self):
        stale_claims = [
            {
                "claim_id": "test-pricing-stale",
                "tool_id": "test-tool",
                "claim_type": "pricing",
                "source_ids": ["source-1"],
                "urgency_score": 30,
                "stale_after": "2026-01-01",
                "verified_at": "2025-10-01",
            },
            {
                "claim_id": "test-capability-stale",
                "tool_id": "test-tool",
                "claim_type": "capability",
                "source_ids": ["source-2"],
                "urgency_score": 20,
                "stale_after": "2026-06-01",
                "verified_at": "2025-01-01",
            },
        ]
        tasks = generate_recheck_tasks(stale_claims, self.sources)
        self.assertEqual(len(tasks), 2)
        # Pricing should come first (higher priority)
        self.assertEqual(tasks[0]["claim_id"], "test-pricing-stale")
        self.assertEqual(tasks[1]["claim_id"], "test-capability-stale")

    def test_task_has_source_urls(self):
        stale_claims = [
            {
                "claim_id": "test-pricing",
                "tool_id": "test-tool",
                "claim_type": "pricing",
                "source_ids": ["source-1"],
                "urgency_score": 10,
            }
        ]
        tasks = generate_recheck_tasks(stale_claims, self.sources)
        self.assertEqual(len(tasks[0]["source_urls"]), 1)
        self.assertEqual(tasks[0]["source_urls"][0]["url"], "https://example.com/pricing")

    def test_empty_claims(self):
        tasks = generate_recheck_tasks([], self.sources)
        self.assertEqual(len(tasks), 0)


class TestLedgerUpdate(unittest.TestCase):
    """Test evidence ledger updates."""

    def test_updates_stale_claims(self):
        ledger = {
            "claims": [
                {
                    "claim_id": "test-1",
                    "claim_type": "pricing",
                    "status": "verified",
                    "verified_at": "2025-01-01",
                    "stale_after": "2025-04-01",
                },
                {
                    "claim_id": "test-2",
                    "claim_type": "capability",
                    "status": "verified",
                    "verified_at": "2026-01-01",
                    "stale_after": "2026-07-01",
                },
            ]
        }
        claim_ids = {"test-1"}
        as_of = date(2026, 11, 23)
        updated = update_ledger_for_recheck(ledger, claim_ids, as_of)
        self.assertEqual(updated, 1)
        # test-1 should be updated
        claim1 = next(c for c in ledger["claims"] if c["claim_id"] == "test-1")
        self.assertEqual(claim1["status"], "needs_review")
        self.assertEqual(claim1["verified_at"], "2026-11-23")
        # test-2 should be unchanged
        claim2 = next(c for c in ledger["claims"] if c["claim_id"] == "test-2")
        self.assertEqual(claim2["status"], "verified")

    def test_no_updates_for_empty_set(self):
        ledger = {
            "claims": [
                {"claim_id": "test-1", "claim_type": "pricing", "status": "verified"}
            ]
        }
        updated = update_ledger_for_recheck(ledger, set(), date(2026, 11, 23))
        self.assertEqual(updated, 0)


class TestV2FreshnessUpdate(unittest.TestCase):
    """Test v2 record freshness updates."""

    def test_updates_freshness_fields(self):
        records = [
            {
                "identity": {"id": "test-tool"},
                "freshness": {
                    "last_verified_at": "2025-01-01T00:00:00Z",
                    "next_review_at": "2025-04-01T00:00:00Z",
                    "stale_fields": ["pricing"],
                },
            }
        ]
        tool_ids = {"test-tool"}
        as_of = date(2026, 11, 23)
        updated = update_v2_freshness(records, tool_ids, as_of)
        self.assertEqual(updated, 1)
        freshness = records[0]["freshness"]
        self.assertEqual(freshness["stale_fields"], [])
        # next_review_at should be ~90 days from as_of
        expected_next = as_of + timedelta(days=90)
        actual_next = datetime.fromisoformat(freshness["next_review_at"].replace("Z", "+00:00")).date()
        self.assertEqual(actual_next, expected_next)

    def test_skips_non_matching_tools(self):
        records = [
            {
                "identity": {"id": "other-tool"},
                "freshness": {"last_verified_at": "2025-01-01T00:00:00Z"},
            }
        ]
        tool_ids = {"test-tool"}
        updated = update_v2_freshness(records, tool_ids, date(2026, 11, 23))
        self.assertEqual(updated, 0)


class TestPipelineIntegration(unittest.TestCase):
    """Integration tests for the full pipeline."""

    def test_pipeline_returns_report(self):
        report = run_recheck_pipeline(as_of="2026-11-23")
        self.assertIn("summary", report)
        self.assertIn("recheck_tasks", report)
        self.assertIn("tools_without_claims", report)
        self.assertIn("overdue_tool_reviews", report)

    def test_pipeline_summary_counts(self):
        report = run_recheck_pipeline(as_of="2026-11-23")
        summary = report["summary"]
        self.assertGreater(summary["total_claims"], 0)
        self.assertGreater(summary["total_tools"], 0)
        self.assertEqual(
            summary["total_claims"],
            summary["status_counts"]["VERIFIED_CURRENTLY"]
            + summary["status_counts"]["NEEDS_RECHECK"]
            + summary["status_counts"]["UNKNOWN"]
            + summary["status_counts"]["NOT_COLLECTED"],
        )

    def test_pipeline_no_apply_does_not_modify(self):
        """Dry run should not modify any files."""
        # Just verify it runs without error
        report = run_recheck_pipeline(as_of="2026-11-23", apply=False)
        self.assertFalse(report["summary"]["applied_updates"])


if __name__ == "__main__":
    unittest.main()
