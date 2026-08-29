"""Load and integrate every Milestone 1 team output for the dashboard."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from performance_score.performance_score import calculate_performance_scores


RAW_COLUMNS = [
    "Record_ID",
    "Outlet_ID",
    "Outlet_Name",
    "Outlet_Type",
    "City",
    "State",
    "Region",
    "Month",
    "Footfall",
    "Orders",
    "Conversion_Rate_%",
    "Average_Order_Value_INR",
    "Sales_Revenue_INR",
    "COGS_INR",
    "Operating_Cost_INR",
    "Marketing_Spend_INR",
    "Profit_INR",
    "Profit_Margin_%",
    "Employees",
    "Employee_Turnover_%",
    "Customer_Satisfaction_1_5",
    "Complaints",
]

IMPUTE_COLUMNS = [
    "Footfall",
    "Orders",
    "Conversion_Rate_%",
    "Average_Order_Value_INR",
    "Marketing_Spend_INR",
    "Employee_Turnover_%",
    "Customer_Satisfaction_1_5",
    "Complaints",
]

BASE_COLUMNS = [
    "date",
    "outlet_id",
    "outlet_name",
    "city",
    "region",
    "revenue",
    "profit",
    "profit_margin",
    "orders",
    "footfall",
    "conversion_rate",
    "avg_order_value",
    "customer_rating",
    "complaints",
    "employee_turnover",
    "benchmark_score",
    "benchmark_rank",
    "benchmark_category",
    "performance_score",
    "performance_rank",
    "health_category",
]

NUMERIC_COLUMNS = [
    "revenue",
    "profit",
    "profit_margin",
    "orders",
    "footfall",
    "conversion_rate",
    "avg_order_value",
    "customer_rating",
    "complaints",
    "employee_turnover",
    "benchmark_score",
    "benchmark_rank",
    "performance_score",
    "performance_rank",
]


class DataValidationError(ValueError):
    """Raised when the team outputs cannot be safely integrated."""


@dataclass(frozen=True)
class DataQualityReport:
    source_rows: int
    rows: int
    outlets: int
    months: int
    imputed_cells: int
    duplicates_removed: int
    missing_cells: int
    duplicate_outlet_months: int
    identity_conflicts: int
    aov_reconciliation_max_error_pct: float
    status: str

    def to_dict(self) -> dict[str, int | float | str]:
        return asdict(self)


def _read_raw_workbook(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Sales and outlet workbook not found: {path}")
    try:
        source = pd.read_excel(path, sheet_name="Raw_Outlet_Data")
    except ValueError as exc:
        raise DataValidationError("Workbook sheet 'Raw_Outlet_Data' is missing") from exc

    missing = sorted(set(RAW_COLUMNS) - set(source.columns))
    if missing:
        raise DataValidationError(f"Raw workbook is missing columns: {', '.join(missing)}")
    return source[RAW_COLUMNS].copy()


def _clean_sales_data(source: pd.DataFrame) -> tuple[pd.DataFrame, int, int, float]:
    """Apply the Sales & Outlet Data notebook's cleaning decisions."""
    df = source.copy()
    source_rows = len(df)

    valid_aov = (
        df["Orders"].notna()
        & df["Average_Order_Value_INR"].notna()
        & df["Sales_Revenue_INR"].notna()
        & df["Sales_Revenue_INR"].ne(0)
    )
    aov_error = (
        (
            df.loc[valid_aov, "Sales_Revenue_INR"]
            - df.loc[valid_aov, "Orders"]
            * df.loc[valid_aov, "Average_Order_Value_INR"]
        ).abs()
        / df.loc[valid_aov, "Sales_Revenue_INR"].abs()
        * 100
    )

    imputed_cells = int(df[IMPUTE_COLUMNS].isna().sum().sum())
    for column in IMPUTE_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")
        df[column] = df[column].fillna(df[column].median())

    # Record_ID is unique even for the 120 duplicated operating records.
    duplicate_subset = [column for column in RAW_COLUMNS if column != "Record_ID"]
    df = df.drop_duplicates(subset=duplicate_subset, keep="first")
    duplicates_removed = source_rows - len(df)

    df["Month"] = pd.to_datetime(df["Month"].astype(str), format="%Y-%m", errors="coerce")
    return df, imputed_cells, duplicates_removed, round(float(aov_error.max()), 4)


