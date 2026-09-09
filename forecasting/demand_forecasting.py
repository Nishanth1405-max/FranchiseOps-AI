

# --------------------------------------------------
# FranchiseOps AI - Demand Forecasting
# Milestone 2 - Inventory Forecasting
# --------------------------------------------------

from pathlib import Path
import pandas as pd


# --------------------------------------------------
# Project Paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

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
    / "demand_forecast_output.csv"
)


# --------------------------------------------------
# Configuration
# --------------------------------------------------

FORECAST_WINDOW = 3

REQUIRED_COLUMNS = [
    "Outlet_ID",
    "SKU_ID",
    "Month",
    "Inventory_Units_Sold",
]


# --------------------------------------------------
# Load Data
# --------------------------------------------------

def load_inventory_data() -> pd.DataFrame:
    """Load inventory data from the raw Excel dataset."""

    df = pd.read_excel(
        INPUT_FILE,
        sheet_name="Raw_Outlet_Data",
        usecols=REQUIRED_COLUMNS,
    )

    return df


# --------------------------------------------------
# Validate Data
# --------------------------------------------------

def validate_data(df: pd.DataFrame) -> None:
    """Validate required columns and data quality."""

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if df.empty:
        raise ValueError("Inventory dataset is empty.")

    if df["SKU_ID"].isna().any():
        raise ValueError("SKU_ID contains missing values.")

    if df["Month"].isna().any():
        raise ValueError("Month contains missing values.")

    if df["Inventory_Units_Sold"].isna().any():
        raise ValueError(
            "Inventory_Units_Sold contains missing values."
        )


# --------------------------------------------------
# Forecasting Logic
# --------------------------------------------------

def calculate_forecast(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate next-month demand using a 3-month
    historical moving average.

    Forecast(t) =
        Average(
            Demand(t-1),
            Demand(t-2),
            Demand(t-3)
        )

    Forecast is calculated separately for each SKU.
    """

    df = df.copy()

    # Convert month into a proper datetime value
    df["Month"] = pd.to_datetime(
        df["Month"].astype(str),
        format="%Y-%m",
    )

    # Sort chronologically for every SKU
    df = df.sort_values(
        ["SKU_ID", "Month"]
    )

    # 3-month moving average of PREVIOUS demand
    df["Demand_Forecast_Next_Month_Units"] = (
        df.groupby("SKU_ID")["Inventory_Units_Sold"]
        .transform(
            lambda series:
            series.shift(1)
            .rolling(
                window=FORECAST_WINDOW,
                min_periods=FORECAST_WINDOW,
            )
            .mean()
        )
    )

    # Round forecast to 2 decimal places
    df["Demand_Forecast_Next_Month_Units"] = (
        df["Demand_Forecast_Next_Month_Units"]
        .round(2)
    )

    return df


# --------------------------------------------------
# Select Latest Forecast
# --------------------------------------------------

def get_latest_forecast(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return the most recent available record for each SKU.
    This represents the forecast that can be used for
    the next planning period.
    """

    latest_month = df["Month"].max()

    latest = df[
        df["Month"] == latest_month
    ].copy()

    return latest


# --------------------------------------------------
# Save Forecast
# --------------------------------------------------

def save_forecast(df: pd.DataFrame) -> None:
    """Save forecast results to CSV."""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_columns = [
        "Outlet_ID",
        "SKU_ID",
        "Month",
        "Inventory_Units_Sold",
        "Demand_Forecast_Next_Month_Units",
    ]

    df[output_columns].to_csv(
        OUTPUT_FILE,
        index=False,
    )


# --------------------------------------------------
# Main Forecasting Pipeline
# --------------------------------------------------

def main() -> None:

    print("Starting demand forecasting...")

    # 1. Load
    df = load_inventory_data()

    print(f"Loaded records: {len(df):,}")

    # 2. Validate
    validate_data(df)

    # 3. Calculate forecast
    forecast_df = calculate_forecast(df)

    # 4. Get latest forecast
    latest_forecast = get_latest_forecast(
        forecast_df
    )

    # 5. Save complete forecasting output
    save_forecast(forecast_df)

    print("\nForecasting completed.")
    print(
        f"Latest historical month: "
        f"{latest_forecast['Month'].max():%Y-%m}"
    )

    print(
        f"SKUs forecasted: "
        f"{latest_forecast['SKU_ID'].nunique():,}"
    )

    print(
        f"Forecast output saved to: "
        f"{OUTPUT_FILE}"
    )

    print("\nSample latest forecasts:")

    print(
        latest_forecast[
            [
                "SKU_ID",
                "Month",
                "Inventory_Units_Sold",
                "Demand_Forecast_Next_Month_Units",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )


# --------------------------------------------------
# Run
# --------------------------------------------------

if __name__ == "__main__":
    main()
