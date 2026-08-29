"""FranchiseOps AI - Milestone 1 Outlet Performance Dashboard."""

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


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "raw" / "FranchiseOps_AI_Milestone1_Member1_Large_Raw_Dataset.xlsx"

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


try:
    data, quality = get_data(str(DATA_PATH))
except (FileNotFoundError, DataValidationError) as exc:
    st.error(f"The dashboard could not load a valid dataset: {exc}")
    st.stop()


st.sidebar.markdown("## FranchiseOps AI")
st.sidebar.caption("Milestone 1 · Outlet Intelligence")
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

month_label = pd.Timestamp(snapshot_month).strftime("%B %Y")
st.title("Outlet Performance Intelligence")
st.markdown(
    f"""<div class="hero"><div class="hero-kicker">FranchiseOps AI · Milestone 1</div>
    <p class="hero-copy">Monitor sales and profit, compare franchise locations, measure outlet health, and convert operating signals into prioritized actions. Current operating snapshot: <b>{month_label}</b>.</p></div>""",
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
        kpi_card("Peer revenue index", f"{attainment:.1f}%", f"Gap {money(total_revenue - total_target)}", "good" if attainment >= 100 else "warn")
    with k3:
        kpi_card("Average health score", f"{average_score:.1f}/100", "Weighted across 7 drivers", "good" if average_score >= 65 else "warn")
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
    trend.add_trace(go.Scatter(x=monthly["date"], y=monthly["target"], name="Peer benchmark", mode="lines+markers", line=dict(color="#94A3B8", width=2, dash="dash")))
    trend.update_layout(title="Revenue vs peer benchmark", yaxis_title="Revenue (₹)", hovermode="x unified")
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
        labels={"target_achievement_pct": "Peer revenue index (%)", "performance_score": "Performance score", "health_category": "Health"},
        title="Performance matrix",
    )
    matrix.add_vline(x=100, line_dash="dash", line_color="#64748B")
    matrix.add_hline(y=70, line_dash="dash", line_color="#64748B")
    st.plotly_chart(style_figure(matrix, 420), width="stretch", config={"displayModeBar": False, "responsive": True})


