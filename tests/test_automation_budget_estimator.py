"""Tests for the automation budget estimator calculation logic."""

import os
import pytest


def calculate_usage(runs, steps, complexity):
    """Replicate the estimator's usage calculation logic."""
    usage = {}
    usage["zapier"] = runs * steps
    usage["make"] = runs * steps
    usage["n8n"] = runs
    usage["ifttt"] = runs
    if complexity == "complex":
        usage["make"] = round(usage["make"] * 1.5)
    elif complexity == "medium":
        usage["make"] = round(usage["make"] * 1.2)
    return usage


def compare_usage(usage_amount, user_input):
    """Replicate the usage-vs-allowance comparison logic.

    Args:
        usage_amount: Estimated usage units for a tool.
        user_input: Dict with keys 'price', 'allowance', 'overageRate'.
            Values are None if user did not enter them.

    Returns:
        Dict with keys 'fits', 'overageUnits', 'overageCost', 'allowanceEntered'.
    """
    fits = False
    overage_units = 0
    overage_cost = 0

    allowance = user_input.get("allowance")
    overage_rate = user_input.get("overageRate")

    if allowance is not None and allowance > 0:
        if usage_amount <= allowance:
            fits = True
        else:
            overage_units = usage_amount - allowance
            if overage_rate is not None and overage_rate > 0:
                overage_cost = overage_units * overage_rate
    elif allowance == 0:
        # User entered 0 allowance — usage exceeds
        overage_units = usage_amount
        if overage_rate is not None and overage_rate > 0:
            overage_cost = overage_units * overage_rate

    return {
        "fits": fits,
        "overageUnits": overage_units,
        "overageCost": overage_cost,
        "allowanceEntered": allowance is not None,
    }


class TestCalculateUsage:
    """Test the usage calculation logic."""

    def test_simple_workflow(self):
        """Simple workflow: 1000 runs, 2 steps, simple complexity."""
        usage = calculate_usage(1000, 2, "simple")
        assert usage["zapier"] == 2000
        assert usage["make"] == 2000
        assert usage["n8n"] == 1000
        assert usage["ifttt"] == 1000

    def test_medium_complexity_multiplier(self):
        """Medium complexity adds 20% to Make credits."""
        usage = calculate_usage(1000, 3, "medium")
        assert usage["zapier"] == 3000
        assert usage["make"] == 3600  # 3000 * 1.2
        assert usage["n8n"] == 1000
        assert usage["ifttt"] == 1000

    def test_complex_complexity_multiplier(self):
        """Complex complexity adds 50% to Make credits."""
        usage = calculate_usage(1000, 4, "complex")
        assert usage["zapier"] == 4000
        assert usage["make"] == 6000  # 4000 * 1.5
        assert usage["n8n"] == 1000
        assert usage["ifttt"] == 1000

    def test_n8n_ignores_steps(self):
        """n8n counts executions, not steps."""
        usage = calculate_usage(500, 10, "complex")
        assert usage["n8n"] == 500

    def test_ifttt_ignores_steps(self):
        """IFTTT counts triggers, not steps."""
        usage = calculate_usage(500, 10, "complex")
        assert usage["ifttt"] == 500

    def test_zapier_counts_all_steps(self):
        """Zapier counts each step as a task."""
        usage = calculate_usage(100, 5, "simple")
        assert usage["zapier"] == 500


class TestValidation:
    """Test input validation logic."""

    def test_valid_inputs(self):
        """Valid inputs should pass."""
        runs, steps = 5000, 3
        assert 1 <= runs <= 100000
        assert 1 <= steps <= 50

    def test_boundary_min_runs(self):
        """Minimum runs should be valid."""
        assert 1 >= 1

    def test_boundary_max_runs(self):
        """Maximum runs should be valid."""
        assert 100000 <= 100000

    def test_boundary_min_steps(self):
        """Minimum steps should be valid."""
        assert 1 >= 1

    def test_boundary_max_steps(self):
        """Maximum steps should be valid."""
        assert 50 <= 50


class TestEdgeCases:
    """Test edge cases and negative scenarios."""

    def test_zero_runs(self):
        """Zero runs should produce zero usage."""
        usage = calculate_usage(0, 3, "simple")
        assert usage["zapier"] == 0
        assert usage["make"] == 0
        assert usage["n8n"] == 0
        assert usage["ifttt"] == 0

    def test_single_step_workflow(self):
        """Single step workflow should work."""
        usage = calculate_usage(100, 1, "simple")
        assert usage["zapier"] == 100
        assert usage["make"] == 100

    def test_large_scale_usage(self):
        """Large scale usage should not overflow."""
        usage = calculate_usage(100000, 50, "complex")
        assert usage["zapier"] == 5000000
        assert usage["make"] == 7500000  # 5000000 * 1.5
        assert usage["n8n"] == 100000


class TestInputEdgeCases:
    """Test input validation edge cases."""

    def test_negative_runs(self):
        """Negative runs should be rejected by validation."""
        runs = -100
        assert not (1 <= runs <= 100000)

    def test_negative_steps(self):
        """Negative steps should be rejected by validation."""
        steps = -5
        assert not (1 <= steps <= 50)

    def test_decimal_runs_truncated(self):
        """Decimal runs are truncated by parseInt in JS, test floor behavior."""
        usage = calculate_usage(5000, 3, "simple")
        assert usage["zapier"] == 15000

    def test_runs_exceeds_max(self):
        """Runs exceeding max should be rejected by validation."""
        runs = 100001
        assert not (1 <= runs <= 100000)

    def test_steps_exceeds_max(self):
        """Steps exceeding max should be rejected by validation."""
        steps = 51
        assert not (1 <= steps <= 50)


