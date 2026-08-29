# FranchiseOps AI - Milestone 1

An interactive Outlet Performance Intelligence dashboard for multi-location franchise operations. It implements the first milestone from the supplied project reference: data integration, outlet benchmarking, performance scoring, agent-style insights, and dashboard reporting.

## What is included

- Validated sales and outlet data for 12 outlets across 8 months
- Transparent five-component performance score
- Deterministic monthly outlet rankings with tie-break rules
- Health categories and severity-based alerts
- Executive overview, benchmarking, outlet drill-down, and action centre
- Rule-based Outlet Performance Agent recommendations
- Downloadable benchmark and agent-insight reports
- Automated analytics, data-quality, and application smoke tests

## Performance score

| Component | Weight | Calculation |
| --- | ---: | --- |
| Revenue target achievement | 35% | `revenue / target_revenue`, capped at 100 |
| Month-over-month growth | 15% | -20% maps to 0, 0% maps to 50, +20% maps to 100 |
| Customer rating | 20% | Rating converted from a 5-point scale to 100 |
| Complaint control | 15% | `100 - complaint_rate * 10`, bounded to 0-100 |
| On-time service | 15% | Existing percentage, bounded to 0-100 |

Health categories: Excellent (85-100), Good (70-84.9), Needs Improvement (55-69.9), and Critical (below 55).

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The application opens at `http://localhost:8501`.

## Build the processed dataset

```bash
python scripts/build_processed_data.py
```

This writes the recalculated scores, rankings, alerts, insights, and recommendations to `data/processed/outlet_performance_intelligence.csv`.

## Run tests

```bash
pytest -q
```

## Project structure

```text
FranchiseOps-AI-main/
├── app.py
├── data/
│   ├── raw/franchiseops_filtered_outlet_data.csv
│   └── processed/outlet_performance_intelligence.csv
├── docs/MILESTONE1_HANDOFF.md
├── scripts/build_processed_data.py
├── src/
│   ├── analytics.py
│   └── data_loader.py
├── tests/
│   ├── test_analytics.py
│   ├── test_app.py
│   └── test_data_loader.py
└── requirements.txt
```

## Data notes

The dashboard treats the uploaded revenue, target, orders, customer rating, complaint rate, and service values as source measures. Precomputed benchmark, score, rank, alert, insight, and recommendation columns in the uploaded CSV are recalculated so the displayed methodology stays internally consistent and auditable.
