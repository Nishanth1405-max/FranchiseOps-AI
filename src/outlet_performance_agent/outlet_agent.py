"""Explainable Outlet Performance Agent used by the Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def analyze_outlet(df: pd.DataFrame, outlet_id: str) -> dict | None:
    """Aggregate one outlet's monthly operating records."""
    outlet = df[df["outlet_id"] == outlet_id]
    if outlet.empty:
        return None
    return {
        "outlet_id": outlet_id,
        "records": len(outlet),
        "total_revenue": float(outlet["revenue"].sum()),
        "total_profit": float(outlet["profit"].sum()),
        "total_orders": float(outlet["orders"].sum()),
        "average_conversion_rate": float(outlet["conversion_rate"].mean()),
        "average_order_value": float(outlet["avg_order_value"].mean()),
        "average_profit_margin": float(outlet["profit_margin"].mean()),
        "average_employee_turnover": float(outlet["employee_turnover"].mean()),
        "average_customer_satisfaction": float(outlet["customer_rating"].mean()),
        "total_complaints": float(outlet["complaints"].sum()),
    }


def get_benchmark(benchmark_df: pd.DataFrame, outlet_id: str) -> pd.Series | None:
    outlet_id_column = "outlet_id" if "outlet_id" in benchmark_df else "Outlet_ID"
    match = benchmark_df[benchmark_df[outlet_id_column] == outlet_id]
    return None if match.empty else match.iloc[0]


def get_performance_score(performance_df: pd.DataFrame, outlet_id: str) -> pd.Series | None:
    outlet_id_column = "outlet_id" if "outlet_id" in performance_df else "Outlet_ID"
    match = performance_df[performance_df[outlet_id_column] == outlet_id]
    return None if match.empty else match.iloc[0]


def _row_issues(row: pd.Series) -> list[str]:
    issues: list[str] = []
    if row["profit_margin"] < 15:
        issues.append("low profit margin")
    if row["conversion_rate"] < 15:
        issues.append("low conversion rate")
    if row["customer_rating"] < 3.5:
        issues.append("low customer satisfaction")
    if row["employee_turnover"] > 10:
        issues.append("high employee turnover")
    if row["complaints"] > 20:
        issues.append("elevated complaints")
    if row["revenue_growth_pct"] < -10:
        issues.append("declining monthly revenue")
    return issues


def _recommendations(row: pd.Series) -> list[str]:
    recommendations: list[str] = []
    if row["profit_margin"] < 15:
        recommendations.append("Review operating costs and strengthen cost control.")
    if row["conversion_rate"] < 15:
        recommendations.append("Improve offers, service quality, and staff engagement to lift conversion.")
    if row["customer_rating"] < 3.5:
        recommendations.append("Investigate customer feedback and address the main service-quality gaps.")
    if row["employee_turnover"] > 10:
        recommendations.append("Improve retention through targeted training and workforce management.")
    if row["complaints"] > 20:
        recommendations.append("Analyze complaint causes, assign owners, and verify corrective actions.")
    if row["revenue_growth_pct"] < -10:
        recommendations.append("Review the latest sales mix and set a weekly revenue recovery target.")
    if not recommendations:
        recommendations.append("Maintain the operating plan and share the outlet's strongest practice with peers.")
    return recommendations


def assess_outlet_row(row: pd.Series) -> tuple[str, str, str]:
    """Return issue tags, one concise insight, and a prioritized recommendation."""
    issues = _row_issues(row)
    if row["health_category"] == "Excellent":
        insight = (
            f"{row['outlet_name']} is an excellent performer with a {row['performance_score']:.1f} "
            f"score, global rank #{int(row['performance_rank'])}, and benchmark rank "
            f"#{int(row['benchmark_rank'])}."
        )
    elif issues:
        insight = (
            f"{row['outlet_name']} is classified as {row['health_category']} and needs attention "
            f"for {', '.join(issues[:2])}; its global performance rank is "
            f"#{int(row['performance_rank'])}."
        )
    else:
        insight = (
            f"{row['outlet_name']} is classified as {row['health_category']} with a "
            f"{row['performance_score']:.1f} score and no major current operating issue."
        )
    return ", ".join(issues) or "No major issue", insight, _recommendations(row)[0]


def generate_insights(
    analysis: dict, benchmark: pd.Series, performance: pd.Series
) -> tuple[list[str], list[str]]:
    """Compatibility API for the original teammate agent implementation."""
    insights = [
        f"Outlet {analysis['outlet_id']} has a performance score of "
        f"{performance.get('Performance_Score', performance.get('performance_score'))} and is "
        f"classified as {performance.get('Performance_Category', performance.get('health_category'))}.",
        f"Its benchmark score is {benchmark.get('Benchmark_Score', benchmark.get('benchmark_score'))} "
        f"with rank #{int(benchmark.get('Benchmark_Rank', benchmark.get('benchmark_rank')))}.",
    ]
    recommendations: list[str] = []
    if analysis["average_profit_margin"] < 15:
        insights.append("Profit margin is relatively low.")
        recommendations.append("Review operating costs and improve cost control.")
    if analysis["average_conversion_rate"] < 15:
        insights.append("Conversion rate needs improvement.")
        recommendations.append("Improve offers, service quality, and staff engagement.")
    if analysis["average_customer_satisfaction"] < 3.5:
        insights.append("Customer satisfaction is below the desired level.")
        recommendations.append("Investigate complaints and improve service quality.")
    if analysis["average_employee_turnover"] > 10:
        insights.append("Employee turnover is high.")
        recommendations.append("Improve retention through training and workforce management.")
    if analysis["total_complaints"] > 800:
        insights.append("The outlet has a high number of complaints.")
        recommendations.append("Analyze complaint reasons and take corrective action.")
    return insights, recommendations or ["Maintain the current operating plan."]


def run_cli(project_root: Path, outlet_id: str) -> None:
    from src.analytics import calculate_performance_metrics
    from src.data_loader import load_outlet_data

    data_path = project_root / "data" / "raw" / "FranchiseOps_AI_Milestone1_Member1_Large_Raw_Dataset.xlsx"
    data, _ = load_outlet_data(data_path)
    data = calculate_performance_metrics(data)
    latest = data[data["outlet_id"] == outlet_id].sort_values("date").tail(1)
    if latest.empty:
        raise SystemExit(f"Outlet not found: {outlet_id}")
    row = latest.iloc[0]
    print(row["insight"])
    print("Recommendation:", row["recommendation"])


if __name__ == "__main__":
    run_cli(Path(__file__).resolve().parents[2], "OUT0706")
