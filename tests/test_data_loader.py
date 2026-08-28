from pathlib import Path

import pandas as pd
import pytest

from src.data_loader import DataValidationError, load_outlet_data, validate_outlet_data


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "raw" / "franchiseops_filtered_outlet_data.csv"


def test_source_data_passes_quality_checks():
    data, report = load_outlet_data(DATA_PATH)
    assert len(data) == 96
    assert report.outlets == 12
    assert report.months == 8
    assert report.missing_cells == 0
    assert report.duplicate_outlet_months == 0
    assert report.identity_conflicts == 0
    assert report.aov_reconciliation_max_error_pct < 0.01
    assert report.status == "Passed"


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