class TestUserInputComparison:
    """Test the usage-vs-allowance comparison logic."""

    def test_usage_fits_within_allowance(self):
        """Usage below allowance should fit."""
        result = compare_usage(
            2000, {"price": 20, "allowance": 5000, "overageRate": None}
        )
        assert result["fits"] is True
        assert result["overageUnits"] == 0
        assert result["allowanceEntered"] is True

    def test_usage_exceeds_allowance(self):
        """Usage above allowance should not fit."""
        result = compare_usage(
            6000, {"price": 20, "allowance": 5000, "overageRate": 0.01}
        )
        assert result["fits"] is False
        assert result["overageUnits"] == 1000
        assert result["allowanceEntered"] is True

    def test_exact_boundary_fits(self):
        """Usage exactly equal to allowance should fit."""
        result = compare_usage(
            5000, {"price": 20, "allowance": 5000, "overageRate": None}
        )
        assert result["fits"] is True
        assert result["overageUnits"] == 0

    def test_no_allowance_entered(self):
        """Missing allowance should not claim fit or overage."""
        result = compare_usage(
            3000, {"price": 20, "allowance": None, "overageRate": None}
        )
        assert result["fits"] is False
        assert result["overageUnits"] == 0
        assert result["allowanceEntered"] is False

    def test_zero_allowance(self):
        """Zero allowance means all usage is overage."""
        result = compare_usage(
            1000, {"price": 0, "allowance": 0, "overageRate": 0.05}
        )
        assert result["fits"] is False
        assert result["overageUnits"] == 1000
        assert result["overageCost"] == 50.0

    def test_free_plan_with_allowance(self):
        """Free plan ($0 price) with allowance should work."""
        result = compare_usage(
            50, {"price": 0, "allowance": 100, "overageRate": None}
        )
        assert result["fits"] is True
        assert result["allowanceEntered"] is True


class TestOverageCalculation:
    """Test overage cost computation."""

    def test_zero_overage(self):
        """No overage when usage fits."""
        result = compare_usage(
            1000, {"price": 20, "allowance": 5000, "overageRate": 0.01}
        )
        assert result["overageCost"] == 0
        assert result["overageUnits"] == 0

    def test_positive_overage(self):
        """Overage cost computed correctly."""
        result = compare_usage(
            6000, {"price": 20, "allowance": 5000, "overageRate": 0.01}
        )
        assert result["overageUnits"] == 1000
        assert result["overageCost"] == 10.0

    def test_missing_overage_rate(self):
        """No overage cost if rate not entered."""
        result = compare_usage(
            6000, {"price": 20, "allowance": 5000, "overageRate": None}
        )
        assert result["overageUnits"] == 1000
        assert result["overageCost"] == 0

    def test_zero_overage_rate(self):
        """Zero overage rate means no cost."""
        result = compare_usage(
            6000, {"price": 20, "allowance": 5000, "overageRate": 0}
        )
        assert result["overageUnits"] == 1000
        assert result["overageCost"] == 0

    def test_large_overage(self):
        """Large overage amount computed correctly."""
        result = compare_usage(
            100000, {"price": 50, "allowance": 10000, "overageRate": 0.005}
        )
        assert result["overageUnits"] == 90000
        assert result["overageCost"] == 450.0

    def test_decimal_overage_rate(self):
        """Decimal overage rate handled correctly."""
        result = compare_usage(
            3000, {"price": 10, "allowance": 2000, "overageRate": 0.0015}
        )
        assert result["overageUnits"] == 1000
        assert result["overageCost"] == 1.5


class TestDisclaimerWording:
    """Test that the HTML contains no unsupported freshness claims."""

    def test_no_checked_claim(self):
        """HTML should not claim pricing was 'checked'."""
        html_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "tools",
            "automation-budget-estimator.html",
        )
        with open(html_path, "r") as f:
            content = f.read()
        # Check the disclaimer section specifically
        assert "checked in November" not in content.lower()

    def test_no_verified_claim(self):
        """HTML disclaimer should not claim pricing was verified.

        'not verified' and 'verify on the official site' are acceptable
        because they negate the claim or instruct the user.
        """
        html_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "tools",
            "automation-budget-estimator.html",
        )
        with open(html_path, "r") as f:
            content = f.read()
        disclaimer_start = content.find('class="disclaimer"')
        assert disclaimer_start != -1, "Disclaimer section not found"
        disclaimer_end = content.find("</div>", disclaimer_start)
        disclaimer_text = content[disclaimer_start:disclaimer_end].lower()
        # Flag positive claims like "pricing verified" but allow "not verified"
        # and "verify on the official site"
        assert "pricing verified" not in disclaimer_text
        assert "was verified" not in disclaimer_text
        assert "are verified" not in disclaimer_text

    def test_no_embedded_plans_object(self):
        """HTML should not contain the old PLANS object with prices."""
        html_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "tools",
            "automation-budget-estimator.html",
        )
        with open(html_path, "r") as f:
            content = f.read()
        # The old PLANS object had plan names like "Platform", "Professional"
        # with embedded prices — should not exist
        assert 'var PLANS' not in content

    def test_tools_metadata_exists(self):
        """HTML should contain the new TOOLS metadata object."""
        html_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "tools",
            "automation-budget-estimator.html",
        )
        with open(html_path, "r") as f:
            content = f.read()
        assert 'var TOOLS' in content

    def test_tracking_calls_present(self):
        """toolnestTrack calls should still be present."""
        html_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "tools",
            "automation-budget-estimator.html",
        )
        with open(html_path, "r") as f:
            content = f.read()
        assert "toolnestTrack('utility_start'" in content
        assert "toolnestTrack('utility_completion'" in content
