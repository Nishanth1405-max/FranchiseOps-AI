# FranchiseOps AI — Integrated Milestone 1 Dashboard

This Streamlit dashboard integrates the four supplied team feature branches while preserving the existing dashboard theme, navigation, five-tab layout, charts, KPI cards, filters, and downloads.

## Integrated team modules

| Team module | Integrated source | Dashboard use |
| --- | --- | --- |
| Sales & Outlet Data | Raw Excel workbook and cleaning notebook | 30,000 validated outlet-month records, trends, filters, and operating KPIs |
| Outlet Benchmarking | `benchmarking/benchmark_output.csv` and reusable Python module | KPI benchmark score, category, rank, and peer comparisons |
| Performance Score | `performance_score/performance_score_output.csv` and reusable Python module | Seven-driver score, health category, global rank, and score-driver chart |
| Outlet Performance Agent | `src/outlet_performance_agent/outlet_agent.py` | Explainable findings, issue tags, severity, and recommendations |
| Performance Dashboard | `app.py` | Overview, Benchmarking, Outlet Analysis, Agent Insights, and Methodology & Quality |

The integration validates that the supplied score output can be reproduced from the supplied benchmarking output before displaying it.

## Data quality result

- 30,120 raw rows loaded from the `Raw_Outlet_Data` worksheet
- 120 duplicated operating rows removed
- 2,288 missing numeric values median-imputed according to the sales-data notebook
- 30,000 clean rows covering 750 outlets and 40 months
- No remaining required-field gaps, duplicate outlet-month rows, or identity conflicts

## Performance score

| Driver | Weight |
| --- | ---: |
| Sales rank | 20% |
| Profit rank | 20% |
| Profit-margin rank | 15% |
| Conversion-rate rank | 15% |
| Average-order-value rank | 10% |
| Customer-satisfaction rank | 10% |
| Complaint-control rank | 10% |

Health categories are Excellent (80–100), Good (65–79.99), Needs Improvement (50–64.99), and Critical (below 50).

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The application opens at `http://localhost:8501`.

## Regenerate team outputs

```bash
python -m benchmarking.benchmarking
python -m performance_score.performance_score
python scripts/build_processed_data.py
```

## Run tests

```bash
pytest -q
```

## Project structure

```text
FranchiseOps-AI-performance-dashboard/
├── app.py
├── benchmarking/
│   ├── benchmarking.py
│   ├── benchmark_output.csv
│   └── outlet_kpis.csv
├── performance_score/
│   ├── performance_score.py
│   └── performance_score_output.csv
├── data/
│   ├── raw/FranchiseOps_AI_Milestone1_Member1_Large_Raw_Dataset.xlsx
│   └── processed/outlet_performance_intelligence.csv
├── src/
│   ├── analytics.py
│   ├── data_loader.py
│   ├── outlet_performance_agent/outlet_agent.py
│   └── sales_outlet_data/franchiseOpsAi.ipynb
├── scripts/build_processed_data.py
├── tests/
└── requirements.txt
```
