import math
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# Inventory Agent - Milestone 2
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "FranchiseOps_AI_Milestone2_Inventory_Dataset.xlsx"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "inventory_agent_output.csv"
)


REQUIRED_COLUMNS = [
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


OUTPUT_COLUMNS = [
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
    "Agent_Recommended_Replenishment_Units",
    "Agent_Daily_Demand_Units",
    "Agent_Lead_Time_Demand_Units",
    "Agent_Projected_Stock_At_Arrival_Units",
    "Agent_Days_Of_Stock_Cover",
    "Agent_Stock_To_Reorder_Ratio",
    "Agent_Wastage_Rate_%",
    "Stock_Availability_%",
    "Inventory_Turnover_Ratio",
    "Wastage_Units",
    "Freshness_Rate_%",
    "Shelf_Life_Days",
    "Agent_Action",
    "Agent_Priority",
    "Agent_Explanation",
]


DAYS_PER_MONTH = 30
URGENT_REORDER_RATIO = 0.50
OVERSTOCK_RATIO = 2.00
WASTAGE_RATE_ALERT_PERCENT = 5.00
LOW_FRESHNESS_PERCENT = 95.00
SHORT_SHELF_LIFE_DAYS = 7


def load_inventory_data(path: str | Path = INPUT_FILE) -> pd.DataFrame:
    """Load the Milestone 2 inventory sheet."""
    return pd.read_excel(path, sheet_name="Raw_Outlet_Data")


def prepare_inventory_data(data: pd.DataFrame) -> pd.DataFrame:
    """Validate inventory fields and remove duplicate outlet/SKU/month rows."""
    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    output = data.copy()

    output["Month"] = pd.to_datetime(
        output["Month"],
        format="%Y-%m",
        errors="coerce",
    )

    numeric_columns = [
        "Closing_Stock_Units",
        "Safety_Stock_Units",
        "Supplier_Lead_Time_Days",
        "Reorder_Point_Units",
        "Demand_Forecast_Next_Month_Units",
        "Recommended_Replenishment_Units",
        "Stock_Availability_%",
        "Inventory_Turnover_Ratio",
        "Wastage_Units",
        "Freshness_Rate_%",
        "Shelf_Life_Days",
    ]

    for column in numeric_columns:
        output[column] = pd.to_numeric(
            output[column],
            errors="coerce",
        )

    if output[REQUIRED_COLUMNS].isna().any().any():
        raise ValueError(
            "Inventory data contains missing or invalid required values."
        )

    non_negative_columns = [
        "Closing_Stock_Units",
        "Safety_Stock_Units",
        "Supplier_Lead_Time_Days",
        "Reorder_Point_Units",
        "Demand_Forecast_Next_Month_Units",
        "Recommended_Replenishment_Units",
        "Inventory_Turnover_Ratio",
        "Wastage_Units",
        "Shelf_Life_Days",
    ]

    if (output[non_negative_columns] < 0).any().any():
        raise ValueError(
            "Inventory quantities and rates cannot be negative."
        )

    if not output["Stock_Availability_%"].between(0, 100).all():
        raise ValueError(
            "Stock availability must be between 0 and 100."
        )

    if not output["Freshness_Rate_%"].between(0, 100).all():
        raise ValueError(
            "Freshness rate must be between 0 and 100."
        )

    return (
        output
        .drop_duplicates(
            subset=["Outlet_ID", "SKU_ID", "Month"],
            keep="first",
        )
        .reset_index(drop=True)
    )


def calculate_inventory_metrics(row: pd.Series) -> pd.Series:
    """Calculate operational inventory metrics without relying on source labels."""
    closing_stock = max(float(row["Closing_Stock_Units"]), 0)
    safety_stock = max(float(row["Safety_Stock_Units"]), 0)
    reorder_point = max(float(row["Reorder_Point_Units"]), 0)
    forecast = max(float(row["Demand_Forecast_Next_Month_Units"]), 0)
    lead_time_days = max(float(row["Supplier_Lead_Time_Days"]), 0)
    wastage_units = max(float(row["Wastage_Units"]), 0)

    daily_demand = forecast / DAYS_PER_MONTH
    lead_time_demand = daily_demand * lead_time_days
    projected_stock_at_arrival = closing_stock - lead_time_demand

    days_of_stock_cover = (
        closing_stock / daily_demand
        if daily_demand
        else math.inf
    )

    calculated_replenishment = max(
        0,
        round(forecast + safety_stock - closing_stock),
    )

    stock_to_reorder_ratio = (
        closing_stock / reorder_point
        if reorder_point
        else math.inf
    )

    wastage_rate_percent = (
        wastage_units
        / max(closing_stock + wastage_units, 1)
        * 100
    )

    return pd.Series(
        {
            "Agent_Daily_Demand_Units": daily_demand,
            "Agent_Lead_Time_Demand_Units": lead_time_demand,
            "Agent_Projected_Stock_At_Arrival_Units": (
                projected_stock_at_arrival
            ),
            "Agent_Days_Of_Stock_Cover": days_of_stock_cover,
            "Agent_Stock_To_Reorder_Ratio": stock_to_reorder_ratio,
            "Agent_Wastage_Rate_%": wastage_rate_percent,
            "Agent_Recommended_Replenishment_Units": (
                calculated_replenishment
            ),
        }
    )


def generate_inventory_decision(row: pd.Series) -> pd.Series:
    """Return an action, priority, and explanation from calculated metrics."""
    projected_stock = row["Agent_Projected_Stock_At_Arrival_Units"]
    safety_stock = row["Safety_Stock_Units"]
    stock_ratio = row["Agent_Stock_To_Reorder_Ratio"]
    is_perishable = row["Product_Type"] == "Perishable"

    waste_risk = (
        row["Agent_Wastage_Rate_%"] >= WASTAGE_RATE_ALERT_PERCENT
        or row["Freshness_Rate_%"] < LOW_FRESHNESS_PERCENT
        or row["Shelf_Life_Days"] <= SHORT_SHELF_LIFE_DAYS
    )

    if projected_stock <= 0 or stock_ratio <= URGENT_REORDER_RATIO:
        action = "URGENT_REORDER"
        priority = "High"
        explanation = (
            "Stock is expected to run out before the supplier lead time ends, "
            "or is at or below 50% of the reorder point. Reorder immediately."
        )
    elif projected_stock <= safety_stock or stock_ratio <= 1:
        action = "REORDER"
        priority = "Medium"
        explanation = (
            "Projected stock at supplier arrival is at or below safety stock, "
            "or current stock is at or below the reorder point. "
            "Plan replenishment."
        )
    elif stock_ratio >= OVERSTOCK_RATIO:
        action = "REDUCE_STOCK"
        priority = "Low"
        explanation = (
            "Current stock is at least twice the reorder point. "
            "Pause or reduce incoming replenishment and consider transfer "
            "or promotion actions."
        )
    elif is_perishable and waste_risk:
        action = "MONITOR_WASTAGE"
        priority = "Medium"
        explanation = (
            "Perishable inventory has elevated wastage, low freshness, or "
            "short remaining shelf life. Monitor usage and reduce avoidable "
            "spoilage."
        )
    else:
        action = "NO_ACTION"
        priority = "Low"
        explanation = (
            "Stock is expected to remain above safety stock through supplier "
            "lead time, with no material overstock or perishability risk."
        )

    return pd.Series(
        {
            "Agent_Action": action,
            "Agent_Priority": priority,
            "Agent_Explanation": explanation,
        }
    )


def build_inventory_agent_output(data: pd.DataFrame) -> pd.DataFrame:
    """Run cleaning, metric calculation, decision logic, and prioritization."""
    output = prepare_inventory_data(data)

    agent_metrics = output.apply(
        calculate_inventory_metrics,
        axis=1,
    )

    output = pd.concat(
        [output, agent_metrics],
        axis=1,
    )

    agent_decisions = output.apply(
        generate_inventory_decision,
        axis=1,
    )

    output = pd.concat(
        [output, agent_decisions],
        axis=1,
    )

    priority_order = pd.CategoricalDtype(
        categories=["High", "Medium", "Low"],
        ordered=True,
    )

    output["Agent_Priority"] = (
        output["Agent_Priority"].astype(priority_order)
    )

    return (
        output[OUTPUT_COLUMNS]
        .sort_values(
            ["Agent_Priority", "Stock_Status", "Outlet_ID", "SKU_ID", "Month"],
            ascending=[True, True, True, True, True],
        )
        .reset_index(drop=True)
    )


def save_output(
    output: pd.DataFrame,
    path: str | Path = OUTPUT_FILE,
) -> None:
    """Save Inventory Agent output to CSV."""
    destination = Path(path)
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        destination,
        index=False,
    )


def main() -> None:
    """Run the Inventory Agent against the Milestone 2 dataset."""
    source = load_inventory_data()

    print("Inventory records:", len(source))

    output = build_inventory_agent_output(source)

    save_output(output)

    print("\nInventory Agent completed.")
    print(f"Total inventory records: {len(output)}")
    print(f"Output saved to: {OUTPUT_FILE}")

    print("\nAgent Action Distribution:")
    print(output["Agent_Action"].value_counts())

    print("\nAgent Priority Distribution:")
    print(output["Agent_Priority"].value_counts())

    print("\nCritical Inventory Items:")
    print(
        output[
            output["Agent_Action"] == "URGENT_REORDER"
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


if __name__ == "__main__":
    main()
