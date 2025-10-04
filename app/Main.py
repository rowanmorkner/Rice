"""
Water-Opt MVP - Streamlit Dashboard

Decision support tool for California rice growers comparing:
- Growing rice (crop revenue - costs)
- Fallowing land and selling water rights (water revenue - reduced costs)
"""

import streamlit as st
from pathlib import Path
import pandas as pd
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.profit import compare_profit, DEFAULT_PARAMS
from models.scenarios import build_hydro_scenarios, build_price_bands, get_scenario_summary

# Page configuration
st.set_page_config(
    page_title="Water-Opt MVP",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for parameters
if 'params' not in st.session_state:
    st.session_state.params = DEFAULT_PARAMS.copy()


def main():
    """Main application entry point."""

    # Header
    st.title("🌾 Water-Opt: Rice Growing Decision Tool")
    st.markdown("*Compare profitability of growing rice vs. fallowing and selling water rights*")

    # Sidebar for navigation
    st.sidebar.title("Navigation")
    tab_selection = st.sidebar.radio(
        "Select Tab:",
        ["Setup", "Hydrology", "Markets", "Decision", "Map", "Compliance"],
        label_visibility="collapsed"
    )

    # Data loading status
    data_dir = Path("data")
    with st.sidebar.expander("📊 Data Status", expanded=False):
        check_data_availability(data_dir)

    # Route to tabs
    if tab_selection == "Setup":
        tab_setup()
    elif tab_selection == "Hydrology":
        tab_hydrology()
    elif tab_selection == "Markets":
        tab_markets()
    elif tab_selection == "Decision":
        tab_decision()
    elif tab_selection == "Map":
        tab_map()
    elif tab_selection == "Compliance":
        tab_compliance()


def check_data_availability(data_dir: Path):
    """Check which data sources are available."""
    sources = {
        "AWDB SWE": data_dir / "stage" / "awdb_swe_daily.parquet",
        "Bulletin 120": data_dir / "stage" / "b120_forecast.parquet",
        "ERS Prices": data_dir / "stage" / "ers_prices.parquet",
        "DWR Crop Map": data_dir / "mart" / "rice_polygons_2022.parquet",
        "CIMIS ETo": data_dir / "stage" / "cimis_daily.parquet"
    }

    for name, path in sources.items():
        if path.exists():
            st.success(f"✓ {name}")
        else:
            st.warning(f"⚠ {name} (not fetched)")

    st.caption("Run `make etl` to fetch data")


def tab_setup():
    """Setup tab: Configure decision parameters."""
    st.header("⚙️ Setup: Decision Parameters")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Field & Production")

        acres = st.number_input(
            "Field Size (acres)",
            min_value=1.0,
            max_value=10000.0,
            value=float(st.session_state.params["acres"]),
            step=10.0,
            help="Total acreage under consideration"
        )

        expected_yield = st.slider(
            "Expected Yield (cwt/acre)",
            min_value=50.0,
            max_value=120.0,
            value=float(st.session_state.params["expected_yield_cwt_ac"]),
            step=5.0,
            help="Expected rice yield in hundredweight per acre"
        )

        price_usd_cwt = st.slider(
            "Rice Price ($/cwt)",
            min_value=10.0,
            max_value=35.0,
            value=float(st.session_state.params["price_usd_cwt"]),
            step=0.50,
            help="Market price for rice"
        )

        st.subheader("Costs")

        var_cost = st.number_input(
            "Variable Cost ($/acre)",
            min_value=0.0,
            max_value=2000.0,
            value=float(st.session_state.params["var_cost_usd_ac"]),
            step=50.0,
            help="Seed, fertilizer, pesticides, labor, fuel"
        )

        fixed_cost = st.number_input(
            "Fixed Cost ($)",
            min_value=0.0,
            max_value=100000.0,
            value=float(st.session_state.params["fixed_cost_usd"]),
            step=500.0,
            help="Equipment, insurance, overhead"
        )

    with col2:
        st.subheader("Water Parameters")

        cu_af_per_ac = st.slider(
            "Consumptive Use (af/acre)",
            min_value=2.0,
            max_value=6.0,
            value=float(st.session_state.params["cu_af_per_ac"]),
            step=0.1,
            help="Water saved by not growing (TODO: Replace with SSEBop data)"
        )

        water_price = st.slider(
            "Water Market Price ($/af)",
            min_value=0.0,
            max_value=1000.0,
            value=float(st.session_state.params["water_price_usd_af"]),
            step=10.0,
            help="Market price for selling water rights"
        )

        conveyance_loss = st.slider(
            "Conveyance Loss (%)",
            min_value=0.0,
            max_value=50.0,
            value=float(st.session_state.params["conveyance_loss_frac"] * 100),
            step=1.0,
            help="Water lost in transport to buyer"
        )

        transaction_cost = st.number_input(
            "Transaction Cost ($)",
            min_value=0.0,
            max_value=10000.0,
            value=float(st.session_state.params["transaction_cost_usd"]),
            step=100.0,
            help="Legal, administrative costs for water sale"
        )

    # Update session state
    st.session_state.params.update({
        "acres": acres,
        "expected_yield_cwt_ac": expected_yield,
        "price_usd_cwt": price_usd_cwt,
        "var_cost_usd_ac": var_cost,
        "fixed_cost_usd": fixed_cost,
        "cu_af_per_ac": cu_af_per_ac,
        "water_price_usd_af": water_price,
        "conveyance_loss_frac": conveyance_loss / 100.0,
        "transaction_cost_usd": transaction_cost
    })

    # Quick preview
    st.divider()
    st.subheader("📋 Parameter Summary")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Field Size", f"{acres:,.0f} acres")
        st.metric("Yield", f"{expected_yield:.0f} cwt/ac")
    with col2:
        st.metric("Rice Price", f"${price_usd_cwt:.2f}/cwt")
        st.metric("Water Price", f"${water_price:.0f}/af")
    with col3:
        st.metric("Variable Cost", f"${var_cost:.0f}/ac")
        st.metric("CU", f"{cu_af_per_ac:.1f} af/ac")


def tab_hydrology():
    """Hydrology tab: Display SWE history and scenarios."""
    st.header("💧 Hydrology: Water Supply Outlook")

    data_dir = Path("data")
    awdb_path = data_dir / "stage" / "awdb_swe_daily.parquet"
    scenarios_path = data_dir / "mart" / "hydro_scenarios.parquet"

    if not awdb_path.exists():
        st.warning("⚠️ AWDB data not available. Run `make etl` to fetch data.")
        st.info("This tab will show:\n- Historical SWE trends from Sierra SNOTEL stations\n- Dry/Median/Wet water year scenarios")
        return

    # Load data
    df_awdb = pd.read_parquet(awdb_path)
    df_awdb['date'] = pd.to_datetime(df_awdb['date'])

    # SWE time series plot
    st.subheader("📈 Snow Water Equivalent (SWE) History")

    from app.components.charts import plot_swe_timeseries
    fig = plot_swe_timeseries(df_awdb)
    st.plotly_chart(fig, use_container_width=True)

    # Hydro scenarios table
    st.subheader("📊 Water Year Scenarios")

    if scenarios_path.exists():
        df_scenarios = pd.read_parquet(scenarios_path)

        # Filter for key months (April-July)
        df_display = df_scenarios[df_scenarios['month'].isin([4, 5, 6, 7])].copy()
        df_display['allocation_pct'] = (df_display['allocation_index'] * 100).astype(int)

        # Pivot for display
        pivot = df_display.pivot_table(
            index='month',
            columns='scenario',
            values='allocation_pct',
            aggfunc='first'
        )[['dry', 'median', 'wet']]

        pivot.index = pivot.index.map({4: 'April', 5: 'May', 6: 'June', 7: 'July'})
        pivot.columns = ['Dry (%)', 'Median (%)', 'Wet (%)']

        st.dataframe(pivot, use_container_width=True)

        st.caption("Allocation index represents estimated water supply availability (0-100%)")
    else:
        st.info("Hydro scenarios not generated yet.")


def tab_markets():
    """Markets tab: Display ERS price history and bands."""
    st.header("💰 Markets: Rice Price Outlook")

    data_dir = Path("data")
    ers_path = data_dir / "stage" / "ers_prices.parquet"

    if not ers_path.exists():
        st.warning("⚠️ ERS price data not available. Run `make etl` to fetch data.")
        st.info("This tab will show:\n- Historical rice price trends\n- Price bands (p10/median/p90)")
        return

    # Load data
    df_ers = pd.read_parquet(ers_path)
    price_bands = build_price_bands(df_ers, data_dir=data_dir)

    # Price summary
    col1, col2, col3 = st.columns(3)

    latest = price_bands.iloc[-1]

    with col1:
        st.metric("Low Price (p10)", f"${latest['p10']:.2f}/cwt",
                  help="10th percentile - pessimistic scenario")
    with col2:
        st.metric("Median Price", f"${latest['median']:.2f}/cwt",
                  help="50th percentile - typical scenario")
    with col3:
        st.metric("High Price (p90)", f"${latest['p90']:.2f}/cwt",
                  help="90th percentile - optimistic scenario")

    # Price band chart
    st.subheader("📈 Price History with Bands")

    from app.components.charts import plot_price_bands
    fig = plot_price_bands(price_bands)
    st.plotly_chart(fig, use_container_width=True)

    st.caption("Price bands represent 10th, 50th, and 90th percentiles")


def tab_decision():
    """Decision tab: Show profit comparison and sensitivity analysis."""
    st.header("🎯 Decision: Profit Analysis")

    # Calculate profits
    result = compare_profit(**st.session_state.params)

    # Profit cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Profit (Growing)",
            f"${result['profit_grow']:,.0f}",
            help="Revenue from rice crop minus all costs"
        )

    with col2:
        st.metric(
            "Profit (Fallowing)",
            f"${result['profit_fallow']:,.0f}",
            help="Revenue from water sale minus fixed costs"
        )

    with col3:
        delta = result['delta']
        st.metric(
            "Delta (Grow - Fallow)",
            f"${delta:,.0f}",
            delta=f"${delta:,.0f}",
            delta_color="normal",
            help="Positive means growing is more profitable"
        )

    # Recommendation
    st.divider()

    if result['delta'] > 0:
        st.success(f"✅ **Recommendation: GROW RICE** (${result['delta']:,.0f} advantage)")
    else:
        st.info(f"💧 **Recommendation: FALLOW & SELL WATER** (${-result['delta']:,.0f} advantage)")

    # Breakeven water price
    st.divider()
    st.subheader("⚖️ Breakeven Analysis")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.metric(
            "Breakeven Water Price",
            f"${result['breakeven_water_price_usd_af']:,.2f}/af",
            help="Water price where profits are equal"
        )

        current_price = st.session_state.params['water_price_usd_af']
        if current_price < result['breakeven_water_price_usd_af']:
            st.caption(f"Current price (${current_price:.0f}/af) is below breakeven → Grow")
        else:
            st.caption(f"Current price (${current_price:.0f}/af) is above breakeven → Fallow")

    with col2:
        from app.components.charts import plot_breakeven_chart
        fig = plot_breakeven_chart(
            st.session_state.params,
            result['breakeven_water_price_usd_af']
        )
        st.plotly_chart(fig, use_container_width=True)

    # Sensitivity analysis
    st.divider()
    st.subheader("🌪️ Sensitivity Analysis")

    from app.components.charts import plot_tornado_chart
    fig = plot_tornado_chart(st.session_state.params)
    st.plotly_chart(fig, use_container_width=True)

    st.caption("Shows how profit delta changes with ±20% variation in each parameter")

    # Export button
    st.divider()
    if st.button("📥 Export Results", type="primary"):
        export_results(result)


