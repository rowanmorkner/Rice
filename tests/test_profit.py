"""
Unit tests for profit calculation models.

Tests cover:
- Positive delta for reasonable parameters
- Breakeven math correctness
- Edge cases and validation
"""

import pytest
from models.profit import (
    compute_profit_grow,
    compute_profit_fallow,
    compute_breakeven_water_price,
    compare_profit,
    DEFAULT_PARAMS
)


class TestProfitGrow:
    """Tests for compute_profit_grow function."""

    def test_positive_profit(self):
        """Test that reasonable parameters yield positive profit."""
        profit = compute_profit_grow(
            acres=100,
            expected_yield_cwt_ac=85,
            price_usd_cwt=19.0,
            var_cost_usd_ac=650,
            fixed_cost_usd=5000
        )
        assert profit > 0, "Profit should be positive with reasonable parameters"
        assert profit == 91500.0, f"Expected $91,500, got ${profit}"

    def test_zero_acres(self):
        """Test that zero acres yields negative profit (fixed costs)."""
        profit = compute_profit_grow(
            acres=0,
            expected_yield_cwt_ac=85,
            price_usd_cwt=19.0,
            var_cost_usd_ac=650,
            fixed_cost_usd=5000
        )
        assert profit == -5000.0, "With zero acres, profit = -fixed_cost"

    def test_high_costs_negative_profit(self):
        """Test that very high costs yield negative profit."""
        profit = compute_profit_grow(
            acres=100,
            expected_yield_cwt_ac=85,
            price_usd_cwt=19.0,
            var_cost_usd_ac=2000,  # Very high variable cost
            fixed_cost_usd=50000  # Very high fixed cost
        )
        assert profit < 0, "Profit should be negative with excessive costs"


class TestProfitFallow:
    """Tests for compute_profit_fallow function."""

    def test_positive_profit_high_water_price(self):
        """Test that high water price yields positive fallow profit."""
        profit = compute_profit_fallow(
            acres=100,
            cu_af_per_ac=4.0,
            water_price_usd_af=500,  # High water price
            conveyance_loss_frac=0.10,
            transaction_cost_usd=500,
            fixed_cost_usd=5000
        )
        assert profit > 0, "High water price should yield positive fallow profit"

    def test_zero_water_price(self):
        """Test that zero water price yields negative profit."""
        profit = compute_profit_fallow(
            acres=100,
            cu_af_per_ac=4.0,
            water_price_usd_af=0,
            conveyance_loss_frac=0.10,
            transaction_cost_usd=500,
            fixed_cost_usd=5000
        )
        assert profit < 0, "Zero water price should yield negative profit"

    def test_conveyance_loss_reduces_revenue(self):
        """Test that higher conveyance loss reduces profit."""
        profit_low_loss = compute_profit_fallow(
            acres=100,
            cu_af_per_ac=4.0,
            water_price_usd_af=200,
            conveyance_loss_frac=0.10,
            transaction_cost_usd=500,
            fixed_cost_usd=5000
        )

        profit_high_loss = compute_profit_fallow(
            acres=100,
            cu_af_per_ac=4.0,
            water_price_usd_af=200,
            conveyance_loss_frac=0.30,  # Higher loss
            transaction_cost_usd=500,
            fixed_cost_usd=5000
        )

        assert profit_low_loss > profit_high_loss, \
            "Lower conveyance loss should yield higher profit"


class TestBreakevenWaterPrice:
    """Tests for compute_breakeven_water_price function."""

    def test_breakeven_correctness(self):
        """Test that breakeven water price equalizes profits."""
        acres = 100
        expected_yield_cwt_ac = 85
        price_usd_cwt = 19.0
        var_cost_usd_ac = 650
        fixed_cost_usd = 5000
        cu_af_per_ac = 4.0
        conveyance_loss_frac = 0.10
        transaction_cost_usd = 500

        # Calculate breakeven
        breakeven = compute_breakeven_water_price(
            acres=acres,
            expected_yield_cwt_ac=expected_yield_cwt_ac,
            price_usd_cwt=price_usd_cwt,
            var_cost_usd_ac=var_cost_usd_ac,
            fixed_cost_usd=fixed_cost_usd,
            cu_af_per_ac=cu_af_per_ac,
            conveyance_loss_frac=conveyance_loss_frac,
            transaction_cost_usd=transaction_cost_usd
        )

        # Calculate profits at breakeven
        profit_grow = compute_profit_grow(
            acres=acres,
            expected_yield_cwt_ac=expected_yield_cwt_ac,
            price_usd_cwt=price_usd_cwt,
            var_cost_usd_ac=var_cost_usd_ac,
            fixed_cost_usd=fixed_cost_usd
        )

        profit_fallow = compute_profit_fallow(
            acres=acres,
            cu_af_per_ac=cu_af_per_ac,
            water_price_usd_af=breakeven,
            conveyance_loss_frac=conveyance_loss_frac,
            transaction_cost_usd=transaction_cost_usd,
            fixed_cost_usd=fixed_cost_usd
        )

        # Profits should be equal within rounding error
        assert abs(profit_grow - profit_fallow) < 10.0, \
            f"Profits should be equal at breakeven: grow=${profit_grow:.2f}, fallow=${profit_fallow:.2f}"

    def test_breakeven_positive(self):
        """Test that breakeven price is positive for reasonable parameters."""
        breakeven = compute_breakeven_water_price(
            acres=100,
            expected_yield_cwt_ac=85,
            price_usd_cwt=19.0,
            var_cost_usd_ac=650,
            fixed_cost_usd=5000,
            cu_af_per_ac=4.0,
            conveyance_loss_frac=0.10,
            transaction_cost_usd=500
        )
        assert breakeven > 0, "Breakeven price should be positive"
        assert 200 < breakeven < 400, \
            f"Breakeven price should be reasonable (got ${breakeven:.2f}/af)"

    def test_breakeven_infinite_with_zero_water(self):
        """Test that breakeven is infinite with zero deliverable water."""
        breakeven = compute_breakeven_water_price(
            acres=100,
            expected_yield_cwt_ac=85,
            price_usd_cwt=19.0,
            var_cost_usd_ac=650,
            fixed_cost_usd=5000,
            cu_af_per_ac=0.0,  # No water to sell
            conveyance_loss_frac=0.10,
            transaction_cost_usd=500
        )
        assert breakeven == float('inf'), "Breakeven should be infinite with no water"