with benchmark_tab:
    st.markdown("### Outlet benchmarking")
    st.markdown(f"<p class='section-note'>Unique peer ranking for {month_label}. The chart shows the leading 20 selected outlets; the table and download contain all results.</p>", unsafe_allow_html=True)
    chart_snapshot = snapshot.head(20)
    benchmark_chart = px.bar(
        chart_snapshot.sort_values("performance_score"), x="performance_score", y="outlet_name", orientation="h",
        color="health_category", color_discrete_map=HEALTH_COLORS, text="performance_score",
        hover_data={"benchmark_score": ":.1f", "target_achievement_pct": ":.1f", "benchmark_gap_pct": ":+.1f", "peer_rank": True},
        labels={"performance_score": "Performance score", "outlet_name": "Outlet", "health_category": "Health"},
        title="Peer performance ranking",
    )
    benchmark_chart.update_traces(texttemplate="%{text:.1f}", textposition="outside", cliponaxis=False)
    benchmark_chart.update_xaxes(range=[0, 105])
    st.plotly_chart(style_figure(benchmark_chart, max(390, 38 * len(chart_snapshot))), width="stretch", config={"displayModeBar": False, "responsive": True})

    display = snapshot[["peer_rank", "outlet_name", "city", "region", "revenue", "target_achievement_pct", "benchmark_score", "performance_score", "health_category", "alert_level"]].rename(
        columns={"peer_rank": "Rank", "outlet_name": "Outlet", "city": "City", "region": "Region", "revenue": "Revenue", "target_achievement_pct": "Peer index %", "benchmark_score": "Benchmark", "performance_score": "Score", "health_category": "Health", "alert_level": "Alert"}
    )
    st.dataframe(
        display, hide_index=True, width="stretch",
        column_config={
            "Revenue": st.column_config.NumberColumn(format="₹ %.0f"),
            "Peer index %": st.column_config.NumberColumn(format="%.1f%%"),
            "Benchmark": st.column_config.NumberColumn(format="%.1f"),
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
        kpi_card("Performance score", f"{row['performance_score']:.1f}", str(row["health_category"]), "good" if row["performance_score"] >= 65 else "warn")
    with d2:
        kpi_card("Monthly revenue", money(float(row["revenue"])), f"{row['target_achievement_pct']:.1f}% of peer benchmark", "good" if row["target_achievement_pct"] >= 100 else "warn")
    with d3:
        kpi_card("Customer rating", f"{row['customer_rating']:.2f}/5", f"Complaint rate {row['complaint_rate']:.2f}%")
    with d4:
        kpi_card("Conversion rate", f"{row['conversion_rate']:.1f}%", f"Alert: {row['alert_level']}", "bad" if row["alert_level"] == "High" else "")

    c1, c2 = st.columns([1.55, 1])
    history_chart = go.Figure()
    history_chart.add_trace(go.Bar(x=selected_history["date"], y=selected_history["revenue"], name="Revenue", marker_color="#2DD4BF"))
    history_chart.add_trace(go.Scatter(x=selected_history["date"], y=selected_history["benchmark_revenue"], name="Peer benchmark", mode="lines+markers", line=dict(color="#FBBF24", width=2)))
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

    score_history = px.line(selected_history, x="date", y="target_achievement_pct", markers=True, title="Peer revenue index trend", labels={"date": "Month", "target_achievement_pct": "Peer index (%)"})
    score_history.update_traces(line_color="#60A5FA", line_width=3)
    score_history.add_hline(y=100, line_dash="dash", line_color="#64748B", annotation_text="Peer benchmark")
    score_history.update_yaxes(rangemode="tozero")
    st.plotly_chart(style_figure(score_history, 330), width="stretch", config={"displayModeBar": False, "responsive": True})


with agent_tab:
    st.markdown("### Outlet Performance Agent")
    st.markdown("<p class='section-note'>Deterministic, explainable findings from the integrated performance agent, ranked by severity and score. No external API key is required.</p>", unsafe_allow_html=True)
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
    for _, agent_row in agent_rows.head(50).iterrows():
        show_agent_card(agent_row)

    export_columns = ["peer_rank", "outlet_id", "outlet_name", "performance_score", "health_category", "alert_level", "issue_tags", "insight", "recommendation"]
    st.download_button(
        "Download agent insights (CSV)", agent_rows[export_columns].to_csv(index=False).encode("utf-8"),
        file_name=f"outlet_agent_insights_{pd.Timestamp(snapshot_month):%Y_%m}.csv", mime="text/csv",
    )


with method_tab:
    st.markdown("### Scoring methodology")
    st.markdown("<p class='section-note'>The supplied benchmarking and performance-score outputs are cross-validated, then joined to cleaned monthly operating records.</p>", unsafe_allow_html=True)
    method_cols = st.columns(5)
    descriptions = {
        "Sales & profit": "Sales rank 20% + profit rank 20%.",
        "Margin & conversion": "Margin rank 15% + conversion rank 15%.",
        "Average order value": "AOV rank contributes 10%.",
        "Customer satisfaction": "Satisfaction rank contributes 10%.",
        "Complaint control": "Lower complaint rank contributes 10%.",
    }
    for column, (name, weight) in zip(method_cols, SCORE_WEIGHTS.items()):
        with column:
            st.markdown(f"<div class='method-card'><b>{html.escape(name)}</b><br><span>{weight:.0%} weight<br>{html.escape(descriptions[name])}</span></div>", unsafe_allow_html=True)

    st.markdown("#### Health and alert rules")
    h1, h2 = st.columns(2)
    with h1:
        st.dataframe(
            pd.DataFrame({"Health category": HEALTH_ORDER, "Score range": ["80-100", "65-79.9", "50-64.9", "Below 50"]}),
            hide_index=True, width="stretch",
        )
    with h2:
        st.markdown(
            """
            - **High:** Critical score, negative profit margin, or customer rating below 2.5.
            - **Medium:** Needs Improvement, below-average benchmark, or an operating risk threshold is breached.
            - **Low:** no high- or medium-severity condition is present.
            """
        )

    st.markdown("#### Data quality")
    q1, q2, q3, q4, q5 = st.columns(5)
    with q1:
        kpi_card("Validation", str(quality["status"]), "Schema and ranges")
    with q2:
        kpi_card("Imputed cells", str(quality["imputed_cells"]), "Median-cleaned inputs", "good")
    with q3:
        kpi_card("Duplicates removed", str(quality["duplicates_removed"]), "Outlet + month", "good")
    with q4:
        kpi_card("Identity conflicts", str(quality["identity_conflicts"]), "ID/name/location", "good")
    with q5:
        kpi_card("AOV max variance", f"{quality['aov_reconciliation_max_error_pct']:.4f}%", "Revenue vs orders × AOV", "good")

    st.info("Benchmark scores summarize 40 months of sales, profit, margin, conversion, order value, and satisfaction. Filtered peer ranking uses performance score, benchmark score, current revenue, and outlet ID as deterministic tie-breakers.")
