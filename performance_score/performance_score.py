import pandas as pd
from pathlib import Path

# --------------------------------------------------
# Performance Score - Milestone 1
# --------------------------------------------------

# Project paths
project_root = Path(__file__).resolve().parent.parent
input_file = project_root / "performance_score" / "benchmark_output.csv"
output_file = project_root / "performance_score" / "performance_score_output.csv"

# Load benchmarking output
df = pd.read_csv(input_file)

# --------------------------------------------------
# Score components
# --------------------------------------------------

# Convert KPI ranks into performance percentages.
# Rank 1 is the best, while rank 750 is the lowest.
max_rank = df["Benchmark_Rank"].max()

df["Sales_Score"] = (max_rank - df["Sales_Rank"] + 1) / max_rank * 100
df["Profit_Score"] = (max_rank - df["Profit_Rank"] + 1) / max_rank * 100
df["Margin_Score"] = (max_rank - df["Margin_Rank"] + 1) / max_rank * 100
df["Conversion_Score"] = (
    (max_rank - df["Conversion_Rank"] + 1) / max_rank * 100
)
df["AOV_Score"] = (max_rank - df["AOV_Rank"] + 1) / max_rank * 100
df["Satisfaction_Score"] = (
    (max_rank - df["Satisfaction_Rank"] + 1) / max_rank * 100
)

# Complaints are different:
# fewer complaints = better performance.
complaint_rank = df["Total_Complaints"].rank(
    ascending=True,
    method="min"
)

df["Complaint_Score"] = (
    (max_rank - complaint_rank + 1) / max_rank * 100
)

# --------------------------------------------------
# Overall Performance Score
# --------------------------------------------------

df["Performance_Score"] = (
    df["Sales_Score"] * 0.20
    + df["Profit_Score"] * 0.20
    + df["Margin_Score"] * 0.15
    + df["Conversion_Score"] * 0.15
    + df["AOV_Score"] * 0.10
    + df["Satisfaction_Score"] * 0.10
    + df["Complaint_Score"] * 0.10
)

df["Performance_Score"] = df["Performance_Score"].round(2)

# --------------------------------------------------
# Performance Health Category
# --------------------------------------------------

def classify_performance(score):
    if score >= 80:
        return "Excellent"
    elif score >= 65:
        return "Good"
    elif score >= 50:
        return "Needs Improvement"
    else:
        return "Critical"


df["Performance_Category"] = df["Performance_Score"].apply(
    classify_performance
)

# --------------------------------------------------
# Performance Rank
# --------------------------------------------------

df["Performance_Rank"] = (
    df["Performance_Score"]
    .rank(method="min", ascending=False)
    .astype(int)
)

# --------------------------------------------------
# Select final output columns
# --------------------------------------------------

output_columns = [
    "Outlet_ID",
    "Outlet_Name",
    "Benchmark_Score",
    "Benchmark_Rank",
    "Benchmark_Category",
    "Performance_Score",
    "Performance_Rank",
    "Performance_Category",
]

performance_output = df[output_columns].sort_values(
    "Performance_Rank"
)

# Save output
performance_output.to_csv(output_file, index=False)

print("Performance Score calculation completed.")
print(f"Total outlets scored: {len(performance_output)}")
print(f"Output saved to: {output_file}")

print("\nPerformance Category Distribution:")
print(
    performance_output["Performance_Category"]
    .value_counts()
    .sort_index()
)

print("\nTop 10 Performing Outlets:")
print(performance_output.head(10).to_string(index=False))