"""
Chart components for Streamlit app using Plotly.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from models.profit import compare_profit


def plot_swe_timeseries(df_awdb: pd.DataFrame) -> go.Figure:
    """
    Plot SWE time series for multiple stations.

    Args:
        df_awdb: DataFrame with columns: date, station_id, wteq_mm

    Returns:
        Plotly figure
    """
    # Select 2-3 representative stations
    stations = df_awdb['station_id'].unique()[:3]
    df_plot = df_awdb[df_awdb['station_id'].isin(stations)].copy()

    # Convert mm to inches for display
    df_plot['wteq_inches'] = df_plot['wteq_mm'] / 25.4

    fig = px.line(
        df_plot,
        x='date',
        y='wteq_inches',
        color='station_id',
        title='Snow Water Equivalent (SWE) - Sierra SNOTEL Stations',
        labels={
            'date': 'Date',
            'wteq_inches': 'SWE (inches)',
            'station_id': 'Station'
        }
    )

    fig.update_layout(
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def plot_price_bands(price_bands: pd.DataFrame) -> go.Figure:
    """
    Plot rice price history with percentile bands.

    Args:
        price_bands: DataFrame with columns: date, price_usd_cwt, p10, median, p90

    Returns:
        Plotly figure
    """
    fig = go.Figure()

    # Add band (shaded area)
    fig.add_trace(go.Scatter(
        x=price_bands['date'],
        y=price_bands['p90'],
        mode='lines',
        name='p90 (High)',
        line=dict(width=0),
        showlegend=False
    ))

    fig.add_trace(go.Scatter(
        x=price_bands['date'],
        y=price_bands['p10'],
        mode='lines',
        name='p10-p90 Band',
        line=dict(width=0),
        fillcolor='rgba(68, 68, 68, 0.2)',
        fill='tonexty',
        showlegend=True
    ))

    # Add median line
    fig.add_trace(go.Scatter(
        x=price_bands['date'],
        y=price_bands['median'],
        mode='lines',
        name='Median',
        line=dict(color='#e74c3c', width=2)
    ))

    # Add actual price points
    fig.add_trace(go.Scatter(
        x=price_bands['date'],
        y=price_bands['price_usd_cwt'],
        mode='markers',
        name='Actual Price',
        marker=dict(size=8, color='#3498db')
    ))

    fig.update_layout(
        title='California Rice Prices with Percentile Bands',
        xaxis_title='Date',
        yaxis_title='Price ($/cwt)',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def plot_breakeven_chart(params: dict, breakeven_price: float) -> go.Figure:
    """
    Plot profit vs water price showing breakeven point.

    Args:
        params: Parameter dict with all decision inputs
        breakeven_price: Breakeven water price

    Returns:
        Plotly figure
    """
    # Generate range of water prices
    water_prices = list(range(0, 1001, 25))

    profit_grow_list = []
    profit_fallow_list = []

    for wp in water_prices:
        result = compare_profit(
            acres=params['acres'],
            expected_yield_cwt_ac=params['expected_yield_cwt_ac'],
            price_usd_cwt=params['price_usd_cwt'],
            var_cost_usd_ac=params['var_cost_usd_ac'],
            fixed_cost_usd=params['fixed_cost_usd'],
            cu_af_per_ac=params['cu_af_per_ac'],
            water_price_usd_af=wp,
            conveyance_loss_frac=params['conveyance_loss_frac'],
            transaction_cost_usd=params['transaction_cost_usd']
        )

        profit_grow_list.append(result['profit_grow'])
        profit_fallow_list.append(result['profit_fallow'])

    fig = go.Figure()

    # Profit from growing (horizontal line)
    fig.add_trace(go.Scatter(
        x=water_prices,
        y=profit_grow_list,
        mode='lines',
        name='Profit (Growing)',
        line=dict(color='#2ecc71', width=3)
    ))

    # Profit from fallowing (increasing line)
    fig.add_trace(go.Scatter(
        x=water_prices,
        y=profit_fallow_list,
        mode='lines',
        name='Profit (Fallowing)',
        line=dict(color='#3498db', width=3)
    ))

    # Add breakeven line
    fig.add_vline(
        x=breakeven_price,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Breakeven: ${breakeven_price:.0f}/af",
        annotation_position="top"
    )

    # Add current price indicator
    current_price = params['water_price_usd_af']
    fig.add_vline(
        x=current_price,
        line_dash="dot",
        line_color="gray",
        annotation_text=f"Current: ${current_price:.0f}/af",
        annotation_position="bottom"
    )

    fig.update_layout(
        title='Profit vs Water Price',
        xaxis_title='Water Price ($/af)',
        yaxis_title='Profit ($)',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def plot_tornado_chart(params: dict) -> go.Figure:
    """
    Create tornado chart for sensitivity analysis.

    Shows impact of ±20% variation in each parameter on profit delta.

    Args:
        params: Parameter dict with all decision inputs

    Returns:
        Plotly figure
    """
    # Base case
    base_result = compare_profit(**params)
    base_delta = base_result['delta']

    # Parameters to vary
    vary_params = {
        'Rice Price': ('price_usd_cwt', params['price_usd_cwt']),
        'Yield': ('expected_yield_cwt_ac', params['expected_yield_cwt_ac']),
        'Water Price': ('water_price_usd_af', params['water_price_usd_af']),
        'Consumptive Use': ('cu_af_per_ac', params['cu_af_per_ac']),
        'Variable Cost': ('var_cost_usd_ac', params['var_cost_usd_ac'])
    }

    results = []

    for label, (param_name, base_value) in vary_params.items():
        # Low case (-20%)
        low_params = params.copy()
        low_params[param_name] = base_value * 0.8
        low_result = compare_profit(**low_params)
        low_impact = low_result['delta'] - base_delta

        # High case (+20%)
        high_params = params.copy()
        high_params[param_name] = base_value * 1.2
        high_result = compare_profit(**high_params)
        high_impact = high_result['delta'] - base_delta

        results.append({
            'parameter': label,
            'low_impact': low_impact,
            'high_impact': high_impact,
            'range': abs(high_impact - low_impact)
        })

    # Sort by range (most sensitive at top)
    df_results = pd.DataFrame(results).sort_values('range', ascending=True)

    fig = go.Figure()

    # Low impact bars (left)
    fig.add_trace(go.Bar(
        y=df_results['parameter'],
        x=df_results['low_impact'],
        name='-20%',
        orientation='h',
        marker=dict(color='#e74c3c'),
        text=[f"${x:,.0f}" for x in df_results['low_impact']],
        textposition='auto'
    ))

    # High impact bars (right)
    fig.add_trace(go.Bar(
        y=df_results['parameter'],
        x=df_results['high_impact'],
        name='+20%',
        orientation='h',
        marker=dict(color='#2ecc71'),
        text=[f"${x:,.0f}" for x in df_results['high_impact']],
        textposition='auto'
    ))

    # Add zero line
    fig.add_vline(x=0, line_dash="dash", line_color="black", line_width=1)

    fig.update_layout(
        title='Sensitivity Analysis: Impact on Profit Delta',
        xaxis_title='Change in Delta ($)',
        yaxis_title='',
        barmode='overlay',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig
