import pandas as pd
from pathlib import Path

# Load dataset
project_root = Path(__file__).resolve().parent.parent
dataset_path = project_root / "data" / "sales_outlet_data.xlsx"
df = pd.read_excel(dataset_path)

print("Rows:", len(df))
print("Columns:", len(df.columns))

# -----------------------------
# STEP 2: KPI Calculation
# -----------------------------

# Group by outlet and aggregate
outlet_kpis = df.groupby(["Outlet_ID", "Outlet_Name"]).agg(
    Total_Sales=("Sales_Revenue_INR", "sum"),
    Total_Profit=("Profit_INR", "sum"),
    Avg_Profit_Margin=("Profit_Margin_%", "mean"),
    Total_Orders=("Orders", "sum"),
    Total_Footfall=("Footfall", "sum"),
    Avg_Conversion_Rate=("Conversion_Rate_%", "mean"),
    Avg_Order_Value=("Average_Order_Value_INR", "mean"),
    Avg_Customer_Satisfaction=("Customer_Satisfaction_1_5", "mean"),
    Total_Complaints=("Complaints", "sum"),
    Months_Recorded=("Month", "nunique")
).reset_index()

# Derived KPI: Average monthly sales
outlet_kpis["Avg_Monthly_Sales"] = (
    outlet_kpis["Total_Sales"] / outlet_kpis["Months_Recorded"]
)

# Round for readability
outlet_kpis = outlet_kpis.round(2)

print("\nOutlet-level KPI table (first 5 rows):")
print(outlet_kpis.head())

print("\nTotal outlets:", len(outlet_kpis))

# Save intermediate output
output_path = project_root / "benchmarking" / "outlet_kpis.csv"
outlet_kpis.to_csv(output_path, index=False)
print(f"\nSaved KPI table to: {output_path}")

# -----------------------------
# STEP 3: Rankings
# -----------------------------

# Individual KPI ranks (1 = best)
outlet_kpis["Sales_Rank"] = outlet_kpis["Total_Sales"].rank(ascending=False, method="min").astype(int)
outlet_kpis["Profit_Rank"] = outlet_kpis["Total_Profit"].rank(ascending=False, method="min").astype(int)
outlet_kpis["Margin_Rank"] = outlet_kpis["Avg_Profit_Margin"].rank(ascending=False, method="min").astype(int)
outlet_kpis["Conversion_Rank"] = outlet_kpis["Avg_Conversion_Rate"].rank(ascending=False, method="min").astype(int)
outlet_kpis["AOV_Rank"] = outlet_kpis["Avg_Order_Value"].rank(ascending=False, method="min").astype(int)
outlet_kpis["Satisfaction_Rank"] = outlet_kpis["Avg_Customer_Satisfaction"].rank(ascending=False, method="min").astype(int)

# -----------------------------
# Overall Benchmark Score (weighted)
# -----------------------------
# Normalize each KPI to 0-1 scale so they're comparable, then combine with weights.

def normalize(col):
    return (col - col.min()) / (col.max() - col.min())

outlet_kpis["norm_sales"] = normalize(outlet_kpis["Total_Sales"])
outlet_kpis["norm_profit"] = normalize(outlet_kpis["Total_Profit"])
outlet_kpis["norm_margin"] = normalize(outlet_kpis["Avg_Profit_Margin"])
outlet_kpis["norm_conversion"] = normalize(outlet_kpis["Avg_Conversion_Rate"])
outlet_kpis["norm_aov"] = normalize(outlet_kpis["Avg_Order_Value"])
outlet_kpis["norm_satisfaction"] = normalize(outlet_kpis["Avg_Customer_Satisfaction"])

# Weights (adjust with team later if needed — sum should be 1.0)
outlet_kpis["Benchmark_Score"] = (
    outlet_kpis["norm_sales"] * 0.25 +
    outlet_kpis["norm_profit"] * 0.25 +
    outlet_kpis["norm_margin"] * 0.15 +
    outlet_kpis["norm_conversion"] * 0.15 +
    outlet_kpis["norm_aov"] * 0.10 +
    outlet_kpis["norm_satisfaction"] * 0.10
) * 100

outlet_kpis["Benchmark_Score"] = outlet_kpis["Benchmark_Score"].round(2)
outlet_kpis["Benchmark_Rank"] = outlet_kpis["Benchmark_Score"].rank(ascending=False, method="min").astype(int)

# Drop helper normalized columns (optional, keep table clean)
outlet_kpis = outlet_kpis.drop(columns=[
    "norm_sales", "norm_profit", "norm_margin",
    "norm_conversion", "norm_aov", "norm_satisfaction"
])

# -----------------------------
# STEP 4: Benchmark Categories (percentile-based)
# -----------------------------

def categorize(score, series):
    p75 = series.quantile(0.75)
    p50 = series.quantile(0.50)
    p25 = series.quantile(0.25)
    if score >= p75:
        return "Top Performer"
    elif score >= p50:
        return "Above Average"
    elif score >= p25:
        return "Average"
    else:
        return "Below Average"

outlet_kpis["Benchmark_Category"] = outlet_kpis["Benchmark_Score"].apply(
    lambda x: categorize(x, outlet_kpis["Benchmark_Score"])
)

# Sort by rank for readability
outlet_kpis = outlet_kpis.sort_values("Benchmark_Rank").reset_index(drop=True)

print("\nFinal benchmarking table (top 10 outlets):")
print(outlet_kpis.head(10)[["Outlet_ID", "Outlet_Name", "Benchmark_Score", "Benchmark_Rank", "Benchmark_Category"]])

print("\nCategory distribution:")
print(outlet_kpis["Benchmark_Category"].value_counts())

# Save final output
final_output_path = project_root / "benchmarking" / "benchmark_output.csv"
outlet_kpis.to_csv(final_output_path, index=False)
print(f"\nSaved final benchmarking output to: {final_output_path}")