def _load_feature_outputs(project_root: Path) -> pd.DataFrame:
    benchmark_path = project_root / "benchmarking" / "benchmark_output.csv"
    performance_path = project_root / "performance_score" / "performance_score_output.csv"
    for path in [benchmark_path, performance_path]:
        if not path.exists():
            raise FileNotFoundError(f"Required team output not found: {path}")

    benchmark = pd.read_csv(benchmark_path)
    supplied_scores = pd.read_csv(performance_path)
    calculated_scores = calculate_performance_scores(benchmark, include_components=True)

    expected = supplied_scores.sort_values("Outlet_ID").reset_index(drop=True)
    actual = calculated_scores[
        [
            "Outlet_ID",
            "Outlet_Name",
            "Benchmark_Score",
            "Benchmark_Rank",
            "Benchmark_Category",
            "Performance_Score",
            "Performance_Rank",
            "Performance_Category",
        ]
    ].sort_values("Outlet_ID").reset_index(drop=True)

    if len(expected) != len(actual) or not expected["Outlet_ID"].equals(actual["Outlet_ID"]):
        raise DataValidationError("Benchmarking and performance-score outputs cover different outlets")
    if not np.allclose(expected["Performance_Score"], actual["Performance_Score"], atol=0.01):
        raise DataValidationError("Performance-score output does not match the supplied benchmarking output")
    if not expected["Performance_Category"].equals(actual["Performance_Category"]):
        raise DataValidationError("Performance health categories are inconsistent")

    return calculated_scores


def _normalise_columns(cleaned: pd.DataFrame, feature_outputs: pd.DataFrame) -> pd.DataFrame:
    df = cleaned.rename(
        columns={
            "Month": "date",
            "Outlet_ID": "outlet_id",
            "Outlet_Name": "outlet_name",
            "Outlet_Type": "outlet_type",
            "City": "city",
            "State": "state",
            "Region": "region",
            "Footfall": "footfall",
            "Orders": "orders",
            "Conversion_Rate_%": "conversion_rate",
            "Average_Order_Value_INR": "avg_order_value",
            "Sales_Revenue_INR": "revenue",
            "COGS_INR": "cogs",
            "Operating_Cost_INR": "operating_cost",
            "Marketing_Spend_INR": "marketing_spend",
            "Profit_INR": "profit",
            "Profit_Margin_%": "profit_margin",
            "Employees": "employees",
            "Employee_Turnover_%": "employee_turnover",
            "Customer_Satisfaction_1_5": "customer_rating",
            "Complaints": "complaints",
        }
    ).drop(columns=["Record_ID"])

    score_columns = feature_outputs.rename(
        columns={
            "Outlet_ID": "outlet_id",
            "Benchmark_Score": "benchmark_score",
            "Benchmark_Rank": "benchmark_rank",
            "Benchmark_Category": "benchmark_category",
            "Performance_Score": "performance_score",
            "Performance_Rank": "performance_rank",
            "Performance_Category": "health_category",
            "Sales_Score": "sales_component_score",
            "Profit_Score": "profit_component_score",
            "Margin_Score": "margin_component_score",
            "Conversion_Score": "conversion_component_score",
            "AOV_Score": "aov_component_score",
            "Satisfaction_Score": "satisfaction_component_score",
            "Complaint_Score": "complaint_component_score",
        }
    )
    score_columns = score_columns[
        [
            "outlet_id",
            "benchmark_score",
            "benchmark_rank",
            "benchmark_category",
            "performance_score",
            "performance_rank",
            "health_category",
            "sales_component_score",
            "profit_component_score",
            "margin_component_score",
            "conversion_component_score",
            "aov_component_score",
            "satisfaction_component_score",
            "complaint_component_score",
        ]
    ]
    df = df.merge(score_columns, on="outlet_id", how="left", validate="many_to_one")

    df = df.sort_values(["outlet_id", "date"]).reset_index(drop=True)
    df["previous_month_revenue"] = df.groupby("outlet_id")["revenue"].shift(1)
    df["previous_month_revenue"] = df["previous_month_revenue"].fillna(df["revenue"])
    df["benchmark_revenue"] = df.groupby("date")["revenue"].transform("mean")
    df["target_revenue"] = df["benchmark_revenue"]
    df["complaint_rate"] = np.where(df["orders"] > 0, df["complaints"] / df["orders"] * 100, 0)
    return df


