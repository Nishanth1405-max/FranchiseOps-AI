from pathlib import Path

import pandas as pd
import pytest

from benchmarking.benchmarking import build_outlet_kpis, calculate_benchmarks
from src.data_loader import DataValidationError, load_outlet_data, validate_outlet_data


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "raw" / "FranchiseOps_AI_Milestone1_Member1_Large_Raw_Dataset.xlsx"


def test_all_team_outputs_integrate_and_pass_quality_checks():
    data, report = load_outlet_data(DATA_PATH)
    assert len(data) == 30_000
    assert report.source_rows == 30_120
    assert report.outlets == 750
    assert report.months == 40
    assert report.imputed_cells == 2_288
    assert report.duplicates_removed == 120
    assert report.missing_cells == 0
    assert report.duplicate_outlet_months == 0
    assert report.identity_conflicts == 0
    assert report.aov_reconciliation_max_error_pct < 0.01
    assert report.status == "Passed"
    assert data["benchmark_score"].notna().all()
    assert data["performance_score"].notna().all()


def test_benchmarking_module_reproduces_supplied_feature_output():
    raw = pd.read_excel(DATA_PATH, sheet_name="Raw_Outlet_Data")
    calculated = calculate_benchmarks(build_outlet_kpis(raw)).sort_values("Outlet_ID")
    supplied = pd.read_csv(ROOT / "benchmarking" / "benchmark_output.csv").sort_values("Outlet_ID")
    assert calculated["Outlet_ID"].tolist() == supplied["Outlet_ID"].tolist()
    assert calculated["Benchmark_Score"].tolist() == supplied["Benchmark_Score"].tolist()
    assert calculated["Benchmark_Category"].tolist() == supplied["Benchmark_Category"].tolist()


def test_duplicate_outlet_month_is_rejected():
    data, _ = load_outlet_data(DATA_PATH)
    duplicated = pd.concat([data, data.iloc[[0]]], ignore_index=True)
    with pytest.raises(DataValidationError, match="duplicate"):
        validate_outlet_data(duplicated)


def test_invalid_customer_rating_is_rejected():
    data, _ = load_outlet_data(DATA_PATH)
    data.loc[0, "customer_rating"] = 5.5
    with pytest.raises(DataValidationError, match="ratings"):
        validate_outlet_data(data)