def tab_map():
    """Map tab: Show rice polygons colored by decision."""
    st.header("🗺️ Map: Field-Level Decisions")

    data_dir = Path("data")
    polygons_path = data_dir / "mart" / "rice_polygons_2022.parquet"

    if not polygons_path.exists():
        st.warning("⚠️ DWR crop map data not available. Run `make etl` to fetch data.")
        st.info("This tab will show:\n- Rice field locations in Sacramento Valley\n- Fields colored by decision (green=grow, blue=fallow)")
        return

    # Load rice polygons
    df_polygons = pd.read_parquet(polygons_path)

    st.subheader(f"📍 {len(df_polygons):,} Rice Fields in Sacramento Valley")
    st.caption(f"Total: {df_polygons['acres'].sum():,.0f} acres")

    # Apply decision uniformly to all polygons
    result = compare_profit(**st.session_state.params)
    decision = "grow" if result['delta'] > 0 else "fallow"
    color = "#2ecc71" if decision == "grow" else "#3498db"

    # Summary stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Decision", decision.upper())
    with col2:
        st.metric("Total Acres", f"{df_polygons['acres'].sum():,.0f}")
    with col3:
        st.metric("Fields", f"{len(df_polygons):,}")

    # Map visualization
    st.subheader("🗺️ Field Map")

    from app.components.map import plot_rice_polygons_map
    fig = plot_rice_polygons_map(df_polygons, decision, color)
    st.plotly_chart(fig, use_container_width=True)

    st.caption(f"All fields shown as '{decision}' based on current parameters (uniform application)")