class TestCompareProfit:
    """Tests for compare_profit function."""

    def test_positive_delta_reasonable_params(self):
        """Test that growing is profitable with reasonable water price."""
        result = compare_profit(
            acres=100,
            expected_yield_cwt_ac=85,
            price_usd_cwt=19.0,
            var_cost_usd_ac=650,
            fixed_cost_usd=5000,
            cu_af_per_ac=4.0,
            water_price_usd_af=200,  # Reasonable water price
            conveyance_loss_frac=0.10,
            transaction_cost_usd=500
        )

        assert result["delta"] > 0, \
            "Growing should be more profitable with low water price"
        assert result["profit_grow"] > result["profit_fallow"], \
            "Grow profit should exceed fallow profit"

    def test_negative_delta_high_water_price(self):
        """Test that fallowing is profitable with high water price."""
        result = compare_profit(
            acres=100,
            expected_yield_cwt_ac=85,
            price_usd_cwt=19.0,
            var_cost_usd_ac=650,
            fixed_cost_usd=5000,
            cu_af_per_ac=4.0,
            water_price_usd_af=500,  # Very high water price
            conveyance_loss_frac=0.10,
            transaction_cost_usd=500
        )

        assert result["delta"] < 0, \
            "Fallowing should be more profitable with high water price"
        assert result["profit_fallow"] > result["profit_grow"], \
            "Fallow profit should exceed grow profit"

    def test_default_params(self):
        """Test that default parameters work correctly."""
        result = compare_profit(**DEFAULT_PARAMS)

        assert "profit_grow" in result
        assert "profit_fallow" in result
        assert "delta" in result
        assert "breakeven_water_price_usd_af" in result

        assert isinstance(result["profit_grow"], (int, float))
        assert isinstance(result["profit_fallow"], (int, float))
        assert isinstance(result["delta"], (int, float))
        assert isinstance(result["breakeven_water_price_usd_af"], (int, float))

    def test_breakeven_at_computed_price(self):
        """Test that delta is near zero at breakeven water price."""
        # First compute breakeven
        result = compare_profit(**DEFAULT_PARAMS)
        breakeven_price = result["breakeven_water_price_usd_af"]

        # Then test at that price
        result_at_breakeven = compare_profit(
            acres=DEFAULT_PARAMS["acres"],
            expected_yield_cwt_ac=DEFAULT_PARAMS["expected_yield_cwt_ac"],
            price_usd_cwt=DEFAULT_PARAMS["price_usd_cwt"],
            var_cost_usd_ac=DEFAULT_PARAMS["var_cost_usd_ac"],
            fixed_cost_usd=DEFAULT_PARAMS["fixed_cost_usd"],
            cu_af_per_ac=DEFAULT_PARAMS["cu_af_per_ac"],
            water_price_usd_af=breakeven_price,
            conveyance_loss_frac=DEFAULT_PARAMS["conveyance_loss_frac"],
            transaction_cost_usd=DEFAULT_PARAMS["transaction_cost_usd"]
        )

        assert abs(result_at_breakeven["delta"]) < 10.0, \
            f"Delta should be near zero at breakeven (got ${result_at_breakeven['delta']:.2f})"

    def test_increasing_rice_price_favors_growing(self):
        """Test that higher rice prices favor growing."""
        result_low = compare_profit(
            acres=100,
            expected_yield_cwt_ac=85,
            price_usd_cwt=15.0,  # Low rice price
            var_cost_usd_ac=650,
            fixed_cost_usd=5000,
            cu_af_per_ac=4.0,
            water_price_usd_af=200,
            conveyance_loss_frac=0.10,
            transaction_cost_usd=500
        )

        result_high = compare_profit(
            acres=100,
            expected_yield_cwt_ac=85,
            price_usd_cwt=25.0,  # High rice price
            var_cost_usd_ac=650,
            fixed_cost_usd=5000,
            cu_af_per_ac=4.0,
            water_price_usd_af=200,
            conveyance_loss_frac=0.10,
            transaction_cost_usd=500
        )

        assert result_high["delta"] > result_low["delta"], \
            "Higher rice price should increase advantage of growing"
