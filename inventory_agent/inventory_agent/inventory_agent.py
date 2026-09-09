import pandas as pd
from pathlib import Path


# --------------------------------------------------
# Inventory Agent - Milestone 2
# --------------------------------------------------

project_root = Path(__file__).resolve().parent.parent.parent

input_file = (
    project_root
    / "data"
    / "raw"
    / "FranchiseOps_AI_Milestone2_Inventory_Dataset.xlsx"
)

output_file = (
    project_root
    / "data"
    / "processed"
    / "inventory_agent_output.csv"
)


# --------------------------------------------------
# Load Inventory Data
# --------------------------------------------------

df = pd.read_excel(
    input_file,
    sheet_name="Raw_Outlet_Data"
)

print("Inventory records:", len(df))


# --------------------------------------------------
# Required Inventory Columns
# --------------------------------------------------

required_columns = [
    "Outlet_ID",
    "Outlet_Name",
    "Month",
    "Product_Category",
    "Product_Type",
    "SKU_ID",
    "Closing_Stock_Units",
    "Safety_Stock_Units",
    "Supplier_Lead_Time_Days",
    "Reorder_Point_Units",
    "Demand_Forecast_Next_Month_Units",
    "Stock_Status",
    "Replenishment_Required",
    "Recommended_Replenishment_Units",
    "Stock_Availability_%",
    "Inventory_Turnover_Ratio",
    "Wastage_Units",
    "Freshness_Rate_%",
    "Shelf_Life_Days",
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )


# --------------------------------------------------
# Inventory Agent Logic
# --------------------------------------------------

def generate_inventory_action(row):

    stock_status = row["Stock_Status"]
    replenishment = row["Replenishment_Required"]
    product_type = row["Product_Type"]

    if stock_status == "Critical":
        return "URGENT_REORDER"

    elif stock_status == "Low":
        return "REORDER"

    elif stock_status == "Overstocked":
        return "REDUCE_STOCK"

    elif product_type == "Perishable" and row["Wastage_Units"] > 0:
        return "MONITOR_WASTAGE"

    elif replenishment == "Yes":
        return "REORDER"

    else:
        return "NO_ACTION"


def generate_priority(row):

    if row["Stock_Status"] == "Critical":
        return "High"

    elif row["Stock_Status"] == "Low":
        return "Medium"

    elif row["Stock_Status"] == "Overstocked":
        return "Medium"

    elif row["Product_Type"] == "Perishable" and row["Wastage_Units"] > 0:
        return "Medium"

    else:
        return "Low"


def generate_explanation(row):

    status = row["Stock_Status"]

    if status == "Critical":
        return (
            "Stock is critically low compared with inventory requirements. "
            "Immediate replenishment is recommended."
        )

    elif status == "Low":
        return (
            "Stock is below the desired inventory level. "
            "Replenishment should be planned."
        )

    elif status == "Overstocked":
        return (
            "Inventory is higher than the required level. "
            "Reduce or delay replenishment to avoid excess stock."
        )

    elif (
        row["Product_Type"] == "Perishable"
        and row["Wastage_Units"] > 0
    ):
        return (
            "Inventory is currently adequate, but wastage is present. "
            "Monitor stock usage and freshness."
        )

    else:
        return (
            "Inventory level is currently healthy. "
            "No immediate action is required."
        )


df["Agent_Action"] = df.apply(
    generate_inventory_action,
    axis=1
)

df["Agent_Priority"] = df.apply(
    generate_priority,
    axis=1
)

df["Agent_Explanation"] = df.apply(
    generate_explanation,
    axis=1
)


# --------------------------------------------------
# Agent Output
# --------------------------------------------------

output_columns = [
    "Outlet_ID",
    "Outlet_Name",
    "Month",
    "Product_Category",
    "Product_Type",
    "SKU_ID",
    "Closing_Stock_Units",
    "Safety_Stock_Units",
    "Reorder_Point_Units",
    "Demand_Forecast_Next_Month_Units",
    "Stock_Status",
    "Replenishment_Required",
    "Recommended_Replenishment_Units",
    "Stock_Availability_%",
    "Inventory_Turnover_Ratio",
    "Wastage_Units",
    "Freshness_Rate_%",
    "Shelf_Life_Days",
    "Agent_Action",
    "Agent_Priority",
    "Agent_Explanation",
]

priority_order = pd.CategoricalDtype(
    categories=["High", "Medium", "Low"],
    ordered=True
)

inventory_output["Agent_Priority"] = (
    inventory_output["Agent_Priority"].astype(priority_order)
)

inventory_output = (
    inventory_output
    .sort_values(
        ["Agent_Priority", "Stock_Status"],
        ascending=[True, True]
    )
    .reset_index(drop=True)
)


# --------------------------------------------------
# Save Output
# --------------------------------------------------

output_file.parent.mkdir(
    parents=True,
    exist_ok=True
)

inventory_output.to_csv(
    output_file,
    index=False
)


# --------------------------------------------------
# Validation / Summary
# --------------------------------------------------

print("\nInventory Agent completed.")

print(
    f"Total inventory records: "
    f"{len(inventory_output)}"
)

print(
    f"Output saved to: "
    f"{output_file}"
)

print("\nAgent Action Distribution:")

print(
    inventory_output["Agent_Action"]
    .value_counts()
)

print("\nAgent Priority Distribution:")

print(
    inventory_output["Agent_Priority"]
    .value_counts()
)

print("\nCritical Inventory Items:")

print(
    inventory_output[
        inventory_output["Agent_Action"] == "URGENT_REORDER"
    ][
        [
            "Outlet_ID",
            "SKU_ID",
            "Closing_Stock_Units",
            "Demand_Forecast_Next_Month_Units",
            "Recommended_Replenishment_Units",
            "Agent_Action",
            "Agent_Priority",
        ]
    ]
    .head(10)
    .to_string(index=False)
)