def tab_compliance():
    """Compliance tab: Regulatory guardrails and disclaimers."""
    st.header("⚖️ Compliance: Regulatory Considerations")

    st.markdown("""
    ## Water Transfer Guardrails

    California water transfers from cropland idling are subject to multiple regulatory
    requirements and constraints:

    ### 1. Consumptive Use Requirement

    - Transfers must be based on **conserved consumptive use**, not just applied water
    - Only water that would have been consumed by the crop can be transferred
    - Conveyance losses must be accounted for in transfer calculations

    ### 2. "New Water" Requirement

    - Transferred water must represent **"new" or "conserved" water**
    - Cannot simply be existing return flows reclassified as transferable water
    - Historical use patterns and return flow obligations must be maintained

    ### 3. Injury Protection (Water Code §1706)

    - Transfers cannot injure other legal users of water
    - Must maintain historical return flows to downstream users
    - Groundwater recharge patterns must be considered

    ### 4. Environmental Review

    - Transfers may require CEQA review depending on scale and duration
    - Biological opinions may be required for impacts on listed species
    - Delta water quality and flow requirements must be met

    ### 5. Hearing Thresholds

    Short-term transfers (≤1 year) involving cropland idling may trigger
    State Water Resources Control Board hearings if:

    - Transfer exceeds **20% of historical use** in any year
    - Cumulative transfers exceed certain volume thresholds
    - There are objections from other water users

    ### 6. Local District Rules

    - Your irrigation district may have additional rules on:
      - Fallowing restrictions (maximum % of district land)
      - Approval processes and fees
      - Timing and notification requirements
      - Conservation plans and reporting

    ## Data Limitations

    This tool uses the following simplifications:

    - **Consumptive Use**: Default 4.0 af/acre (typical CA rice range: 3.5-4.5 af/ac)
      - TODO: Replace with SSEBop actual ET data for field-specific estimates
    - **Conveyance Loss**: User-adjustable, typically 10-15%
    - **Price Data**: Based on USDA ERS Rice Outlook (stub data in MVP)
    - **Water Prices**: User-specified, not market data

    ## Disclaimer

    ⚠️ **This tool is for educational and planning purposes only.**

    - Results are estimates based on simplified models and incomplete data
    - Actual profitability depends on many factors not captured here
    - Water transfer feasibility requires detailed analysis by qualified professionals

    **Before making any decisions:**

    1. Consult with your **irrigation district** on transfer rules and approval processes
    2. Engage a **water rights attorney** familiar with California water law
    3. Contact the **State Water Resources Control Board** about permit requirements
    4. Consider engaging a **certified hydrologist** for consumptive use calculations
    5. Review **environmental compliance** requirements (CEQA, ESA, etc.)

    ## Resources

    - [CA Water Code §1706-1732](https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=WAT&sectionNum=1706) (Water Transfers)
    - [SWRCB Water Transfer Portal](https://www.waterboards.ca.gov/waterrights/water_issues/programs/water_transfers/)
    - [DWR Water Transfers](https://water.ca.gov/Programs/All-Programs/Water-Transfers)
    - [USDA NRCS Consumptive Use Guide](https://www.nrcs.usda.gov/)

    ---

    *Water-Opt MVP v0.1.0 - Educational Tool for CA Rice Growers*
    """)


def export_results(result: dict):
    """Export decision results to CSV and charts to PNG."""
    export_dir = Path("data/mart/exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    # Export CSV
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    csv_data = {
        "timestamp": timestamp,
        **st.session_state.params,
        **result
    }

    df_export = pd.DataFrame([csv_data])
    csv_path = export_dir / f"decision_{timestamp}.csv"
    df_export.to_csv(csv_path, index=False)

    st.success(f"✅ Results exported to {csv_path}")
    st.caption("CSV contains all input parameters and profit calculations")


if __name__ == "__main__":
    main()
