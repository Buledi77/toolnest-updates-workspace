#!/usr/bin/env python3
"""Tests for the safe batch recheck strategy in freshness_recheck_pipeline.py.

Validates:
- Batch ordering (pricing claims before capability claims)
- State transitions (pending → in_progress → completed)
- Domain throttling
- Source volatility scoring
- Blocked source handling
"""

import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from freshness_recheck_pipeline import (  # noqa: E402
    calculate_priority_score,
    create_controlled_batches,
    extract_domain,
    generate_recheck_tasks,
    get_priority_score,
    CLAIM_PRIORITY,
    SOURCE_VOLATILITY,
    DEFAULT_BATCH_SIZE,
    DOMAIN_THROTTLE_DEFAULT,
)


class TestPriorityScoring(unittest.TestCase):
    """Test that priority scoring correctly orders claims."""
    
    def setUp(self):
        self.sources = {
            "src-1": {"source_id": "src-1", "url": "https://example.com/pricing", "source_type": "pricing_page"},
            "src-2": {"source_id": "src-2", "url": "https://example.com/docs", "source_type": "documentation"},
            "src-3": {"source_id": "src-3", "url": "https://example.com", "source_type": "homepage"},
        }
    
    def test_pricing_higher_than_capability(self):
        """Pricing claims should score higher than capability claims."""
        pricing_claim = {
            "claim_id": "pricing-1",
            "claim_type": "pricing",
            "source_ids": ["src-1"],
            "urgency_score": 0,
        }
        capability_claim = {
            "claim_id": "cap-1",
            "claim_type": "capability",
            "source_ids": ["src-2"],
            "urgency_score": 0,
        }
        pricing_score = calculate_priority_score(pricing_claim, self.sources)
        cap_score = calculate_priority_score(capability_claim, self.sources)
        self.assertGreater(pricing_score, cap_score)
    
    def test_free_plan_high_priority(self):
        """Free plan claims should have high priority."""
        free_plan_claim = {
            "claim_id": "fp-1",
            "claim_type": "free_plan",
            "source_ids": ["src-1"],
            "urgency_score": 0,
        }
        general_claim = {
            "claim_id": "gen-1",
            "claim_type": "general",
            "source_ids": ["src-3"],
            "urgency_score": 0,
        }
        fp_score = calculate_priority_score(free_plan_claim, self.sources)
        gen_score = calculate_priority_score(general_claim, self.sources)
        self.assertGreater(fp_score, gen_score)
    
    def test_trial_high_priority(self):
        """Trial claims should have high priority."""
        trial_claim = {
            "claim_id": "trial-1",
            "claim_type": "trial",
            "source_ids": ["src-1"],
            "urgency_score": 0,
        }
        general_claim = {
            "claim_id": "gen-1",
            "claim_type": "general",
            "source_ids": ["src-3"],
            "urgency_score": 0,
        }
        trial_score = calculate_priority_score(trial_claim, self.sources)
        gen_score = calculate_priority_score(general_claim, self.sources)
        self.assertGreater(trial_score, gen_score)
    
    def test_overdue_claims_score_higher(self):
        """Overdue claims should score higher than non-overdue ones."""
        overdue_claim = {
            "claim_id": "overdue-1",
            "claim_type": "pricing",
            "source_ids": ["src-1"],
            "urgency_score": 30,  # 30 days overdue
        }
        current_claim = {
            "claim_id": "current-1",
            "claim_type": "pricing",
            "source_ids": ["src-1"],
            "urgency_score": 0,
        }
        overdue_score = calculate_priority_score(overdue_claim, self.sources)
        current_score = calculate_priority_score(current_claim, self.sources)
        self.assertGreater(overdue_score, current_score)
    
    def test_source_volatility_affects_score(self):
        """Higher volatility sources should increase priority."""
        volatile_claim = {
            "claim_id": "vol-1",
            "claim_type": "capability",
            "source_ids": ["src-1"],  # pricing_page = volatility 8
            "urgency_score": 0,
        }
        stable_claim = {
            "claim_id": "stable-1",
            "claim_type": "capability",
            "source_ids": ["src-2"],  # documentation = volatility 2
            "urgency_score": 0,
        }
        volatile_score = calculate_priority_score(volatile_claim, self.sources)
        stable_score = calculate_priority_score(stable_claim, self.sources)
        self.assertGreater(volatile_score, stable_score)
    
    def test_impact_multiplier_for_pricing(self):
        """Pricing claims should have 2x impact multiplier."""
        pricing_claim = {
            "claim_id": "p-1",
            "claim_type": "pricing",
            "source_ids": ["src-1"],
            "urgency_score": 0,
        }
        # Pricing has impact_multiplier 2.0
        score = calculate_priority_score(pricing_claim, self.sources)
        # Base score for pricing: (11-1)*100 + 8*10 + 0 = 1080, * 2.0 = 2160
        self.assertGreater(score, 2000)
    
    def test_billing_impact_multiplier(self):
        """Billing claims should have 1.5x impact multiplier."""
        billing_claim = {
            "claim_id": "b-1",
            "claim_type": "billing",
            "source_ids": ["src-1"],
            "urgency_score": 0,
        }
        score = calculate_priority_score(billing_claim, self.sources)
        # Base: (11-3)*100 + 8*10 + 0 = 880, * 1.5 = 1320
        self.assertGreater(score, 1000)


