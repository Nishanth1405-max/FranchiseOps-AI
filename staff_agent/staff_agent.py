import pandas as pd
from pathlib import Path


# -----------------------------------
# PATHS AND LOAD DATASET
# -----------------------------------

project_root = Path(__file__).resolve().parent.parent

dataset_path = (
    project_root
    / "data"
    / "raw"
    / "FranchiseOps_AI_Milestone2_Inventory_Dataset.xlsx"
)

output_folder = project_root / "staff_agent"
output_folder.mkdir(parents=True, exist_ok=True)

df = pd.read_excel(dataset_path)

required_columns = [
    "Outlet_ID",
    "Outlet_Name",
    "Month",
    "Employees",
    "Employee_Turnover_%",
    "Customer_Satisfaction_1_5",
    "Complaints",
]

missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

print("Dataset loaded successfully!")
print("Rows:", len(df))


# -----------------------------------
# CLEAN STAFF FIELDS
# -----------------------------------

df["Month"] = pd.to_datetime(
    df["Month"].astype(str),
    format="%Y-%m",
    errors="coerce"
)

numeric_columns = [
    "Employees",
    "Employee_Turnover_%",
    "Customer_Satisfaction_1_5",
    "Complaints",
]

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(
    subset=["Outlet_ID", "Outlet_Name", "Month"]
)


# -----------------------------------
# MONTHLY OUTLET STAFF DATA
# One record per outlet-month.
# Repeated rows are deduplicated because
# the dataset check found identical staff
# values within each outlet-month.
# -----------------------------------

monthly_outlet_staff = (
    df[
        [
            "Outlet_ID",
            "Outlet_Name",
            "Month",
            "Employees",
            "Employee_Turnover_%",
            "Customer_Satisfaction_1_5",
            "Complaints",
        ]
    ]
    .groupby(["Outlet_ID", "Outlet_Name", "Month"], as_index=False)
    .agg(
        Employees=("Employees", "mean"),
        Employee_Turnover=("Employee_Turnover_%", "mean"),
        Customer_Satisfaction=("Customer_Satisfaction_1_5", "mean"),
        Complaints=("Complaints", "sum"),
    )
)

monthly_outlet_staff = monthly_outlet_staff.sort_values(
    ["Outlet_ID", "Month"]
)


# -----------------------------------
# EXISTING OUTLET-LEVEL STAFF ANALYSIS
# -----------------------------------

staff_data = (
    monthly_outlet_staff
    .groupby(["Outlet_ID", "Outlet_Name"], as_index=False)
    .agg(
        Avg_Employees=("Employees", "mean"),
        Avg_Employee_Turnover=("Employee_Turnover", "mean"),
        Avg_Customer_Satisfaction=("Customer_Satisfaction", "mean"),
        Total_Complaints=("Complaints", "sum"),
    )
)

staff_data = staff_data.round(2)

print("Total outlets:", len(staff_data))


# -----------------------------------
# CALCULATE THRESHOLDS
# -----------------------------------

high_turnover_threshold = staff_data[
    "Avg_Employee_Turnover"
].quantile(0.75)

low_satisfaction_threshold = staff_data[
    "Avg_Customer_Satisfaction"
].quantile(0.25)

high_complaints_threshold = staff_data[
    "Total_Complaints"
].quantile(0.75)


# -----------------------------------
# STAFF STATUS LOGIC
# -----------------------------------

def get_staff_status(row):
    high_turnover = (
        row["Avg_Employee_Turnover"] >= high_turnover_threshold
    )

    low_satisfaction = (
        row["Avg_Customer_Satisfaction"] <= low_satisfaction_threshold
    )

    high_complaints = (
        row["Total_Complaints"] >= high_complaints_threshold
    )

    if high_turnover and low_satisfaction and high_complaints:
        return "Critical"

    if high_turnover or low_satisfaction or high_complaints:
        return "Needs Attention"

    return "Stable"


staff_data["Staff_Status"] = staff_data.apply(
    get_staff_status,
    axis=1
)


# -----------------------------------
# GENERATE INSIGHTS
# -----------------------------------

def generate_insight(row):
    if row["Staff_Status"] == "Critical":
        return (
            "High employee turnover, low customer satisfaction "
            "and high complaints indicate significant staff-related concerns."
        )

    if row["Staff_Status"] == "Needs Attention":
        return (
            "Staff indicators require attention due to turnover, "
            "customer satisfaction or complaint levels."
        )

    return (
        "Staff indicators appear relatively stable. "
        "Continue monitoring workforce and customer-service measures."
    )


staff_data["Insight"] = staff_data.apply(
    generate_insight,
    axis=1
)


# -----------------------------------
# GENERATE RECOMMENDATIONS
# -----------------------------------

