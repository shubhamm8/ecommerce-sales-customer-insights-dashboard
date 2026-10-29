"""
Interactive Plotly Visualizations Engine.

Employs professional design principles:
- Cohesive color scheme: Navy (#0f172a), Ocean Blue (#0284c7), Teal (#0d9488), Accent Gold (#f59e0b).
- Polished typography, clean grid lines, transparent backgrounds.
- Responsive margins and clear hover templates.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


COLOR_PRIMARY = "#0284c7"    # Sky / Ocean Blue
COLOR_NAVY = "#0f172a"       # Deep Slate Navy
COLOR_TEAL = "#0d9488"       # Teal
COLOR_AMBER = "#f59e0b"      # Warning / Accent Gold
COLOR_ROSE = "#e11d48"       # Danger / Anomaly Rose
COLOR_MUTED = "#64748b"      # Muted Grey

SEGMENT_COLORS = [
    "#0284c7",  # Blue
    "#0d9488",  # Teal
    "#8b5cf6",  # Violet
    "#f59e0b",  # Amber
    "#e11d48",  # Rose
    "#10b981",  # Emerald
]


def apply_custom_layout(fig: go.Figure, title: str = "", height: int = 420) -> go.Figure:
    """Apply consistent styling across all dashboard figures."""
    fig.update_layout(
        title=dict(text=title, font=dict(family="Inter, sans-serif", size=16, color=COLOR_NAVY, weight=600)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248, 250, 252, 0.6)",
        font=dict(family="Inter, sans-serif", color="#334155"),
        margin=dict(l=40, r=40, t=50, b=40),
        height=height,
        hoverlabel=dict(bgcolor="#ffffff", font_size=12, font_family="Inter, sans-serif"),
        xaxis=dict(showgrid=True, gridcolor="#e2e8f0", linecolor="#cbd5e1"),
        yaxis=dict(showgrid=True, gridcolor="#e2e8f0", linecolor="#cbd5e1"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def plot_sales_trend(sales_ts_df: pd.DataFrame, title: str = "Sales Revenue Trajectory") -> go.Figure:
    """Interactive line and area chart for historical revenue."""
    if sales_ts_df.empty:
        fig = go.Figure()
        return apply_custom_layout(fig, title)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sales_ts_df["Date"],
        y=sales_ts_df["Revenue"],
        mode="lines",
        name="Net Revenue ($)",
        line=dict(color=COLOR_PRIMARY, width=2.5),
        fill="tozeroy",
        fillcolor="rgba(2, 132, 199, 0.08)",
        hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Revenue:</b> $%{y:,.2f}<extra></extra>",
    ))

    fig.update_yaxes(tickprefix="$")
    return apply_custom_layout(fig, title)


def plot_top_products(prod_df: pd.DataFrame, title: str = "Top Products by Revenue", top_n: int = 10) -> go.Figure:
    """Horizontal bar chart of top catalog items."""
    if prod_df.empty:
        return apply_custom_layout(go.Figure(), title)

    df_plot = prod_df.head(top_n).sort_values(by="Revenue", ascending=True)

    fig = go.Figure(go.Bar(
        x=df_plot["Revenue"],
        y=df_plot["Description"],
        orientation="h",
        marker=dict(
            color=df_plot["Revenue"],
            colorscale=[[0, "#38bdf8"], [1, "#0369a1"]],
            showscale=False,
        ),
        hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.2f}<br>Units: %{customdata:,}<extra></extra>",
        customdata=df_plot["UnitsSold"] if "UnitsSold" in df_plot.columns else df_plot["Revenue"],
    ))

    fig.update_xaxes(tickprefix="$")
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return apply_custom_layout(fig, title, height=max(380, top_n * 32))


def plot_country_distribution(geo_df: pd.DataFrame, title: str = "Global Revenue by Country") -> go.Figure:
    """Donut chart for geographic revenue split."""
    if geo_df.empty:
        return apply_custom_layout(go.Figure(), title)

    df_plot = geo_df.copy()
    if len(df_plot) > 6:
        top_5 = df_plot.head(5)
        others_rev = df_plot.iloc[5:]["Revenue"].sum()
        others_row = pd.DataFrame([{"Country": "Other Markets", "Revenue": others_rev}])
        df_plot = pd.concat([top_5, others_row], ignore_index=True)

    fig = px.pie(
        df_plot,
        names="Country",
        values="Revenue",
        hole=0.55,
        color_discrete_sequence=px.colors.sequential.Blues_r,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label", hovertemplate="<b>%{label}</b><br>Revenue: $%{value:,.2f}<extra></extra>")
    return apply_custom_layout(fig, title, height=380)


def plot_forecast(
    historical_series: pd.Series,
    future_df: pd.DataFrame,
    comparison_df: Optional[pd.DataFrame] = None,
    title: str = "Sales Forecast with Prediction Intervals",
) -> go.Figure:
    """Combined historical, test backtest, and future forecast intervals plot."""
    fig = go.Figure()

    # Historical
    fig.add_trace(go.Scatter(
        x=historical_series.index,
        y=historical_series.values,
        mode="lines",
        name="Historical Sales",
        line=dict(color="#64748b", width=1.5),
        hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Actual:</b> $%{y:,.2f}<extra></extra>",
    ))

    # Test backtest
    if comparison_df is not None and not comparison_df.empty:
        fig.add_trace(go.Scatter(
            x=comparison_df["Date"],
            y=comparison_df["Model_Pred"],
            mode="lines",
            name="Validation Model Fit",
            line=dict(color="#0d9488", width=2, dash="dot"),
            hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Predicted:</b> $%{y:,.2f}<extra></extra>",
        ))

    # Future Forecast
    if future_df is not None and not future_df.empty:
        # Shaded 95% Confidence Band
        fig.add_trace(go.Scatter(
            x=future_df["Date"].tolist() + future_df["Date"].tolist()[::-1],
            y=future_df["Upper_95"].tolist() + future_df["Lower_95"].tolist()[::-1],
            fill="toself",
            fillcolor="rgba(2, 132, 199, 0.12)",
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            showlegend=True,
            name="95% Confidence Band",
        ))

        # Future Mean
        fig.add_trace(go.Scatter(
            x=future_df["Date"],
            y=future_df["Forecast"],
            mode="lines+markers",
            name="Future Forecast",
            line=dict(color=COLOR_PRIMARY, width=2.5),
            marker=dict(size=5),
            hovertemplate="<b>Forecast Date:</b> %{x|%Y-%m-%d}<br><b>Forecast:</b> $%{y:,.2f}<extra></extra>",
        ))

    fig.update_yaxes(tickprefix="$")
    return apply_custom_layout(fig, title, height=450)


def plot_rfm_clusters_3d(labeled_rfm: pd.DataFrame, title: str = "3D Customer Segments (RFM Space)") -> go.Figure:
    """3D interactive scatter plot of customer clusters."""
    if labeled_rfm.empty or "Segment" not in labeled_rfm.columns:
        return apply_custom_layout(go.Figure(), title)

    fig = px.scatter_3d(
        labeled_rfm,
        x="Recency",
        y="Frequency",
        z="Monetary",
        color="Segment",
        color_discrete_sequence=SEGMENT_COLORS,
        opacity=0.8,
        hover_data={"CustomerID": True, "Recency": True, "Frequency": True, "Monetary": ":$.2f"},
    )
    fig.update_layout(
        scene=dict(
            xaxis_title="Recency (Days)",
            yaxis_title="Frequency (Orders)",
            zaxis_title="Monetary Spend ($)",
            bgcolor="rgba(248, 250, 252, 0.9)",
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        height=520,
    )
    return fig


def plot_rfm_clusters_2d(labeled_rfm: pd.DataFrame, title: str = "Customer Segmentation Map (Recency vs Monetary)") -> go.Figure:
    """2D scatter plot colored by customer segment with size proportional to frequency."""
    if labeled_rfm.empty or "Segment" not in labeled_rfm.columns:
        return apply_custom_layout(go.Figure(), title)

    # Cap bubble sizes safely
    sizes = np.clip(labeled_rfm["Frequency"].values * 3, 6, 30)

    fig = px.scatter(
        labeled_rfm,
        x="Recency",
        y="Monetary",
        color="Segment",
        size=sizes,
        color_discrete_sequence=SEGMENT_COLORS,
        hover_data={"CustomerID": True, "Recency": True, "Frequency": True, "Monetary": ":$.2f"},
        log_y=True,
    )
    fig.update_yaxes(tickprefix="$", title="Monetary Total ($ - Log Scale)")
    fig.update_xaxes(title="Recency (Days Ago)")
    return apply_custom_layout(fig, title, height=420)


def plot_anomalies(anomaly_df: pd.DataFrame, title: str = "Sales Timeline with Detected Anomalies") -> go.Figure:
    """Timeline plot showing baseline, actual revenue, and potential anomalies highlighted."""
    if anomaly_df.empty:
        return apply_custom_layout(go.Figure(), title)

    fig = go.Figure()

    # Normal line
    fig.add_trace(go.Scatter(
        x=anomaly_df["Date"],
        y=anomaly_df["Value"],
        mode="lines",
        name="Sales Revenue",
        line=dict(color="#0284c7", width=1.8),
        hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Sales:</b> $%{y:,.2f}<extra></extra>",
    ))

    # Baseline
    if "Baseline" in anomaly_df.columns:
        fig.add_trace(go.Scatter(
            x=anomaly_df["Date"],
            y=anomaly_df["Baseline"],
            mode="lines",
            name="Expected Baseline",
            line=dict(color="#94a3b8", width=1.5, dash="dash"),
            hovertemplate="<b>Baseline:</b> $%{y:,.2f}<extra></extra>",
        ))

    # Highlight Anomalies
    anomalies = anomaly_df[anomaly_df["IsAnomaly"]]
    if not anomalies.empty:
        fig.add_trace(go.Scatter(
            x=anomalies["Date"],
            y=anomalies["Value"],
            mode="markers",
            name="Potential Anomaly",
            marker=dict(color=COLOR_ROSE, size=10, symbol="diamond", line=dict(width=1.5, color="#ffffff")),
            hovertemplate="<b>ANOMALY DETECTED</b><br><b>Date:</b> %{x|%Y-%m-%d}<br><b>Observed:</b> $%{y:,.2f}<br><b>Type:</b> %{customdata}<extra></extra>",
            customdata=anomalies["Type"],
        ))

    fig.update_yaxes(tickprefix="$")
    return apply_custom_layout(fig, title, height=420)


def plot_association_rules(rules_df: pd.DataFrame, title: str = "Product Association Rules Matrix") -> go.Figure:
    """Scatter plot of Support vs Confidence with Lift as marker color."""
    if rules_df.empty or "Support" not in rules_df.columns:
        return apply_custom_layout(go.Figure(), title)

    fig = px.scatter(
        rules_df,
        x="Support",
        y="Confidence",
        color="Lift",
        size="TransactionCount" if "TransactionCount" in rules_df.columns else None,
        color_continuous_scale="Viridis",
        hover_data={"Antecedent": True, "Consequent": True, "Lift": ":.2f", "Support": ":.3f", "Confidence": ":.2%"},
    )
    fig.update_xaxes(tickformat=".1%", title="Support (Frequency of Co-occurrence)")
    fig.update_yaxes(tickformat=".1%", title="Confidence P(B | A)")
    return apply_custom_layout(fig, title, height=420)
