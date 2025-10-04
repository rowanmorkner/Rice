"""
Profit calculation model for grow vs fallow decision.

Compares profitability of growing rice versus fallowing land and selling water rights.
Includes breakeven water price calculation.
"""

from typing import Dict, Optional


def compute_profit_grow(
    acres: float,
    expected_yield_cwt_ac: float,
    price_usd_cwt: float,
    var_cost_usd_ac: float,
    fixed_cost_usd: float
) -> float:
    """
    Calculate profit from growing rice.

    Args:
        acres: Field size in acres
        expected_yield_cwt_ac: Expected yield in hundredweight per acre (cwt/ac)
        price_usd_cwt: Rice price in USD per hundredweight
        var_cost_usd_ac: Variable costs in USD per acre (seed, fertilizer, labor, fuel)
        fixed_cost_usd: Fixed costs in USD (equipment, overhead, insurance)

    Returns:
        Profit in USD

    Formula:
        Revenue = acres × yield × price
        Variable Costs = acres × var_cost
        Total Cost = Variable Costs + Fixed Costs
        Profit = Revenue - Total Cost
    """
    revenue = acres * expected_yield_cwt_ac * price_usd_cwt
    variable_costs = acres * var_cost_usd_ac
    total_cost = variable_costs + fixed_cost_usd

    profit = revenue - total_cost

    return profit


def compute_profit_fallow(
    acres: float,
    cu_af_per_ac: float,
    water_price_usd_af: float,
    conveyance_loss_frac: float,
    transaction_cost_usd: float,
    fixed_cost_usd: float
) -> float:
    """
    Calculate profit from fallowing and selling water rights.

    Args:
        acres: Field size in acres
        cu_af_per_ac: Consumptive use in acre-feet per acre (water saved by not growing)
        water_price_usd_af: Market price for water in USD per acre-foot
        conveyance_loss_frac: Fraction of water lost in conveyance (0-1)
        transaction_cost_usd: Fixed transaction costs for water sale (legal, admin)
        fixed_cost_usd: Fixed costs still incurred when fallowing (reduced maintenance)

    Returns:
        Profit in USD

    Formula:
        Water Saved = acres × cu_af_per_ac
        Deliverable Water = Water Saved × (1 - conveyance_loss)
        Revenue = Deliverable Water × water_price - transaction_cost
        Profit = Revenue - fixed_cost

    Note:
        cu_af_per_ac default is typically 3.5-4.5 af/ac for CA rice
        TODO: Replace with actual ET data from SSEBop when available
    """
    water_saved_af = acres * cu_af_per_ac
    deliverable_water_af = water_saved_af * (1.0 - conveyance_loss_frac)
    revenue = deliverable_water_af * water_price_usd_af - transaction_cost_usd
    profit = revenue - fixed_cost_usd

    return profit


def compute_breakeven_water_price(
    acres: float,
    expected_yield_cwt_ac: float,
    price_usd_cwt: float,
    var_cost_usd_ac: float,
    fixed_cost_usd: float,
    cu_af_per_ac: float,
    conveyance_loss_frac: float,
    transaction_cost_usd: float
) -> float:
    """
    Calculate breakeven water price where profit_grow == profit_fallow.

    Args:
        acres: Field size in acres
        expected_yield_cwt_ac: Expected yield in hundredweight per acre
        price_usd_cwt: Rice price in USD per hundredweight
        var_cost_usd_ac: Variable costs in USD per acre
        fixed_cost_usd: Fixed costs in USD
        cu_af_per_ac: Consumptive use in acre-feet per acre
        conveyance_loss_frac: Fraction of water lost in conveyance (0-1)
        transaction_cost_usd: Transaction costs for water sale

    Returns:
        Breakeven water price in USD per acre-foot

    Formula:
        Set profit_grow == profit_fallow and solve for water_price_usd_af:

        profit_grow = (acres × yield × rice_price) - (acres × var_cost) - fixed_cost

        profit_fallow = (acres × cu × (1 - loss) × water_price - transaction) - fixed_cost

        Setting equal and solving for water_price:
        water_price = [(acres × yield × rice_price) - (acres × var_cost) + transaction]
                      / [acres × cu × (1 - loss)]
    """
    # Calculate profit_grow numerator components
    revenue_grow = acres * expected_yield_cwt_ac * price_usd_cwt
    cost_grow = acres * var_cost_usd_ac

    # Calculate deliverable water
    deliverable_water_af = acres * cu_af_per_ac * (1.0 - conveyance_loss_frac)

    if deliverable_water_af <= 0:
        # No water to sell, breakeven is undefined
        return float('inf')

    # Solve for water_price_usd_af
    # profit_grow = profit_fallow
    # revenue_grow - cost_grow - fixed = (deliverable × price - transaction) - fixed
    # revenue_grow - cost_grow = deliverable × price - transaction
    # price = (revenue_grow - cost_grow + transaction) / deliverable

    breakeven = (revenue_grow - cost_grow + transaction_cost_usd) / deliverable_water_af

    return breakeven


