from pathlib import Path

import numpy as np

from src.analytics import SCORE_WEIGHTS, calculate_performance_metrics, rerank_snapshot
from src.data_loader import load_outlet_data


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "raw" / "FranchiseOps_AI_Milestone1_Member1_Large_Raw_Dataset.xlsx"


def _processed():
    source, _ = load_outlet_data(DATA_PATH)
    return calculate_performance_metrics(source)


def test_grouped_score_weights_sum_to_one():
    assert np.isclose(sum(SCORE_WEIGHTS.values()), 1.0)


def test_supplied_scores_and_agent_outputs_are_complete():
    data = _processed()
    assert data["performance_score"].between(0, 100).all()
    assert data[["health_category", "alert_level", "insight", "recommendation"]].notna().all().all()


def test_global_performance_ranks_cover_every_outlet():
    data = _processed().drop_duplicates("outlet_id")
    assert len(data) == 750
    assert data["performance_rank"].between(1, 750).all()
    ordered = data.sort_values(["performance_score", "performance_rank"], ascending=[False, True])
    assert ordered["performance_rank"].is_monotonic_increasing


def test_monthly_benchmark_equals_peer_mean():
    data = _processed()
    for _, group in data.groupby("date"):
        assert np.allclose(group["benchmark_revenue"], group["revenue"].mean())


def test_health_thresholds_match_performance_score_module():
    data = _processed().drop_duplicates("outlet_id")
    assert (data.loc[data["performance_score"] >= 80, "health_category"] == "Excellent").all()
    assert (data.loc[data["performance_score"] < 50, "health_category"] == "Critical").all()
    assert (data.loc[data["health_category"] == "Critical", "alert_level"] == "High").all()


def test_filtered_peer_ranking_is_contiguous():
    data = _processed()
    snapshot = data[(data["date"] == data["date"].max()) & (data["region"] == "West")]
    ranked = rerank_snapshot(snapshot)
    assert len(ranked) == 200
    assert ranked["peer_rank"].tolist() == list(range(1, 201))
