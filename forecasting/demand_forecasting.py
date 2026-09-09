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

SERIES_COLUMNS = [
    "Outlet_ID",
    "SKU_ID",
]

DUPLICATE_KEY_COLUMNS = SERIES_COLUMNS + ["Month"]

REQUIRED_COLUMNS = [
    "Outlet_ID",
    "SKU_ID",
    "Month",
    "Inventory_Units_Sold",
]


# --------------------------------------------------
# Load Inventory Data
# --------------------------------------------------

def load_inventory_data() -> pd.DataFrame:
    """Load inventory data from the raw Excel dataset."""

    return pd.read_excel(
        INPUT_FILE,
        sheet_name="Raw_Outlet_Data",
        usecols=REQUIRED_COLUMNS,
    )


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

    if df["Outlet_ID"].isna().any():
        raise ValueError("Outlet_ID contains missing values.")

    if df["SKU_ID"].isna().any():
        raise ValueError("SKU_ID contains missing values.")

    if df["Month"].isna().any():
        raise ValueError("Month contains missing values.")

    if df["Inventory_Units_Sold"].isna().any():
        raise ValueError(
            "Inventory_Units_Sold contains missing values."
        )


# --------------------------------------------------
# Clean Data
# --------------------------------------------------

def clean_inventory_data(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, int]:
    """
    Convert Month to datetime and remove duplicate
    Outlet_ID + SKU_ID + Month records.
    """

    df = df.copy()

    df["Month"] = pd.to_datetime(
        df["Month"].astype(str),
        format="%Y-%m",
    )

    duplicate_count = int(
        df.duplicated(
            DUPLICATE_KEY_COLUMNS,
            keep="first",
        ).sum()
    )

    df = (
        df.drop_duplicates(
            subset=DUPLICATE_KEY_COLUMNS,
            keep="first",
        )
        .sort_values(DUPLICATE_KEY_COLUMNS)
        .reset_index(drop=True)
    )

    return df, duplicate_count


# --------------------------------------------------
# Forecasting Logic
# --------------------------------------------------

def calculate_forecast(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate next-month demand using a 3-month
    historical moving average.

    Each forecast is calculated separately for each
    Outlet_ID + SKU_ID series.
    """

    df = df.copy()

    df = df.sort_values(
        SERIES_COLUMNS + ["Month"]
    )

    df["Demand_Forecast_Next_Month_Units"] = (
        df.groupby(SERIES_COLUMNS)["Inventory_Units_Sold"]
        .transform(
            lambda series: (
                series.shift(1)
                .rolling(
                    window=FORECAST_WINDOW,
                    min_periods=FORECAST_WINDOW,
                )
                .mean()
            )
        )
    )

    df["Demand_Forecast_Next_Month_Units"] = (
        df["Demand_Forecast_Next_Month_Units"]
        .round(2)
    )

    return df


# --------------------------------------------------
# Select Latest Forecast
# --------------------------------------------------

def get_latest_forecast(df: pd.DataFrame) -> pd.DataFrame:
    """Return the latest available forecast for every outlet-SKU."""

    latest_month = df["Month"].max()

    return df[
        df["Month"] == latest_month
    ].copy()


# --------------------------------------------------
# Save Forecast
# --------------------------------------------------

def save_forecast(df: pd.DataFrame) -> None:
    """Save all historical forecast results to CSV."""

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

    # 3. Clean duplicate outlet-SKU-month records
    clean_df, duplicate_count = clean_inventory_data(df)

    print(f"Duplicate records removed: {duplicate_count:,}")
    print(
        f"Records used for forecasting: "
        f"{len(clean_df):,}"
    )

    # 4. Calculate outlet-level forecasts
    forecast_df = calculate_forecast(clean_df)

    # 5. Get the latest forecast for every outlet-SKU
    latest_forecast = get_latest_forecast(forecast_df)

    # 6. Save all forecast results
    save_forecast(forecast_df)

    print("\nForecasting completed.")

    print(
        f"Latest historical month: "
        f"{latest_forecast['Month'].max():%Y-%m}"
    )

    print(
        f"Outlet-SKU series forecasted: "
        f"{latest_forecast.groupby(SERIES_COLUMNS).ngroups:,}"
    )

    print(
        f"Forecast output saved to: "
        f"{OUTPUT_FILE}"
    )

    print("\nSample latest forecasts:")

    print(
        latest_forecast[
            [
                "Outlet_ID",
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