"""Overall outlet health scoring from the teammate feature branch."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


OUTPUT_COLUMNS = [
    "Outlet_ID",
    "Outlet_Name",
    "Benchmark_Score",
    "Benchmark_Rank",
    "Benchmark_Category",
    "Performance_Score",
    "Performance_Rank",
    "Performance_Category",
]


def classify_performance(score: float) -> str:
    if score >= 80:
        return "Excellent"
    if score >= 65:
        return "Good"
    if score >= 50:
        return "Needs Improvement"
    return "Critical"


def calculate_performance_scores(
    benchmark_df: pd.DataFrame, *, include_components: bool = False
) -> pd.DataFrame:
    """Convert benchmark ranks to the seven weighted performance drivers."""
    df = benchmark_df.copy()
    max_rank = int(df["Benchmark_Rank"].max())
    rank_sources = {
        "Sales_Score": "Sales_Rank",
        "Profit_Score": "Profit_Rank",
        "Margin_Score": "Margin_Rank",
        "Conversion_Score": "Conversion_Rank",
        "AOV_Score": "AOV_Rank",
        "Satisfaction_Score": "Satisfaction_Rank",
    }
    for score_column, rank_column in rank_sources.items():
        df[score_column] = (max_rank - df[rank_column] + 1) / max_rank * 100

    complaint_rank = df["Total_Complaints"].rank(ascending=True, method="min")
    df["Complaint_Score"] = (max_rank - complaint_rank + 1) / max_rank * 100
    df["Performance_Score"] = (
        df["Sales_Score"] * 0.20
        + df["Profit_Score"] * 0.20
        + df["Margin_Score"] * 0.15
        + df["Conversion_Score"] * 0.15
        + df["AOV_Score"] * 0.10
        + df["Satisfaction_Score"] * 0.10
        + df["Complaint_Score"] * 0.10
    ).round(2)
    df["Performance_Category"] = df["Performance_Score"].apply(classify_performance)
    df["Performance_Rank"] = (
        df["Performance_Score"].rank(method="min", ascending=False).astype(int)
    )
    df = df.sort_values("Performance_Rank").reset_index(drop=True)
    if include_components:
        return df
    return df[OUTPUT_COLUMNS]


def run(project_root: Path) -> None:
    input_file = project_root / "benchmarking" / "benchmark_output.csv"
    output_file = project_root / "performance_score" / "performance_score_output.csv"
    benchmark = pd.read_csv(input_file)
    output = calculate_performance_scores(benchmark)
    output.to_csv(output_file, index=False)
    print(f"Performance scoring completed for {len(output)} outlets.")


if __name__ == "__main__":
    run(Path(__file__).resolve().parent.parent)
