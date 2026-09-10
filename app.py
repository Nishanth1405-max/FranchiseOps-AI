"""FranchiseOps AI - Milestone 1 and 2 Outlet Intelligence Dashboard."""

from __future__ import annotations

import html
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analytics import (
    HEALTH_COLORS,
    HEALTH_ORDER,
    SCORE_WEIGHTS,
    calculate_performance_metrics,
    rerank_snapshot,
    score_component_frame,
)
from src.data_loader import DataValidationError, load_outlet_data
from src.milestone2_loader import Milestone2DataError, load_milestone2_outputs


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "raw" / "franchiseops_filtered_outlet_data.csv"
STAFF_AGENT_PATH = ROOT / "staff_agent" / "staff_agent_output.csv"
MARKETING_AGENT_PATH = ROOT / "data" / "processed" / "marketing_agent_output.csv"
INVENTORY_AGENT_PATH = ROOT / "data" / "processed" / "inventory_agent_output.csv"
FORECAST_PATH = ROOT / "data" / "processed" / "demand_forecast_output.csv"

st.set_page_config(
    page_title="FranchiseOps AI | Outlet Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


CSS = """
<style>
    :root {
        --panel: #0D1B2A;
        --text: #F3F7FC;
        --muted: #9FB0C5;
        --line: rgba(159,176,197,.18);
        --accent: #2DD4BF;
    }
    .stApp { background: radial-gradient(circle at 82% 2%, #12304A 0, #07111F 36%); }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background: #091522; border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] * { color: var(--text); }
    .block-container { max-width: 1500px; padding-top: 1.4rem; padding-bottom: 3rem; }
    h1, h2, h3 { color: var(--text) !important; letter-spacing: -.02em; }
    p, label, .stMarkdown { color: var(--text); }
    .hero {
        padding: 1.1rem 1.3rem; margin: .2rem 0 1.25rem;
        border: 1px solid var(--line); border-radius: 18px;
        background: linear-gradient(120deg, rgba(45,212,191,.12), rgba(96,165,250,.06));
    }
    .hero-kicker { color: var(--accent); font-weight: 750; font-size: .78rem; letter-spacing: .12em; text-transform: uppercase; }
    .hero-copy { color: var(--muted); margin: .35rem 0 0; max-width: 920px; line-height: 1.55; }
    .status-pill { display: inline-flex; padding: .28rem .62rem; border-radius: 999px; color: #A7F3D0; background: rgba(32,217,162,.12); border: 1px solid rgba(32,217,162,.3); font-size: .75rem; font-weight: 700; }
    .kpi-card {
        min-height: 124px; padding: 1rem 1.05rem; border: 1px solid var(--line); border-radius: 16px;
        background: linear-gradient(145deg, rgba(16,36,58,.98), rgba(10,24,39,.98));
        box-shadow: 0 12px 30px rgba(0,0,0,.12);
    }
    .kpi-label { color: var(--muted); font-size: .78rem; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; }
    .kpi-value { color: var(--text); font-size: 1.68rem; font-weight: 800; margin-top: .32rem; line-height: 1.15; }
    .kpi-delta { color: var(--muted); font-size: .78rem; margin-top: .48rem; }
    .kpi-delta.good { color: #6EE7B7; } .kpi-delta.warn { color: #FCD34D; } .kpi-delta.bad { color: #FDA4AF; }
    .section-note { color: var(--muted); margin-top: -.6rem; margin-bottom: .8rem; }
    .agent-card {
        padding: 1rem 1.05rem; margin-bottom: .75rem; border-radius: 14px;
        background: rgba(13,27,42,.92); border: 1px solid var(--line); border-left: 4px solid #60A5FA;
    }
    .agent-card.high { border-left-color: #FB7185; } .agent-card.medium { border-left-color: #FBBF24; } .agent-card.low { border-left-color: #20D9A2; }
    .agent-title { color: var(--text); font-size: 1rem; font-weight: 800; }
    .agent-meta { color: var(--muted); font-size: .78rem; margin: .18rem 0 .55rem; }
    .agent-copy { color: #D7E2EF; line-height: 1.48; font-size: .9rem; }
    .method-card { padding: .9rem 1rem; border-radius: 14px; background: rgba(13,27,42,.85); border: 1px solid var(--line); min-height: 126px; }
    .method-card b { color: var(--text); } .method-card span { color: var(--muted); font-size: .86rem; }
    div[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
    div[data-testid="stTabs"] button { color: var(--muted); font-weight: 700; }
    div[data-testid="stTabs"] button[aria-selected="true"] { color: var(--accent); }
    .stDownloadButton > button { width: 100%; border-color: rgba(45,212,191,.45); color: var(--text); }
    hr { border-color: var(--line) !important; }
    @media (max-width: 800px) { .block-container { padding: 1rem; } .kpi-card { min-height: 108px; } }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def get_data(path: str) -> tuple[pd.DataFrame, dict]:
    source, report = load_outlet_data(path)
    return calculate_performance_metrics(source), report.to_dict()


@st.cache_data(show_spinner=False)
def get_milestone2_data(
    staff_path: str,
    marketing_path: str,
    inventory_path: str,
    forecast_path: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    return load_milestone2_outputs(
        staff_path,
        marketing_path,
        inventory_path,
        forecast_path,
    )


def money(value: float) -> str:
    if abs(value) >= 10_000_000:
        return f"₹{value / 10_000_000:.2f} Cr"
    if abs(value) >= 100_000:
        return f"₹{value / 100_000:.1f} L"
    return f"₹{value:,.0f}"


def kpi_card(label: str, value: str, note: str, tone: str = "") -> None:
    st.markdown(
        f"""<div class="kpi-card"><div class="kpi-label">{html.escape(label)}</div>
        <div class="kpi-value">{html.escape(value)}</div>
        <div class="kpi-delta {tone}">{html.escape(note)}</div></div>""",
        unsafe_allow_html=True,
    )


def style_figure(fig: go.Figure, height: int = 370) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=16, r=16, t=55, b=18),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#D7E2EF", family="Arial, sans-serif", size=12),
        title_font=dict(color="#F3F7FC", size=16),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(bgcolor="#10243A", font_color="#F3F7FC"),
    )
    fig.update_xaxes(gridcolor="rgba(159,176,197,.10)", zerolinecolor="rgba(159,176,197,.15)")
    fig.update_yaxes(gridcolor="rgba(159,176,197,.10)", zerolinecolor="rgba(159,176,197,.15)")
    return fig


def show_agent_card(row: pd.Series) -> None:
    severity = str(row["alert_level"]).lower()
    st.markdown(
        f"""<div class="agent-card {severity}">
        <div class="agent-title">#{int(row['peer_rank'])} · {html.escape(str(row['outlet_name']))}</div>
        <div class="agent-meta">{html.escape(str(row['health_category']))} · Score {row['performance_score']:.1f} · {html.escape(str(row['alert_level']))} priority</div>
        <div class="agent-copy"><b>Finding:</b> {html.escape(str(row['insight']))}<br><b>Action:</b> {html.escape(str(row['recommendation']))}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def show_milestone2_agent_card(
    title: str,
    meta: str,
    insight: str,
    recommendation: str,
    severity: str,
) -> None:
    tone = {
        "critical": "high",
        "high": "high",
        "needs attention": "medium",
        "medium": "medium",
        "stable": "low",
        "low": "low",
    }.get(severity.lower(), "medium")
    st.markdown(
        f"""<div class="agent-card {tone}">
        <div class="agent-title">{html.escape(title)}</div>
        <div class="agent-meta">{html.escape(meta)}</div>
        <div class="agent-copy"><b>Finding:</b> {html.escape(insight)}<br><b>Action:</b> {html.escape(recommendation)}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def inventory_recommendation(row: pd.Series) -> str:
    action = str(row["Agent_Action"])
    replenishment = int(row["Recommended_Replenishment_Units"])
    if action == "URGENT_REORDER":
        return f"Place an urgent replenishment order for {replenishment:,} units."
    if action == "REORDER":
        return f"Plan replenishment for {replenishment:,} units before stock falls further."
    if action == "REDUCE_STOCK":
        return "Delay new purchases and rebalance excess stock to reduce holding cost."
    if action == "MONITOR_WASTAGE":
        return "Review stock rotation, expiry handling, and order quantities to reduce wastage."
    return "Continue routine stock monitoring; no immediate replenishment action is required."


try:
    data, quality = get_data(str(DATA_PATH))
except (FileNotFoundError, DataValidationError) as exc:
    st.error(f"The dashboard could not load a valid dataset: {exc}")
    st.stop()

milestone2_error = None
try:
    staff_data, marketing_data, inventory_data, forecast_data, milestone2_quality = get_milestone2_data(
        str(STAFF_AGENT_PATH),
        str(MARKETING_AGENT_PATH),
        str(INVENTORY_AGENT_PATH),
        str(FORECAST_PATH),
    )
except (FileNotFoundError, Milestone2DataError) as exc:
    milestone2_error = str(exc)
    staff_data = pd.DataFrame()
    marketing_data = pd.DataFrame()
    inventory_data = pd.DataFrame()
    forecast_data = pd.DataFrame()
    milestone2_quality = {
        "staff_outlets": 0,
        "marketing_outlets": 0,
        "inventory_outlets": 0,
        "forecast_outlets": 0,
        "inventory_records": 0,
        "forecast_records": 0,
        "forecast_skus": 0,
        "available_forecasts": 0,
        "shared_outlets": 0,
    }


st.sidebar.markdown("## FranchiseOps AI")
st.sidebar.caption("Milestones 1 & 2 · Outlet Intelligence")
st.sidebar.markdown("---")
st.sidebar.markdown("### Analysis filters")

min_date = data["date"].min().date()
max_date = data["date"].max().date()
date_selection = st.sidebar.date_input(
    "Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
)
if isinstance(date_selection, tuple) and len(date_selection) == 2:
    start_date, end_date = date_selection
else:
    start_date = end_date = date_selection

all_regions = sorted(data["region"].unique().tolist())
selected_regions = st.sidebar.multiselect("Regions", all_regions, default=all_regions)
region_data = data[data["region"].isin(selected_regions)] if selected_regions else data.iloc[0:0]
outlet_options = (
    region_data[["outlet_id", "outlet_name"]]
    .drop_duplicates()
    .sort_values("outlet_name")
    .set_index("outlet_id")["outlet_name"]
    .to_dict()
)
selected_outlets = st.sidebar.multiselect(
    "Outlets", options=list(outlet_options), default=list(outlet_options), format_func=lambda value: outlet_options[value]
)

filtered = data[
    (data["date"].dt.date >= start_date)
    & (data["date"].dt.date <= end_date)
    & (data["region"].isin(selected_regions))
    & (data["outlet_id"].isin(selected_outlets))
].copy()

if filtered.empty:
    st.title("Outlet Performance Intelligence")
    st.warning("No records match the current filters. Select at least one region and outlet.")
    st.stop()

available_months = sorted(filtered["date"].unique(), reverse=True)
snapshot_month = st.sidebar.selectbox(
    "Benchmark month", available_months, format_func=lambda value: pd.Timestamp(value).strftime("%B %Y")
)
snapshot = rerank_snapshot(filtered[filtered["date"] == snapshot_month])

st.sidebar.markdown("---")
st.sidebar.markdown(f"<span class='status-pill'>● Data quality {quality['status']}</span>", unsafe_allow_html=True)
st.sidebar.caption(f"{quality['rows']} validated records · {quality['outlets']} outlets · {quality['months']} months")
st.sidebar.caption(
    f"Milestone 2 · {milestone2_quality['shared_outlets']} shared outlets · All four modules active"
)

month_label = pd.Timestamp(snapshot_month).strftime("%B %Y")
st.title("Outlet Performance Intelligence")
st.markdown(
    f"""<div class="hero"><div class="hero-kicker">FranchiseOps AI · Milestones 1 & 2</div>
    <p class="hero-copy">Monitor revenue, compare franchise locations, measure outlet health, and convert performance, staff, marketing, inventory, and demand signals into prioritized actions. Current peer snapshot: <b>{month_label}</b>.</p></div>""",
    unsafe_allow_html=True,
)

overview_tab, benchmark_tab, outlet_tab, agent_tab, method_tab = st.tabs(
    ["Overview", "Benchmarking", "Outlet Analysis", "Agent Insights", "Methodology & Quality"]
)


with overview_tab:
    total_revenue = float(snapshot["revenue"].sum())
    total_target = float(snapshot["target_revenue"].sum())
    attainment = total_revenue / total_target * 100 if total_target else 0
    average_score = float(snapshot["performance_score"].mean())
    healthy_count = int(snapshot["health_category"].isin(["Excellent", "Good"]).sum())
    priority_count = int(snapshot["alert_level"].isin(["High", "Medium"]).sum())

    earlier = filtered[filtered["date"] < snapshot_month]
    previous_month = earlier["date"].max() if not earlier.empty else None
    previous_revenue = float(earlier[earlier["date"] == previous_month]["revenue"].sum()) if previous_month is not None else 0
    revenue_delta = (total_revenue / previous_revenue - 1) * 100 if previous_revenue else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        kpi_card("Monthly revenue", money(total_revenue), f"{revenue_delta:+.1f}% vs prior month", "good" if revenue_delta >= 0 else "bad")
    with k2:
        kpi_card("Target achievement", f"{attainment:.1f}%", f"Gap {money(total_revenue - total_target)}", "good" if attainment >= 100 else "warn")
    with k3:
        kpi_card("Average health score", f"{average_score:.1f}/100", "Weighted across 5 drivers", "good" if average_score >= 70 else "warn")
    with k4:
        kpi_card("Healthy outlets", f"{healthy_count}/{len(snapshot)}", "Excellent or Good", "good")
    with k5:
        kpi_card("Priority alerts", str(priority_count), "High + Medium severity", "bad" if priority_count else "good")

    st.markdown("### Network performance")
    st.markdown("<p class='section-note'>Revenue trajectory and the latest outlet health mix for the selected peer group.</p>", unsafe_allow_html=True)
    left, right = st.columns([1.7, 1])
    monthly = filtered.groupby("date", as_index=False).agg(revenue=("revenue", "sum"), target=("target_revenue", "sum"))
    trend = go.Figure()
    trend.add_trace(go.Scatter(x=monthly["date"], y=monthly["revenue"], name="Revenue", mode="lines+markers", line=dict(color="#2DD4BF", width=3)))
    trend.add_trace(go.Scatter(x=monthly["date"], y=monthly["target"], name="Target", mode="lines+markers", line=dict(color="#94A3B8", width=2, dash="dash")))
    trend.update_layout(title="Revenue vs target", yaxis_title="Revenue (₹)", hovermode="x unified")
    trend.update_yaxes(tickformat="~s")
    with left:
        st.plotly_chart(style_figure(trend), width="stretch", config={"displayModeBar": False, "responsive": True})

    health_counts = snapshot["health_category"].value_counts().reindex(HEALTH_ORDER, fill_value=0)
    donut = go.Figure(go.Pie(labels=health_counts.index, values=health_counts.values, hole=.64, marker_colors=[HEALTH_COLORS[x] for x in health_counts.index], textinfo="label+value", sort=False))
    donut.update_layout(title="Outlet health mix", showlegend=False, annotations=[dict(text=f"{len(snapshot)}<br>outlets", x=.5, y=.5, showarrow=False, font_size=17)])
    with right:
        st.plotly_chart(style_figure(donut), width="stretch", config={"displayModeBar": False, "responsive": True})

    matrix = px.scatter(
        snapshot, x="target_achievement_pct", y="performance_score", size="revenue", color="health_category",
        color_discrete_map=HEALTH_COLORS, hover_name="outlet_name",
        hover_data={"revenue": ":,.0f", "target_achievement_pct": ":.1f", "performance_score": ":.1f", "health_category": False},
        labels={"target_achievement_pct": "Target achievement (%)", "performance_score": "Performance score", "health_category": "Health"},
        title="Performance matrix",
    )
    matrix.add_vline(x=100, line_dash="dash", line_color="#64748B")
    matrix.add_hline(y=70, line_dash="dash", line_color="#64748B")
    st.plotly_chart(style_figure(matrix, 420), width="stretch", config={"displayModeBar": False, "responsive": True})


with benchmark_tab:
    st.markdown("### Outlet benchmarking")
    st.markdown(f"<p class='section-note'>Unique peer ranking for {month_label}. Filters dynamically define the comparison group.</p>", unsafe_allow_html=True)
    benchmark_chart = px.bar(
        snapshot.sort_values("performance_score"), x="performance_score", y="outlet_name", orientation="h",
        color="health_category", color_discrete_map=HEALTH_COLORS, text="performance_score",
        hover_data={"target_achievement_pct": ":.1f", "benchmark_gap_pct": ":+.1f", "peer_rank": True},
        labels={"performance_score": "Performance score", "outlet_name": "Outlet", "health_category": "Health"},
        title="Peer performance ranking",
    )
    benchmark_chart.update_traces(texttemplate="%{text:.1f}", textposition="outside", cliponaxis=False)
    benchmark_chart.update_xaxes(range=[0, 105])
    st.plotly_chart(style_figure(benchmark_chart, max(390, 38 * len(snapshot))), width="stretch", config={"displayModeBar": False, "responsive": True})

    display = snapshot[["peer_rank", "outlet_name", "city", "region", "revenue", "target_achievement_pct", "benchmark_gap_pct", "performance_score", "health_category", "alert_level"]].rename(
        columns={"peer_rank": "Rank", "outlet_name": "Outlet", "city": "City", "region": "Region", "revenue": "Revenue", "target_achievement_pct": "Target %", "benchmark_gap_pct": "Peer gap %", "performance_score": "Score", "health_category": "Health", "alert_level": "Alert"}
    )
    st.dataframe(
        display, hide_index=True, width="stretch",
        column_config={
            "Revenue": st.column_config.NumberColumn(format="₹ %.0f"),
            "Target %": st.column_config.NumberColumn(format="%.1f%%"),
            "Peer gap %": st.column_config.NumberColumn(format="%+.1f%%"),
            "Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
        },
    )
    st.download_button(
        "Download benchmark report (CSV)", display.to_csv(index=False).encode("utf-8"),
        file_name=f"outlet_benchmark_{pd.Timestamp(snapshot_month):%Y_%m}.csv", mime="text/csv",
    )


with outlet_tab:
    st.markdown("### Outlet drill-down")
    outlet_lookup = snapshot.set_index("outlet_id")["outlet_name"].to_dict()
    selected_detail_id = st.selectbox("Select outlet", list(outlet_lookup), format_func=lambda value: outlet_lookup[value])
    selected_history = filtered[filtered["outlet_id"] == selected_detail_id].sort_values("date")
    detail = selected_history[selected_history["date"] == snapshot_month]
    if detail.empty:
        detail = selected_history.tail(1)
    row = detail.iloc[0]

    d1, d2, d3, d4 = st.columns(4)
    with d1:
        kpi_card("Performance score", f"{row['performance_score']:.1f}", str(row["health_category"]), "good" if row["performance_score"] >= 70 else "warn")
    with d2:
        kpi_card("Monthly revenue", money(float(row["revenue"])), f"{row['target_achievement_pct']:.1f}% of target", "good" if row["target_achievement_pct"] >= 100 else "warn")
    with d3:
        kpi_card("Customer rating", f"{row['customer_rating']:.2f}/5", f"Complaint rate {row['complaint_rate']:.2f}%")
    with d4:
        kpi_card("Service reliability", f"{row['on_time_service_pct']:.1f}%", f"Alert: {row['alert_level']}", "bad" if row["alert_level"] == "High" else "")

    c1, c2 = st.columns([1.55, 1])
    history_chart = go.Figure()
    history_chart.add_trace(go.Bar(x=selected_history["date"], y=selected_history["revenue"], name="Revenue", marker_color="#2DD4BF"))
    history_chart.add_trace(go.Scatter(x=selected_history["date"], y=selected_history["target_revenue"], name="Target", mode="lines+markers", line=dict(color="#FBBF24", width=2)))
    history_chart.update_layout(title="Revenue history", yaxis_title="Revenue (₹)", hovermode="x unified")
    history_chart.update_yaxes(tickformat="~s")
    with c1:
        st.plotly_chart(style_figure(history_chart), width="stretch", config={"displayModeBar": False, "responsive": True})

    components = score_component_frame(row)
    component_chart = px.bar(
        components.sort_values("score"), x="score", y="component", orientation="h", text="score", color="score",
        color_continuous_scale=[[0, "#FB7185"], [.55, "#FBBF24"], [1, "#20D9A2"]], range_color=[0, 100], title="Score drivers",
    )
    component_chart.update_traces(texttemplate="%{text:.1f}", textposition="outside", cliponaxis=False)
    component_chart.update_xaxes(range=[0, 108])
    component_chart.update_layout(coloraxis_showscale=False)
    with c2:
        st.plotly_chart(style_figure(component_chart), width="stretch", config={"displayModeBar": False, "responsive": True})

    st.markdown("#### Agent assessment")
    detail_for_card = row.copy()
    detail_for_card["peer_rank"] = int(snapshot.loc[snapshot["outlet_id"] == selected_detail_id, "peer_rank"].iloc[0])
    show_agent_card(detail_for_card)

    score_history = px.line(selected_history, x="date", y="performance_score", markers=True, title="Performance score trend", labels={"date": "Month", "performance_score": "Score"})
    score_history.update_traces(line_color="#60A5FA", line_width=3)
    score_history.add_hline(y=70, line_dash="dash", line_color="#64748B", annotation_text="Good threshold")
    score_history.update_yaxes(range=[0, 100])
    st.plotly_chart(style_figure(score_history, 330), width="stretch", config={"displayModeBar": False, "responsive": True})


with agent_tab:
    st.markdown("### Multi-agent decision centre")
    st.markdown(
        "<p class='section-note'>Milestone 1 outlet intelligence and Milestone 2 staff, marketing, inventory, and demand analysis in one consistent dashboard. All recommendations are deterministic and explainable.</p>",
        unsafe_allow_html=True,
    )
    outlet_agent_tab, staff_agent_tab, marketing_agent_tab, inventory_agent_tab = st.tabs(
        ["Outlet Performance", "Staff Agent", "Marketing Agent", "Inventory & Forecasting"]
    )

    with outlet_agent_tab:
        st.markdown("#### Outlet Performance Agent")
        priority_order = pd.Categorical(snapshot["alert_level"], categories=["High", "Medium", "Low"], ordered=True)
        agent_rows = snapshot.assign(_priority=priority_order).sort_values(["_priority", "performance_score"])
        high_count = int((agent_rows["alert_level"] == "High").sum())
        medium_count = int((agent_rows["alert_level"] == "Medium").sum())
        low_count = int((agent_rows["alert_level"] == "Low").sum())
        a1, a2, a3 = st.columns(3)
        with a1:
            kpi_card("Immediate action", str(high_count), "High-severity outlet alerts", "bad" if high_count else "good")
        with a2:
            kpi_card("Watch list", str(medium_count), "Medium-severity outlet alerts", "warn" if medium_count else "good")
        with a3:
            kpi_card("Stable", str(low_count), "Low-severity outlets", "good")

        st.markdown("#### Prioritized action queue")
        for _, agent_row in agent_rows.iterrows():
            show_agent_card(agent_row)

        export_columns = ["peer_rank", "outlet_id", "outlet_name", "performance_score", "health_category", "alert_level", "issue_tags", "insight", "recommendation"]
        st.download_button(
            "Download agent insights (CSV)", agent_rows[export_columns].to_csv(index=False).encode("utf-8"),
            file_name=f"outlet_agent_insights_{pd.Timestamp(snapshot_month):%Y_%m}.csv", mime="text/csv",
        )

    with staff_agent_tab:
        st.markdown("#### Staff Agent")
        st.markdown(
            "<p class='section-note'>People and service health based on employee levels, turnover, customer satisfaction, and complaints.</p>",
            unsafe_allow_html=True,
        )
        if milestone2_error:
            st.error(f"Staff Agent data is unavailable: {milestone2_error}")
        else:
            staff_ids = staff_data["Outlet_ID"].tolist()
            staff_names = staff_data.set_index("Outlet_ID")["Outlet_Name"].to_dict()
            default_staff = staff_ids.index("OUT0706") if "OUT0706" in staff_ids else 0
            staff_outlet_id = st.selectbox(
                "Select Milestone 2 outlet",
                staff_ids,
                index=default_staff,
                format_func=lambda value: f"{value} · {staff_names[value]}",
                key="staff_agent_outlet",
            )
            staff_row = staff_data.set_index("Outlet_ID").loc[staff_outlet_id]
            staff_tone = "bad" if staff_row["Staff_Status"] == "Critical" else "warn" if staff_row["Staff_Status"] == "Needs Attention" else "good"

            s1, s2, s3, s4, s5 = st.columns(5)
            with s1:
                kpi_card("Staff status", str(staff_row["Staff_Status"]), "Quartile-based risk rules", staff_tone)
            with s2:
                kpi_card("Average employees", f"{staff_row['Avg_Employees']:.1f}", "Outlet staffing level")
            with s3:
                kpi_card("Employee turnover", f"{staff_row['Avg_Employee_Turnover']:.2f}%", "Lower is better", staff_tone)
            with s4:
                kpi_card("Customer satisfaction", f"{staff_row['Avg_Customer_Satisfaction']:.2f}/5", "Service outcome", staff_tone)
            with s5:
                kpi_card("Complaints", f"{int(staff_row['Total_Complaints']):,}", "Total records analyzed", staff_tone)

            show_milestone2_agent_card(
                f"{staff_outlet_id} · {staff_row['Outlet_Name']}",
                f"Staff status: {staff_row['Staff_Status']}",
                str(staff_row["Insight"]),
                str(staff_row["Recommendation"]),
                str(staff_row["Staff_Status"]),
            )

            staff_left, staff_right = st.columns([1.65, 1])
            staff_scatter = px.scatter(
                staff_data,
                x="Avg_Employee_Turnover",
                y="Avg_Customer_Satisfaction",
                size="Total_Complaints",
                color="Staff_Status",
                color_discrete_map={"Critical": "#FB7185", "Needs Attention": "#FBBF24", "Stable": "#20D9A2"},
                hover_name="Outlet_Name",
                hover_data={"Outlet_ID": True, "Avg_Employees": ":.1f", "Total_Complaints": ":,.0f"},
                labels={"Avg_Employee_Turnover": "Employee turnover (%)", "Avg_Customer_Satisfaction": "Customer satisfaction (1-5)", "Staff_Status": "Status"},
                title="Staff risk matrix",
            )
            with staff_left:
                st.plotly_chart(style_figure(staff_scatter), width="stretch", config={"displayModeBar": False, "responsive": True})

            staff_counts = staff_data["Staff_Status"].value_counts().reindex(["Critical", "Needs Attention", "Stable"], fill_value=0)
            staff_donut = go.Figure(go.Pie(
                labels=staff_counts.index,
                values=staff_counts.values,
                hole=.64,
                marker_colors=["#FB7185", "#FBBF24", "#20D9A2"],
                textinfo="label+value",
                sort=False,
            ))
            staff_donut.update_layout(
                title="Staff status mix",
                showlegend=False,
                annotations=[dict(text=f"{len(staff_data)}<br>outlets", x=.5, y=.5, showarrow=False, font_size=17)],
            )
            with staff_right:
                st.plotly_chart(style_figure(staff_donut), width="stretch", config={"displayModeBar": False, "responsive": True})

            staff_queue = staff_data.assign(
                _priority=staff_data["Staff_Status"].map({"Critical": 0, "Needs Attention": 1, "Stable": 2})
            ).sort_values(["_priority", "Avg_Employee_Turnover", "Total_Complaints"], ascending=[True, False, False])
            st.markdown("#### Highest-priority staff outlets")
            st.dataframe(
                staff_queue[["Outlet_ID", "Outlet_Name", "Avg_Employee_Turnover", "Avg_Customer_Satisfaction", "Total_Complaints", "Staff_Status"]].head(20),
                hide_index=True,
                width="stretch",
                column_config={
                    "Avg_Employee_Turnover": st.column_config.NumberColumn("Turnover", format="%.2f%%"),
                    "Avg_Customer_Satisfaction": st.column_config.NumberColumn("Satisfaction", format="%.2f"),
                    "Total_Complaints": st.column_config.NumberColumn("Complaints", format="%d"),
                },
            )
            st.download_button(
                "Download Staff Agent output (CSV)",
                staff_data.to_csv(index=False).encode("utf-8"),
                file_name="staff_agent_output.csv",
                mime="text/csv",
            )

    with marketing_agent_tab:
        st.markdown("#### Marketing Agent")
        st.markdown(
            "<p class='section-note'>Campaign efficiency and conversion analysis using spend, sales revenue, orders, and revenue generated per marketing rupee.</p>",
            unsafe_allow_html=True,
        )
        if milestone2_error:
            st.error(f"Marketing Agent data is unavailable: {milestone2_error}")
        else:
            marketing_ids = marketing_data["Outlet_ID"].tolist()
            default_marketing = marketing_ids.index("OUT0706") if "OUT0706" in marketing_ids else 0
            marketing_outlet_id = st.selectbox(
                "Select Milestone 2 outlet",
                marketing_ids,
                index=default_marketing,
                key="marketing_agent_outlet",
            )
            marketing_row = marketing_data.set_index("Outlet_ID").loc[marketing_outlet_id]
            marketing_tone = "bad" if marketing_row["Alert_Level"] == "High" else "warn" if marketing_row["Alert_Level"] == "Medium" else "good"

            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                kpi_card("Marketing category", str(marketing_row["Marketing_Category"]), f"{marketing_row['Alert_Level']} alert", marketing_tone)
            with m2:
                kpi_card("Marketing spend", money(float(marketing_row["Total_Marketing_Spend"])), "Total analyzed spend")
            with m3:
                kpi_card("Sales revenue", money(float(marketing_row["Total_Sales_Revenue"])), "Attributed outlet revenue", "good")
            with m4:
                kpi_card("Revenue per ₹1", f"₹{marketing_row['Revenue_Per_Marketing_Rupee']:.2f}", "Marketing efficiency", marketing_tone)
            with m5:
                kpi_card("Conversion rate", f"{marketing_row['Average_Conversion_Rate']:.2f}%", f"Spend ratio {marketing_row['Marketing_Spend_Percentage']:.2f}%", marketing_tone)

            show_milestone2_agent_card(
                f"{marketing_outlet_id} · Marketing performance",
                f"{marketing_row['Marketing_Category']} · {marketing_row['Alert_Level']} alert · {int(marketing_row['Records'])} records",
                str(marketing_row["Marketing_Insights"]),
                str(marketing_row["Recommendations"]),
                str(marketing_row["Alert_Level"]),
            )

            marketing_left, marketing_right = st.columns([1.65, 1])
            marketing_scatter = px.scatter(
                marketing_data,
                x="Revenue_Per_Marketing_Rupee",
                y="Average_Conversion_Rate",
                size="Total_Marketing_Spend",
                color="Marketing_Category",
                color_discrete_map={"Needs Improvement": "#FB7185", "Moderate": "#FBBF24", "High Performing": "#20D9A2"},
                hover_name="Outlet_ID",
                hover_data={"Total_Sales_Revenue": ":,.0f", "Marketing_Spend_Percentage": ":.2f"},
                labels={"Revenue_Per_Marketing_Rupee": "Revenue per marketing rupee", "Average_Conversion_Rate": "Conversion rate (%)", "Marketing_Category": "Category"},
                title="Marketing efficiency matrix",
            )
            with marketing_left:
                st.plotly_chart(style_figure(marketing_scatter), width="stretch", config={"displayModeBar": False, "responsive": True})

            marketing_counts = marketing_data["Marketing_Category"].value_counts().reindex(["Needs Improvement", "Moderate", "High Performing"], fill_value=0)
            marketing_donut = go.Figure(go.Pie(
                labels=marketing_counts.index,
                values=marketing_counts.values,
                hole=.64,
                marker_colors=["#FB7185", "#FBBF24", "#20D9A2"],
                textinfo="label+value",
                sort=False,
            ))
            marketing_donut.update_layout(
                title="Marketing category mix",
                showlegend=False,
                annotations=[dict(text=f"{len(marketing_data)}<br>outlets", x=.5, y=.5, showarrow=False, font_size=17)],
            )
            with marketing_right:
                st.plotly_chart(style_figure(marketing_donut), width="stretch", config={"displayModeBar": False, "responsive": True})

            marketing_queue = marketing_data.assign(
                _priority=marketing_data["Alert_Level"].map({"High": 0, "Medium": 1, "Low": 2})
            ).sort_values(["_priority", "Revenue_Per_Marketing_Rupee", "Average_Conversion_Rate"])
            st.markdown("#### Highest-priority marketing outlets")
            st.dataframe(
                marketing_queue[["Outlet_ID", "Revenue_Per_Marketing_Rupee", "Average_Conversion_Rate", "Marketing_Spend_Percentage", "Marketing_Category", "Alert_Level"]].head(20),
                hide_index=True,
                width="stretch",
                column_config={
                    "Revenue_Per_Marketing_Rupee": st.column_config.NumberColumn("Revenue / ₹1", format="₹ %.2f"),
                    "Average_Conversion_Rate": st.column_config.NumberColumn("Conversion", format="%.2f%%"),
                    "Marketing_Spend_Percentage": st.column_config.NumberColumn("Spend ratio", format="%.2f%%"),
                },
            )
            st.download_button(
                "Download Marketing Agent output (CSV)",
                marketing_data.to_csv(index=False).encode("utf-8"),
                file_name="marketing_agent_output.csv",
                mime="text/csv",
            )

    with inventory_agent_tab:
        st.markdown("#### Inventory Agent and Forecasting")
        st.markdown(
            "<p class='section-note'>Current stock health, replenishment decisions, wastage monitoring, and a three-month moving-average demand forecast.</p>",
            unsafe_allow_html=True,
        )
        if milestone2_error:
            st.error(f"Inventory and forecasting data is unavailable: {milestone2_error}")
        else:
            inventory_names = (
                inventory_data[["Outlet_ID", "Outlet_Name"]]
                .drop_duplicates("Outlet_ID")
                .set_index("Outlet_ID")["Outlet_Name"]
                .to_dict()
            )
            inventory_ids = sorted(inventory_names)
            default_inventory = inventory_ids.index("OUT0706") if "OUT0706" in inventory_ids else 0
            inventory_outlet_id = st.selectbox(
                "Select Milestone 2 outlet",
                inventory_ids,
                index=default_inventory,
                format_func=lambda value: f"{value} · {inventory_names[value]}",
                key="inventory_agent_outlet",
            )

            inventory_history = inventory_data[
                inventory_data["Outlet_ID"] == inventory_outlet_id
            ].sort_values("Month")
            inventory_row = inventory_history.iloc[-1]
            selected_sku = str(inventory_row["SKU_ID"])
            forecast_history = forecast_data[
                (forecast_data["Outlet_ID"] == inventory_outlet_id)
                & (forecast_data["SKU_ID"] == selected_sku)
            ].sort_values("Month")
            latest_forecast = forecast_history[
                "Demand_Forecast_Next_Month_Units"
            ].dropna().iloc[-1]
            inventory_tone = (
                "bad"
                if inventory_row["Agent_Priority"] == "High"
                else "warn"
                if inventory_row["Agent_Priority"] == "Medium"
                else "good"
            )
            inventory_month = pd.Timestamp(inventory_row["Month"]).strftime("%B %Y")

            v1, v2, v3, v4, v5 = st.columns(5)
            with v1:
                kpi_card(
                    "Stock status",
                    str(inventory_row["Stock_Status"]),
                    f"{inventory_row['Agent_Priority']} priority",
                    inventory_tone,
                )
            with v2:
                kpi_card(
                    "Closing stock",
                    f"{int(inventory_row['Closing_Stock_Units']):,}",
                    f"Safety stock {int(inventory_row['Safety_Stock_Units']):,}",
                )
            with v3:
                kpi_card(
                    "Reorder point",
                    f"{int(inventory_row['Reorder_Point_Units']):,}",
                    f"Availability {inventory_row['Stock_Availability_%']:.1f}%",
                    inventory_tone,
                )
            with v4:
                kpi_card(
                    "3-month forecast",
                    f"{latest_forecast:,.0f}",
                    "Prior-three-month demand estimate",
                )
            with v5:
                kpi_card(
                    "Replenishment",
                    f"{int(inventory_row['Recommended_Replenishment_Units']):,}",
                    f"Action: {str(inventory_row['Agent_Action']).replace('_', ' ').title()}",
                    inventory_tone,
                )

            show_milestone2_agent_card(
                f"{inventory_outlet_id} · {selected_sku}",
                (
                    f"{inventory_month} · {inventory_row['Product_Category']} · "
                    f"Freshness {inventory_row['Freshness_Rate_%']:.1f}% · "
                    f"Wastage {int(inventory_row['Wastage_Units']):,} units"
                ),
                str(inventory_row["Agent_Explanation"]),
                inventory_recommendation(inventory_row),
                str(inventory_row["Agent_Priority"]),
            )

            latest_inventory = (
                inventory_data.sort_values(["Outlet_ID", "SKU_ID", "Month"])
                .groupby(["Outlet_ID", "SKU_ID"], as_index=False, group_keys=False)
                .tail(1)
            )
            inventory_left, inventory_right = st.columns([1.65, 1])
            stock_trend = go.Figure()
            stock_trend.add_trace(
                go.Scatter(
                    x=inventory_history["Month"],
                    y=inventory_history["Closing_Stock_Units"],
                    name="Closing stock",
                    mode="lines+markers",
                    line=dict(color="#2DD4BF", width=3),
                )
            )
            stock_trend.add_trace(
                go.Scatter(
                    x=inventory_history["Month"],
                    y=inventory_history["Reorder_Point_Units"],
                    name="Reorder point",
                    mode="lines",
                    line=dict(color="#FBBF24", width=2, dash="dash"),
                )
            )
            stock_trend.add_trace(
                go.Scatter(
                    x=inventory_history["Month"],
                    y=inventory_history["Safety_Stock_Units"],
                    name="Safety stock",
                    mode="lines",
                    line=dict(color="#60A5FA", width=2, dash="dot"),
                )
            )
            stock_trend.update_layout(
                title="Stock level vs inventory thresholds",
                yaxis_title="Units",
                hovermode="x unified",
            )
            with inventory_left:
                st.plotly_chart(
                    style_figure(stock_trend),
                    width="stretch",
                    config={"displayModeBar": False, "responsive": True},
                )

            action_order = [
                "URGENT_REORDER",
                "REORDER",
                "MONITOR_WASTAGE",
                "REDUCE_STOCK",
                "NO_ACTION",
            ]
            action_counts = latest_inventory["Agent_Action"].value_counts().reindex(
                action_order, fill_value=0
            )
            action_donut = go.Figure(
                go.Pie(
                    labels=[label.replace("_", " ").title() for label in action_counts.index],
                    values=action_counts.values,
                    hole=.64,
                    marker_colors=["#FB7185", "#FBBF24", "#A78BFA", "#60A5FA", "#20D9A2"],
                    textinfo="label+value",
                    sort=False,
                )
            )
            action_donut.update_layout(
                title="Latest inventory action mix",
                showlegend=False,
                annotations=[dict(text=f"{len(latest_inventory)}<br>SKUs", x=.5, y=.5, showarrow=False, font_size=17)],
            )
            with inventory_right:
                st.plotly_chart(
                    style_figure(action_donut),
                    width="stretch",
                    config={"displayModeBar": False, "responsive": True},
                )

            demand_chart = go.Figure()
            demand_chart.add_trace(
                go.Scatter(
                    x=forecast_history["Month"],
                    y=forecast_history["Inventory_Units_Sold"],
                    name="Actual units sold",
                    mode="lines+markers",
                    line=dict(color="#2DD4BF", width=3),
                )
            )
            demand_chart.add_trace(
                go.Scatter(
                    x=forecast_history["Month"],
                    y=forecast_history["Demand_Forecast_Next_Month_Units"],
                    name="3-month forecast",
                    mode="lines+markers",
                    line=dict(color="#FBBF24", width=2, dash="dash"),
                )
            )
            demand_chart.update_layout(
                title="Demand history and moving-average forecast",
                yaxis_title="Units",
                hovermode="x unified",
            )
            st.plotly_chart(
                style_figure(demand_chart, 400),
                width="stretch",
                config={"displayModeBar": False, "responsive": True},
            )

            inventory_queue = latest_inventory.assign(
                _priority=latest_inventory["Agent_Priority"].map(
                    {"High": 0, "Medium": 1, "Low": 2}
                )
            ).sort_values(
                ["_priority", "Stock_Availability_%", "Recommended_Replenishment_Units"],
                ascending=[True, True, False],
            )
            st.markdown("#### Latest prioritized inventory queue")
            st.dataframe(
                inventory_queue[
                    [
                        "Outlet_ID",
                        "SKU_ID",
                        "Stock_Status",
                        "Closing_Stock_Units",
                        "Stock_Availability_%",
                        "Recommended_Replenishment_Units",
                        "Agent_Action",
                        "Agent_Priority",
                    ]
                ].head(25),
                hide_index=True,
                width="stretch",
                column_config={
                    "Closing_Stock_Units": st.column_config.NumberColumn("Closing stock", format="%d"),
                    "Stock_Availability_%": st.column_config.NumberColumn("Availability", format="%.1f%%"),
                    "Recommended_Replenishment_Units": st.column_config.NumberColumn("Replenish", format="%d"),
                },
            )
            inventory_download, forecast_download = st.columns(2)
            with inventory_download:
                st.download_button(
                    "Download Inventory Agent output (CSV)",
                    inventory_data.to_csv(index=False, date_format="%Y-%m").encode("utf-8"),
                    file_name="inventory_agent_output.csv",
                    mime="text/csv",
                )
            with forecast_download:
                st.download_button(
                    "Download Demand Forecast output (CSV)",
                    forecast_data.to_csv(index=False, date_format="%Y-%m-%d").encode("utf-8"),
                    file_name="demand_forecast_output.csv",
                    mime="text/csv",
                )


with method_tab:
    st.markdown("### Scoring methodology")
    st.markdown("<p class='section-note'>All scores and rankings are recalculated from source operating measures; uploaded derived columns are not trusted blindly.</p>", unsafe_allow_html=True)
    method_cols = st.columns(5)
    descriptions = {
        "Revenue target achievement": "Revenue divided by target, capped at 100.",
        "Month-over-month growth": "-20%→0, 0%→50, +20%→100.",
        "Customer rating": "Five-point rating converted to 100.",
        "Complaint control": "Lower complaints produce a higher score.",
        "On-time service": "Existing service percentage, bounded 0-100.",
    }
    for column, (name, weight) in zip(method_cols, SCORE_WEIGHTS.items()):
        with column:
            st.markdown(f"<div class='method-card'><b>{html.escape(name)}</b><br><span>{weight:.0%} weight<br>{html.escape(descriptions[name])}</span></div>", unsafe_allow_html=True)

    st.markdown("#### Health and alert rules")
    h1, h2 = st.columns(2)
    with h1:
        st.dataframe(
            pd.DataFrame({"Health category": HEALTH_ORDER, "Score range": ["85-100", "70-84.9", "55-69.9", "Below 55"]}),
            hide_index=True, width="stretch",
        )
    with h2:
        st.markdown(
            """
            - **High:** critical score, severe revenue decline, complaint rate ≥7%, or on-time service <70%.
            - **Medium:** score below 70, target achievement below 90%, complaint rate ≥5%, or service below 80%.
            - **Low:** no high- or medium-severity condition is present.
            """
        )

    st.markdown("#### Milestone 2 integration")
    i1, i2, i3, i4, i5 = st.columns(5)
    with i1:
        kpi_card("Staff Agent coverage", str(milestone2_quality["staff_outlets"]), "Validated outlet outputs", "good" if not milestone2_error else "bad")
    with i2:
        kpi_card("Marketing coverage", str(milestone2_quality["marketing_outlets"]), "Validated outlet outputs", "good" if not milestone2_error else "bad")
    with i3:
        kpi_card("Inventory records", f"{milestone2_quality['inventory_records']:,}", "Unique outlet/SKU/month", "good" if not milestone2_error else "bad")
    with i4:
        kpi_card("Forecasted SKUs", str(milestone2_quality["forecast_skus"]), "Latest forecasts available", "good" if not milestone2_error else "bad")
    with i5:
        kpi_card("Shared coverage", str(milestone2_quality["shared_outlets"]), "All four modules", "good" if not milestone2_error else "bad")
    st.caption(
        "Staff and Marketing use explainable quartile rules. Inventory uses stock-status, replenishment, and wastage rules. Forecasting uses the previous three months of demand after removing 120 supplied duplicate test rows."
    )

    st.markdown("#### Data quality")
    q1, q2, q3, q4, q5 = st.columns(5)
    with q1:
        kpi_card("Validation", str(quality["status"]), "Schema and ranges")
    with q2:
        kpi_card("Missing cells", str(quality["missing_cells"]), "Required measures", "good")
    with q3:
        kpi_card("Duplicate rows", str(quality["duplicate_outlet_months"]), "Outlet + month", "good")
    with q4:
        kpi_card("Identity conflicts", str(quality["identity_conflicts"]), "ID/name/location", "good")
    with q5:
        kpi_card("AOV max variance", f"{quality['aov_reconciliation_max_error_pct']:.4f}%", "Revenue vs orders × AOV", "good")

    st.info("Benchmark revenue is the monthly peer-group mean. Rankings use performance score first, followed by target achievement, revenue, and outlet ID as deterministic tie-breakers.")