def build_quality_report(
    df: pd.DataFrame,
    *,
    source_rows: int | None = None,
    imputed_cells: int = 0,
    duplicates_removed: int = 0,
    aov_error: float | None = None,
) -> DataQualityReport:
    identity_counts = df.groupby("outlet_id")[["outlet_name", "city", "region"]].nunique()
    identity_conflicts = int((identity_counts > 1).any(axis=1).sum())
    missing_cells = int(df[BASE_COLUMNS].isna().sum().sum())
    duplicate_outlet_months = int(df.duplicated(["date", "outlet_id"]).sum())

    if aov_error is None:
        expected_revenue = df["orders"] * df["avg_order_value"]
        denominator = df["revenue"].abs().replace(0, np.nan)
        reconciliation = ((df["revenue"] - expected_revenue).abs() / denominator * 100).dropna()
        aov_error = round(float(reconciliation.max()), 4) if not reconciliation.empty else 0.0

    status = (
        "Passed"
        if missing_cells == 0 and duplicate_outlet_months == 0 and identity_conflicts == 0
        else "Review"
    )
    return DataQualityReport(
        source_rows=source_rows if source_rows is not None else len(df),
        rows=len(df),
        outlets=int(df["outlet_id"].nunique()),
        months=int(df["date"].nunique()),
        imputed_cells=imputed_cells,
        duplicates_removed=duplicates_removed,
        missing_cells=missing_cells,
        duplicate_outlet_months=duplicate_outlet_months,
        identity_conflicts=identity_conflicts,
        aov_reconciliation_max_error_pct=aov_error,
        status=status,
    )


def validate_outlet_data(df: pd.DataFrame) -> DataQualityReport:
    issues: list[str] = []
    missing_columns = sorted(set(BASE_COLUMNS) - set(df.columns))
    if missing_columns:
        raise DataValidationError(f"Missing required columns: {', '.join(missing_columns)}")
    if df[BASE_COLUMNS].isna().any().any():
        issues.append("required fields contain missing values")
    if df.duplicated(["date", "outlet_id"]).any():
        issues.append("duplicate outlet-month records were found")
    if (df["revenue"] < 0).any() or (df["orders"] < 0).any():
        issues.append("revenue and orders cannot be negative")
    if not df["customer_rating"].between(1, 5).all():
        issues.append("customer ratings must be between 1 and 5")
    if not df["conversion_rate"].between(0, 100).all():
        issues.append("conversion rates must be between 0 and 100")
    if not df["performance_score"].between(0, 100).all():
        issues.append("performance scores must be between 0 and 100")

    report = build_quality_report(df)
    if report.identity_conflicts:
        issues.append("an outlet ID maps to conflicting names, cities, or regions")
    if issues:
        raise DataValidationError("; ".join(issues))
    return report


def load_outlet_data(path: str | Path) -> tuple[pd.DataFrame, DataQualityReport]:
    """Return cleaned monthly records enriched by all teammate feature outputs."""
    source_path = Path(path)
    project_root = source_path.parents[2]
    source = _read_raw_workbook(source_path)
    cleaned, imputed_cells, duplicates_removed, aov_error = _clean_sales_data(source)
    feature_outputs = _load_feature_outputs(project_root)
    integrated = _normalise_columns(cleaned, feature_outputs)

    base_report = validate_outlet_data(integrated)
    report = build_quality_report(
        integrated,
        source_rows=len(source),
        imputed_cells=imputed_cells,
        duplicates_removed=duplicates_removed,
        aov_error=aov_error,
    )
    if base_report.status != "Passed" or report.status != "Passed":
        raise DataValidationError("Integrated outlet data failed quality checks")
    return integrated.sort_values(["date", "outlet_id"]).reset_index(drop=True), report