def generate_recommendation(row):
    if row["Staff_Status"] == "Critical":
        return (
            "Review retention practices, workload distribution "
            "and targeted staff training."
        )

    if row["Staff_Status"] == "Needs Attention":
        return (
            "Monitor turnover, review staff training needs "
            "and track customer-service feedback."
        )

    return (
        "Maintain current staff-management practices "
        "and continue monitoring workforce indicators."
    )


staff_data["Recommendation"] = staff_data.apply(
    generate_recommendation,
    axis=1
)


# -----------------------------------
# WORKFORCE TREND ANALYSIS
# Compare each outlet's earliest and
# latest available month in the dataset.
# -----------------------------------

first_month = monthly_outlet_staff["Month"].min()
latest_month = monthly_outlet_staff["Month"].max()

first_records = (
    monthly_outlet_staff[
        monthly_outlet_staff["Month"] == first_month
    ][
        [
            "Outlet_ID",
            "Outlet_Name",
            "Employees",
            "Employee_Turnover",
        ]
    ]
    .rename(
        columns={
            "Employees": "Employees_First_Month",
            "Employee_Turnover": "Turnover_First_Month",
        }
    )
)

latest_records = (
    monthly_outlet_staff[
        monthly_outlet_staff["Month"] == latest_month
    ][
        [
            "Outlet_ID",
            "Outlet_Name",
            "Employees",
            "Employee_Turnover",
        ]
    ]
    .rename(
        columns={
            "Employees": "Employees_Latest_Month",
            "Employee_Turnover": "Turnover_Latest_Month",
        }
    )
)

workforce_trends = first_records.merge(
    latest_records,
    on=["Outlet_ID", "Outlet_Name"],
    how="outer"
)

workforce_trends["Employee_Change"] = (
    workforce_trends["Employees_Latest_Month"]
    - workforce_trends["Employees_First_Month"]
)

workforce_trends["Turnover_Change"] = (
    workforce_trends["Turnover_Latest_Month"]
    - workforce_trends["Turnover_First_Month"]
)

workforce_trends["Employee_Trend"] = workforce_trends[
    "Employee_Change"
].apply(
    lambda value:
        "Increased" if value > 0
        else "Decreased" if value < 0
        else "No change" if pd.notna(value)
        else "Insufficient data"
)

workforce_trends["Trend_Insight"] = workforce_trends.apply(
    lambda row: (
        f"Employee count {row['Employee_Trend'].lower()} "
        f"by {abs(row['Employee_Change']):.2f} between "
        f"{first_month.strftime('%Y-%m')} and "
        f"{latest_month.strftime('%Y-%m')}."
        if pd.notna(row["Employee_Change"])
        else "Insufficient data to compare employee count."
    ),
    axis=1
)

workforce_trends = workforce_trends.round(2)


# -----------------------------------
# MONTHLY WORKFORCE SUMMARY
# -----------------------------------

monthly_workforce_summary = (
    monthly_outlet_staff
    .groupby("Month", as_index=False)
    .agg(
        Outlets_Recorded=("Outlet_ID", "nunique"),
        Average_Employees=("Employees", "mean"),
        Average_Employee_Turnover=("Employee_Turnover", "mean"),
        Average_Customer_Satisfaction=("Customer_Satisfaction", "mean"),
        Total_Complaints=("Complaints", "sum"),
    )
    .sort_values("Month")
)

monthly_workforce_summary["Month"] = (
    monthly_workforce_summary["Month"].dt.strftime("%Y-%m")
)

monthly_workforce_summary = monthly_workforce_summary.round(2)


# -----------------------------------
# SAVE OUTPUT FILES
# -----------------------------------

staff_output_path = output_folder / "staff_agent_output.csv"
trend_output_path = output_folder / "workforce_outlet_trends.csv"
monthly_output_path = output_folder / "workforce_monthly_summary.csv"

staff_data.to_csv(staff_output_path, index=False)
workforce_trends.to_csv(trend_output_path, index=False)
monthly_workforce_summary.to_csv(monthly_output_path, index=False)


# -----------------------------------
# DISPLAY RESULTS
# -----------------------------------

print("\nStaff Agent completed successfully!")

print("\nStaff Status Distribution:")
print(staff_data["Staff_Status"].value_counts())

print("\nOutlet Workforce Trend Period:")
print(f"{first_month.strftime('%Y-%m')} to {latest_month.strftime('%Y-%m')}")

print("\nMonthly Workforce Summary (latest 5 months):")
print(monthly_workforce_summary.tail(5).to_string(index=False))

print("\nTop 10 Staff Agent Results:")
print(
    staff_data[
        [
            "Outlet_ID",
            "Outlet_Name",
            "Avg_Employees",
            "Avg_Employee_Turnover",
            "Avg_Customer_Satisfaction",
            "Total_Complaints",
            "Staff_Status",
        ]
    ].head(10).to_string(index=False)
)

print("\nOutput files saved:")
print(staff_output_path)
print(trend_output_path)
print(monthly_output_path)