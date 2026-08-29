"""Outlet KPI aggregation and benchmarking from the teammate feature branch."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def build_outlet_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate the supplied monthly workbook to one KPI row per outlet."""
    outlet_kpis = (
        df.groupby(["Outlet_ID", "Outlet_Name"])
        .agg(
            Total_Sales=("Sales_Revenue_INR", "sum"),
            Total_Profit=("Profit_INR", "sum"),
            Avg_Profit_Margin=("Profit_Margin_%", "mean"),
            Total_Orders=("Orders", "sum"),
            Total_Footfall=("Footfall", "sum"),
            Avg_Conversion_Rate=("Conversion_Rate_%", "mean"),
            Avg_Order_Value=("Average_Order_Value_INR", "mean"),
            Avg_Customer_Satisfaction=("Customer_Satisfaction_1_5", "mean"),
            Total_Complaints=("Complaints", "sum"),
            Months_Recorded=("Month", "nunique"),
        )
        .reset_index()
    )
    outlet_kpis["Avg_Monthly_Sales"] = (
        outlet_kpis["Total_Sales"] / outlet_kpis["Months_Recorded"]
    )
    return outlet_kpis.round(2)


def _normalise(series: pd.Series) -> pd.Series:
    spread = series.max() - series.min()
    if spread == 0 or pd.isna(spread):
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - series.min()) / spread


def calculate_benchmarks(outlet_kpis: pd.DataFrame) -> pd.DataFrame:
    """Calculate KPI ranks, weighted benchmark score, and percentile category."""
    df = outlet_kpis.copy()
    ranking_specs = {
        "Sales_Rank": "Total_Sales",
        "Profit_Rank": "Total_Profit",
        "Margin_Rank": "Avg_Profit_Margin",
        "Conversion_Rank": "Avg_Conversion_Rate",
        "AOV_Rank": "Avg_Order_Value",
        "Satisfaction_Rank": "Avg_Customer_Satisfaction",
    }
    for rank_column, value_column in ranking_specs.items():
        df[rank_column] = df[value_column].rank(ascending=False, method="min").astype(int)

    weights = {
        "Total_Sales": 0.25,
        "Total_Profit": 0.25,
        "Avg_Profit_Margin": 0.15,
        "Avg_Conversion_Rate": 0.15,
        "Avg_Order_Value": 0.10,
        "Avg_Customer_Satisfaction": 0.10,
    }
    df["Benchmark_Score"] = sum(_normalise(df[column]) * weight for column, weight in weights.items())
    df["Benchmark_Score"] = (df["Benchmark_Score"] * 100).round(2)
    df["Benchmark_Rank"] = df["Benchmark_Score"].rank(ascending=False, method="min").astype(int)

    p75, p50, p25 = (
        df["Benchmark_Score"].quantile(0.75),
        df["Benchmark_Score"].quantile(0.50),
        df["Benchmark_Score"].quantile(0.25),
    )
    df["Benchmark_Category"] = np.select(
        [
            df["Benchmark_Score"] >= p75,
            df["Benchmark_Score"] >= p50,
            df["Benchmark_Score"] >= p25,
        ],
        ["Top Performer", "Above Average", "Average"],
        default="Below Average",
    )
    return df.sort_values("Benchmark_Rank").reset_index(drop=True)


def run(project_root: Path) -> None:
    workbook = project_root / "data" / "raw" / "FranchiseOps_AI_Milestone1_Member1_Large_Raw_Dataset.xlsx"
    raw = pd.read_excel(workbook, sheet_name="Raw_Outlet_Data")
    outlet_kpis = build_outlet_kpis(raw)
    output = calculate_benchmarks(outlet_kpis)
    destination = project_root / "benchmarking"
    destination.mkdir(parents=True, exist_ok=True)
    outlet_kpis.to_csv(destination / "outlet_kpis.csv", index=False)
    output.to_csv(destination / "benchmark_output.csv", index=False)
    print(f"Benchmarking completed for {len(output)} outlets.")


if __name__ == "__main__":
    run(Path(__file__).resolve().parent.parent)