def compare_profit(
    acres: float,
    expected_yield_cwt_ac: float,
    price_usd_cwt: float,
    var_cost_usd_ac: float,
    fixed_cost_usd: float,
    cu_af_per_ac: float = 4.0,  # Default CA rice consumptive use
    water_price_usd_af: float = 0.0,
    conveyance_loss_frac: float = 0.10,  # 10% conveyance loss
    transaction_cost_usd: float = 500.0  # Legal/admin costs
) -> Dict[str, float]:
    """
    Compare profit from growing rice versus fallowing and selling water.

    Args:
        acres: Field size in acres
        expected_yield_cwt_ac: Expected yield in hundredweight per acre
        price_usd_cwt: Rice price in USD per hundredweight
        var_cost_usd_ac: Variable costs in USD per acre
        fixed_cost_usd: Fixed costs in USD
        cu_af_per_ac: Consumptive use in acre-feet per acre (default 4.0)
        water_price_usd_af: Market price for water in USD per acre-foot
        conveyance_loss_frac: Fraction of water lost in conveyance (default 0.10)
        transaction_cost_usd: Transaction costs for water sale (default 500)

    Returns:
        Dict with:
            profit_grow: Profit from growing rice (USD)
            profit_fallow: Profit from fallowing (USD)
            delta: Difference (profit_grow - profit_fallow)
            breakeven_water_price_usd_af: Water price where profits are equal

    Example:
        >>> result = compare_profit(
        ...     acres=100,
        ...     expected_yield_cwt_ac=85,
        ...     price_usd_cwt=19.0,
        ...     var_cost_usd_ac=650,
        ...     fixed_cost_usd=5000,
        ...     cu_af_per_ac=4.0,
        ...     water_price_usd_af=200,
        ...     conveyance_loss_frac=0.10,
        ...     transaction_cost_usd=500
        ... )
        >>> result['profit_grow']
        91500.0
        >>> result['delta'] > 0  # Growing is more profitable
        True
    """
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
        water_price_usd_af=water_price_usd_af,
        conveyance_loss_frac=conveyance_loss_frac,
        transaction_cost_usd=transaction_cost_usd,
        fixed_cost_usd=fixed_cost_usd
    )

    delta = profit_grow - profit_fallow

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

    return {
        "profit_grow": profit_grow,
        "profit_fallow": profit_fallow,
        "delta": delta,
        "breakeven_water_price_usd_af": breakeven
    }


# Default parameters (typical CA rice operation)
DEFAULT_PARAMS = {
    "acres": 100,
    "expected_yield_cwt_ac": 85,  # CA average ~85 cwt/ac
    "price_usd_cwt": 19.0,  # Medium-grain estimate
    "var_cost_usd_ac": 650,  # Seed, fertilizer, pesticide, labor, fuel
    "fixed_cost_usd": 5000,  # Equipment, insurance, overhead
    "cu_af_per_ac": 4.0,  # TODO: Replace with SSEBop ET data
    "water_price_usd_af": 200,  # Market water price
    "conveyance_loss_frac": 0.10,  # 10% loss in conveyance
    "transaction_cost_usd": 500  # Legal/admin for water sale
}
