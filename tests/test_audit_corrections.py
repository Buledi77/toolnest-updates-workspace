import json
import os
import re
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_json(path):
    with open(os.path.join(BASE, path), encoding="utf-8") as f:
        return json.load(f)


def _read_html(path):
    with open(os.path.join(BASE, path), encoding="utf-8") as f:
        return f.read()


class TestAlsoConsiderIdsResolve(unittest.TestCase):
    """Every also_consider ID in task-catalog.json resolves to an existing tool."""

    def test_also_consider_ids_resolve(self):
        tools_data = _load_json("data/tools-v1.json")
        valid_ids = {t["id"] for t in tools_data["tools"]}

        catalog = _load_json("data/recommendations/task-catalog.json")
        for task in catalog["tasks"]:
            for aid in task.get("also_consider", []):
                with self.subTest(task=task["id"], also_consider=aid):
                    self.assertIn(
                        aid,
                        valid_ids,
                        f"also_consider ID '{aid}' in task '{task['id']}' does not resolve to an existing tool",
                    )

    def test_also_consider_ids_in_homepage(self):
        """Also consider IDs embedded in index.html must also resolve."""
        tools_data = _load_json("data/tools-v1.json")
        valid_ids = {t["id"] for t in tools_data["tools"]}

        html = _read_html("index.html")
        # Extract also_consider arrays from the GOALS JavaScript
        matches = re.findall(r"also_consider:\s*\[([^\]]*)\]", html)
        for match in matches:
            ids = re.findall(r'"([^"]+)"', match)
            for aid in ids:
                with self.subTest(also_consider=aid):
                    self.assertIn(
                        aid,
                        valid_ids,
                        f"also_consider ID '{aid}' in index.html does not resolve to an existing tool",
                    )


class TestSparseFiltersHidden(unittest.TestCase):
    """Free Plan and Platform filters are hidden in decision-engine.html."""

    def test_sparse_filters_hidden(self):
        html = _read_html("tools/decision-engine.html")

        # Platform filter group should have display:none
        self.assertRegex(
            html,
            r'de-filter-group[\s\S]*?style="display:none"[\s\S]*?dePlatforms',
            "Platform filter should be hidden with display:none",
        )

        # Free Plan toggle row should have display:none
        self.assertRegex(
            html,
            r'de-toggle-row[\s\S]*?style="display:none"[\s\S]*?deFreePlanToggle',
            "Free Plan toggle should be hidden with display:none",
        )

        # There should be a notice about disabled filters
        self.assertIn("disabled", html.lower(), "Should have a notice about disabled filters")


class TestDataQualityNotInScoring(unittest.TestCase):
    """Data Quality bonus is not present in decision-engine-config.json scoring rules."""

    def test_data_quality_not_in_config(self):
        config = _load_json("data/decision-engine-config.json")
        rule_ids = [r["id"] for r in config["scoring"]["rules"]]
        self.assertNotIn(
            "data_quality_bonus",
            rule_ids,
            "data_quality_bonus should not be in scoring rules",
        )

    def test_data_quality_not_in_html(self):
        html = _read_html("tools/decision-engine.html")
        # The Data Quality scoring block should not exist in the JS
        self.assertNotIn(
            'rule:"Data Quality"',
            html,
            "Data Quality scoring should not appear in decision-engine.html",
        )

    def test_max_score_is_90(self):
        config = _load_json("data/decision-engine-config.json")
        self.assertEqual(
            config["scoring"]["total_max_score"],
            90,
            "Total max score should be 90 after removing Data Quality bonus",
        )


class TestMissingFieldsNoFalsePenalty(unittest.TestCase):
    """Tools with missing useCaseTags/bestFor are not penalized."""

    def test_missing_fields_no_false_penalty(self):
        html = _read_html("tools/decision-engine.html")
        # The transparency note should mention insufficient structured evidence
        self.assertIn(
            "insufficient structured evidence",
            html,
            "Should mention 'insufficient structured evidence' for missing data",
        )


class TestStackExcludesUnknownPrices(unittest.TestCase):
    """Stack Analyzer excludes unknown-price tools from totals."""

    def test_stack_excludes_unknown_prices(self):
        html = _read_html("tools/stack-analyzer.html")
        # getMonthlyEstimate returns null for unknown pricing
        self.assertIn("return null", html)
        # Unknown count tracking exists
        self.assertIn("unknownCount", html)
        # Unknown tools shown separately
        self.assertIn("saUnknownBox", html)


