"""Dashboard analytics over the integrated Milestone 1 team outputs."""

from __future__ import annotations

from collections import OrderedDict

import numpy as np
import pandas as pd

from src.outlet_performance_agent.outlet_agent import assess_outlet_row


# Five grouped methodology cards preserve the dashboard's existing layout.
SCORE_WEIGHTS = OrderedDict(
    [
        ("Sales & profit", 0.40),
        ("Margin & conversion", 0.30),
        ("Average order value", 0.10),
        ("Customer satisfaction", 0.10),
        ("Complaint control", 0.10),
    ]
)

COMPONENT_COLUMNS = OrderedDict(
    [
        ("Sales", "sales_component_score"),
        ("Profit", "profit_component_score"),
        ("Profit margin", "margin_component_score"),
        ("Conversion", "conversion_component_score"),
        ("Average order value", "aov_component_score"),
        ("Customer satisfaction", "satisfaction_component_score"),
        ("Complaint control", "complaint_component_score"),
    ]
)

HEALTH_ORDER = ["Excellent", "Good", "Needs Improvement", "Critical"]
HEALTH_COLORS = {
    "Excellent": "#20D9A2",
    "Good": "#60A5FA",
    "Needs Improvement": "#FBBF24",
    "Critical": "#FB7185",
}


def _safe_percentage(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return pd.Series(
        np.where(denominator > 0, numerator / denominator * 100, 0.0),
        index=numerator.index,
    )


def _alert_level(df: pd.DataFrame) -> pd.Series:
    high = (
        df["health_category"].eq("Critical")
        | df["profit_margin"].lt(0)
        | df["customer_rating"].lt(2.5)
    )
    medium = (
        df["health_category"].eq("Needs Improvement")
        | df["benchmark_category"].eq("Below Average")
        | df["profit_margin"].lt(15)
        | df["conversion_rate"].lt(15)
        | df["customer_rating"].lt(3.5)
        | df["employee_turnover"].gt(10)
        | df["complaints"].gt(20)
    )
    return pd.Series(
        np.select([high, medium], ["High", "Medium"], default="Low"),
        index=df.index,
        dtype="string",
    )


def calculate_performance_metrics(source: pd.DataFrame) -> pd.DataFrame:
    """Add monthly peer context and agent assessments without replacing team scores."""
    df = source.copy()
    df["target_achievement_pct"] = _safe_percentage(df["revenue"], df["benchmark_revenue"])
    df["benchmark_gap_pct"] = df["target_achievement_pct"] - 100
    df["revenue_growth_pct"] = _safe_percentage(
        df["revenue"] - df["previous_month_revenue"], df["previous_month_revenue"]
    )
    df["rank"] = df["performance_rank"].astype(int)
    df["alert_level"] = _alert_level(df)

    assessments = df.apply(assess_outlet_row, axis=1, result_type="expand")
    assessments.columns = ["issue_tags", "insight", "recommendation"]
    df[["issue_tags", "insight", "recommendation"]] = assessments
    return df.sort_values(["date", "performance_rank", "outlet_id"]).reset_index(drop=True)


def rerank_snapshot(snapshot: pd.DataFrame) -> pd.DataFrame:
    """Create a unique peer rank for the outlets currently selected in the UI."""
    ranked = snapshot.sort_values(
        ["performance_score", "benchmark_score", "revenue", "outlet_id"],
        ascending=[False, False, False, True],
    ).copy()
    ranked["peer_rank"] = np.arange(1, len(ranked) + 1)
    return ranked


def score_component_frame(row: pd.Series) -> pd.DataFrame:
    weights = [0.20, 0.20, 0.15, 0.15, 0.10, 0.10, 0.10]
    return pd.DataFrame(
        {
            "component": list(COMPONENT_COLUMNS.keys()),
            "score": [float(row[column]) for column in COMPONENT_COLUMNS.values()],
            "weight": weights,
        }
    )