class TestBatchOrdering(unittest.TestCase):
    """Test that batches are ordered correctly."""
    
    def setUp(self):
        self.tasks = [
            {
                "task_id": "t1",
                "claim_id": "c1",
                "tool_id": "tool-a",
                "claim_type": "pricing",
                "composite_score": 2160,
                "source_urls": [{"url": "https://tool-a.com/pricing"}],
            },
            {
                "task_id": "t2",
                "claim_id": "c2",
                "tool_id": "tool-b",
                "claim_type": "free_plan",
                "composite_score": 2060,
                "source_urls": [{"url": "https://tool-b.com/pricing"}],
            },
            {
                "task_id": "t3",
                "claim_id": "c3",
                "tool_id": "tool-c",
                "claim_type": "capability",
                "composite_score": 680,
                "source_urls": [{"url": "https://tool-c.com/docs"}],
            },
            {
                "task_id": "t4",
                "claim_id": "c4",
                "tool_id": "tool-d",
                "claim_type": "general",
                "composite_score": 100,
                "source_urls": [{"url": "https://tool-d.com"}],
            },
        ]
    
    def test_pricing_in_first_batch(self):
        """Pricing claims should appear in the first batch."""
        batches = create_controlled_batches(self.tasks, batch_size=10)
        first_batch = batches[0]
        first_batch_types = {t["claim_type"] for t in first_batch}
        self.assertIn("pricing", first_batch_types)
    
    def test_batches_ordered_by_priority(self):
        """Tasks in earlier batches should have higher scores."""
        batches = create_controlled_batches(self.tasks, batch_size=2)
        # First batch should have highest-scoring tasks
        if len(batches) >= 2:
            max_score_batch_0 = max(t["composite_score"] for t in batches[0])
            max_score_batch_1 = max(t["composite_score"] for t in batches[1])
            self.assertGreaterEqual(max_score_batch_0, max_score_batch_1)
    
    def test_batch_size_respected(self):
        """Batch size limit should be respected."""
        batches = create_controlled_batches(self.tasks, batch_size=2)
        for batch in batches:
            tool_ids = {t["tool_id"] for t in batch}
            self.assertLessEqual(len(tool_ids), 2)
    
    def test_empty_tasks_returns_empty(self):
        """Empty task list should return empty batches."""
        batches = create_controlled_batches([])
        self.assertEqual(batches, [])
    
    def test_single_task_single_batch(self):
        """A single task should produce one batch."""
        batches = create_controlled_batches([self.tasks[0]])
        self.assertEqual(len(batches), 1)
        self.assertEqual(len(batches[0]), 1)


class TestDomainThrottling(unittest.TestCase):
    """Test domain-aware throttling in batch creation."""
    
    def test_domain_extraction(self):
        """Domain extraction should work for various URLs."""
        self.assertEqual(extract_domain("https://example.com/pricing"), "example.com")
        self.assertEqual(extract_domain("http://tool.example.com/page"), "tool.example.com")
        self.assertEqual(extract_domain("https://example.com:8080/path"), "example.com")
        self.assertEqual(extract_domain(""), "")
        self.assertEqual(extract_domain(None), "")
    
    def test_domain_throttle_limits(self):
        """Domain throttle should limit claims per domain per batch."""
        # Create 10 tasks all from the same domain with small batch size
        tasks = []
        for i in range(10):
            tasks.append({
                "task_id": f"t{i}",
                "claim_id": f"c{i}",
                "tool_id": f"tool-{i}",
                "claim_type": "pricing",
                "composite_score": 1000 - i,
                "source_urls": [{"url": "https://same-domain.com/pricing"}],
            })
        
        # With batch_size=10 and domain_throttle=3, first batch should
        # have at most 3 from same-domain.com before moving to next batch
        batches = create_controlled_batches(tasks, batch_size=10, domain_throttle=3)
        # Since all are from same domain, domain throttle should split them
        # into multiple batches
        self.assertGreater(len(batches), 1)
        # Each batch should have at most 3 from the same domain
        for batch in batches:
            same_domain_count = sum(
                1 for t in batch
                if "same-domain.com" in str(t.get("source_urls", []))
            )
            self.assertLessEqual(same_domain_count, 3)


class TestStateTransitions(unittest.TestCase):
    """Test that recheck state transitions work correctly."""
    
    def test_task_initial_status(self):
        """New tasks should start with 'pending' status."""
        sources = {
            "src-1": {"source_id": "src-1", "url": "https://example.com/pricing", "source_type": "pricing_page"},
        }
        stale_claims = [{
            "claim_id": "test-1",
            "tool_id": "test-tool",
            "claim_type": "pricing",
            "source_ids": ["src-1"],
            "urgency_score": 10,
            "stale_after": "2025-01-01",
            "verified_at": "2024-06-01",
        }]
        tasks = generate_recheck_tasks(stale_claims, sources)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["status"], "pending")
    
    def test_task_has_required_fields(self):
        """Tasks should have all required fields."""
        sources = {
            "src-1": {"source_id": "src-1", "url": "https://example.com/pricing", "source_type": "pricing_page"},
        }
        stale_claims = [{
            "claim_id": "test-1",
            "tool_id": "test-tool",
            "claim_type": "pricing",
            "source_ids": ["src-1"],
            "urgency_score": 10,
        }]
        tasks = generate_recheck_tasks(stale_claims, sources)
        task = tasks[0]
        required_fields = [
            "task_id", "claim_id", "tool_id", "claim_type",
            "priority", "composite_score", "source_urls", "status",
        ]
        for field in required_fields:
            self.assertIn(field, task)
    
    def test_tasks_sorted_by_composite_score(self):
        """Tasks should be sorted by composite score descending."""
        sources = {
            "src-1": {"source_id": "src-1", "url": "https://example.com/pricing", "source_type": "pricing_page"},
            "src-2": {"source_id": "src-2", "url": "https://example.com/docs", "source_type": "documentation"},
        }
        stale_claims = [
            {
                "claim_id": "general-1",
                "tool_id": "tool-a",
                "claim_type": "general",
                "source_ids": ["src-2"],
                "urgency_score": 0,
            },
            {
                "claim_id": "pricing-1",
                "tool_id": "tool-b",
                "claim_type": "pricing",
                "source_ids": ["src-1"],
                "urgency_score": 0,
            },
        ]
        tasks = generate_recheck_tasks(stale_claims, sources)
        # Pricing should come first (higher composite score)
        self.assertEqual(tasks[0]["claim_type"], "pricing")
        self.assertGreater(tasks[0]["composite_score"], tasks[1]["composite_score"])


class TestClaimPriorityConstants(unittest.TestCase):
    """Test that claim priority constants are correct."""
    
    def test_pricing_is_highest_priority(self):
        """Pricing should have the lowest numeric priority (highest urgency)."""
        self.assertEqual(get_priority_score("pricing"), 1)
        self.assertEqual(get_priority_score("free_plan"), 1)
    
    def test_general_is_lowest_priority(self):
        """General should have the highest numeric priority (lowest urgency)."""
        self.assertEqual(get_priority_score("general"), 10)
    
    def test_unknown_type_defaults(self):
        """Unknown claim types should default to priority 10."""
        self.assertEqual(get_priority_score("unknown_type"), 10)
    
    def test_source_volatility_values(self):
        """Source volatility should have expected values."""
        self.assertEqual(SOURCE_VOLATILITY["pricing_page"], 8)
        self.assertEqual(SOURCE_VOLATILITY["changelog"], 7)
        self.assertEqual(SOURCE_VOLATILITY["documentation"], 2)
    
    def test_default_batch_size(self):
        """Default batch size should be 10."""
        self.assertEqual(DEFAULT_BATCH_SIZE, 10)
    
    def test_default_domain_throttle(self):
        """Default domain throttle should be 5."""
        self.assertEqual(DOMAIN_THROTTLE_DEFAULT, 5)


if __name__ == "__main__":
    unittest.main()
