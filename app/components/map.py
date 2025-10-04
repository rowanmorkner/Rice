"""
Map components for Streamlit app using Plotly.
"""

import pandas as pd
import plotly.graph_objects as go


def plot_rice_polygons_map(
    df_polygons: pd.DataFrame,
    decision: str,
    color: str
) -> go.Figure:
    """
    Plot rice polygon centroids on a map.

    Args:
        df_polygons: DataFrame with columns: centroid_x, centroid_y, acres, county
        decision: "grow" or "fallow"
        color: Hex color code

    Returns:
        Plotly figure
    """
    # Sample polygons if too many (for performance)
    if len(df_polygons) > 2000:
        df_plot = df_polygons.sample(n=2000, random_state=42)
        caption = f"Showing 2,000 of {len(df_polygons):,} fields (sampled for performance)"
    else:
        df_plot = df_polygons
        caption = f"Showing all {len(df_polygons):,} fields"

    # Create hover text
    df_plot = df_plot.copy()
    df_plot['hover_text'] = df_plot.apply(
        lambda row: f"Acres: {row['acres']:.1f}<br>Decision: {decision}<br>County: {row.get('county', 'N/A')}",
        axis=1
    )

    fig = go.Figure()

    fig.add_trace(go.Scattermapbox(
        lon=df_plot['centroid_x'],
        lat=df_plot['centroid_y'],
        mode='markers',
        marker=dict(
            size=5,
            color=color,
            opacity=0.6
        ),
        text=df_plot['hover_text'],
        hovertemplate='%{text}<extra></extra>',
        name=decision.capitalize()
    ))

    # Calculate center point
    center_lat = df_plot['centroid_y'].mean()
    center_lon = df_plot['centroid_x'].mean()

    fig.update_layout(
        mapbox=dict(
            style='open-street-map',
            center=dict(lat=center_lat, lon=center_lon),
            zoom=8
        ),
        title=dict(
            text=f'Sacramento Valley Rice Fields - {decision.upper()}<br><sub>{caption}</sub>',
            x=0.5,
            xanchor='center'
        ),
        showlegend=True,
        height=600,
        margin=dict(l=0, r=0, t=60, b=0)
    )

    return fig