class TestAnnualDiscountVerified(unittest.TestCase):
    """Annual calculation uses verified discount data when present."""

    def test_annual_discount_verified(self):
        html = _read_html("tools/stack-analyzer.html")
        # Should check for annualDiscount in tiers
        self.assertIn("annualDiscount", html)
        # Should label as estimate when no verified discount
        self.assertIn("(estimate)", html)


class TestUrlStateRestoresAfterLoad(unittest.TestCase):
    """URL state restore in Stack Analyzer happens after async data loading."""

    def test_url_state_restores_after_load(self):
        html = _read_html("tools/stack-analyzer.html")
        # restoreUrlState should be called inside loadTools .then()
        # Check that restoreUrlState is NOT called in init()
        init_match = re.search(
            r"function init\(\)\s*\{([^}]+)\}", html, re.DOTALL
        )
        self.assertIsNotNone(init_match, "init() function should exist")
        init_body = init_match.group(1)
        self.assertNotIn(
            "restoreUrlState",
            init_body,
            "restoreUrlState should NOT be called in init()",
        )

        # restoreUrlState should be called inside loadTools .then()
        load_match = re.search(
            r"function loadTools\(\)\s*\{([^}]+\.then\([^)]+\)\.then\([^)]+\)[^}]*?)\}",
            html,
            re.DOTALL,
        )
        if load_match:
            load_body = load_match.group(1)
            self.assertIn(
                "restoreUrlState",
                load_body,
                "restoreUrlState should be called inside loadTools .then() callback",
            )

        # restoreUrlState should call renderSelected to display restored tools
        # Use a more robust regex that handles nested braces
        restore_match = re.search(
            r"function restoreUrlState\(\)\s*\{", html
        )
        self.assertIsNotNone(restore_match, "restoreUrlState function should exist")
        # Extract the function body by finding the matching closing brace
        start = restore_match.end()
        depth = 1
        pos = start
        while pos < len(html) and depth > 0:
            if html[pos] == "{":
                depth += 1
            elif html[pos] == "}":
                depth -= 1
            pos += 1
        restore_body = html[start:pos - 1]
        self.assertIn(
            "renderSelected",
            restore_body,
            "restoreUrlState should call renderSelected to display restored tools",
        )


class TestBetaPagesNoindex(unittest.TestCase):
    """Both beta pages contain noindex,follow robots meta."""

    def test_decision_engine_noindex(self):
        html = _read_html("tools/decision-engine.html")
        self.assertRegex(
            html,
            r'<meta\s+name="robots"\s+content="noindex,?\s*follow">',
            "Decision Engine should have noindex,follow robots meta",
        )

    def test_stack_analyzer_noindex(self):
        html = _read_html("tools/stack-analyzer.html")
        self.assertRegex(
            html,
            r'<meta\s+name="robots"\s+content="noindex,?\s*follow">',
            "Stack Analyzer should have noindex,follow robots meta",
        )


class TestSitemapNoBetaPages(unittest.TestCase):
    """Sitemap does not contain decision-engine or stack-analyzer URLs."""

    def test_sitemap_no_beta_pages(self):
        sitemap = _read_html("sitemap.xml")
        self.assertNotIn(
            "decision-engine",
            sitemap,
            "Sitemap should not contain decision-engine URL",
        )
        self.assertNotIn(
            "stack-analyzer",
            sitemap,
            "Sitemap should not contain stack-analyzer URL",
        )


class TestIndexedUrlsUnchanged(unittest.TestCase):
    """Key indexed URLs remain unchanged in sitemap and canonical tags."""

    def test_indexed_urls_unchanged(self):
        sitemap = _read_html("sitemap.xml")

        # Check that key indexed URL patterns exist
        expected_patterns = [
            "tools/",
            "compare/",
            "alternatives/",
            "best/",
            "category/",
        ]
        for pattern in expected_patterns:
            self.assertIn(
                pattern,
                sitemap,
                f"Sitemap should contain {pattern} URLs",
            )

    def test_homepage_canonical_unchanged(self):
        html = _read_html("index.html")
        self.assertIn(
            'href="https://www.toolnestai.tech/"',
            html,
            "Homepage canonical should be unchanged",
        )

    def test_config_filters_disabled(self):
        """Config marks sparse filters as disabled."""
        config = _load_json("data/decision-engine-config.json")
        platforms = config["filters"]["platforms"]
        self.assertFalse(
            platforms.get("enabled", True),
            "Platform filter should be marked as enabled: false in config",
        )
        free_plan = config["filters"]["hasFreePlan"]
        self.assertFalse(
            free_plan.get("enabled", True),
            "Free Plan filter should be marked as enabled: false in config",
        )


if __name__ == "__main__":
    unittest.main()
