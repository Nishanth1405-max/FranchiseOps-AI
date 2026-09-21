# FranchiseOps AI - Milestones 1, 2 & 3

An interactive Outlet Performance Intelligence dashboard for multi-location franchise operations. It keeps the original Milestone 1 visual design, adds Staff, Marketing, Inventory, and Demand Forecasting views for Milestone 2, and adds Workforce, Marketing Effectiveness, Data Preparation, and Operational Insights for Milestone 3.

## What is included

- Milestone 1 sales and outlet performance dashboard
- Outlet benchmarking, performance scoring, rankings, health categories, and alerts
- Rule-based Outlet Performance Agent insights and recommendations
- Staff Agent analysis for 750 outlets
- Marketing Agent analysis for 750 outlets
- Inventory Agent analysis for 30,000 unique outlet/SKU/month records
- Three-month moving-average demand forecasting for 750 outlet/SKU combinations
- Validated shared coverage across all 750 Milestone 2 outlet IDs
- Milestone 3 data preparation for 30,000 unique outlet/SKU/month records
- Workforce performance, attendance, productivity, and scheduling analysis for 750 outlets
- Marketing effectiveness, campaign ROI, reach, conversion, and engagement analysis for 750 outlets
- Cross-functional Operational Insights with a single prioritized action queue
- Existing dark dashboard theme, card design, charts, tables, filters, and downloads
- Automated analytics, data-quality, agent, and Streamlit application tests

## Project flow

```text
Milestone 1 data
  → validation → benchmarking → performance score → outlet insights

Milestone 2 data
  → Staff Agent → staff status + insight + recommendation
  → Marketing Agent → category + alert + insight + recommendation
  → Inventory Agent → stock action + priority + replenishment
  → Demand Forecasting → previous-three-month moving-average estimate

All active outputs
  → validated loaders → one Streamlit decision dashboard

Milestone 3 combined data
  → validation + duplicate removal
  → Workforce Intelligence + Marketing Effectiveness
  → Workforce + Marketing + Inventory
  → Operational health score + primary focus + recommended action
```

## Milestone 3 modules

| Module | Main input | Main output | Why it is included |
| --- | --- | --- | --- |
| Data Preparation | Combined Milestone 2/3 workbook | Validated 30,000-row analytical dataset and quality report | Prevents duplicate or invalid records from changing scores and decisions |
| Staff Workforce | Productivity, attendance, staff score, schedule status | Workforce category, alert, insight, recommendation, monthly summary | Explains whether an outlet has a people-performance or scheduling issue |
| Marketing Effectiveness | Spend, sales, orders, conversion, reach, campaign conversions, ROI | Effectiveness score, campaign category, insight, recommendation | Connects marketing cost with campaign results and customer response |
| Operational Insights | Workforce, marketing, and latest inventory outputs | Operational health score, priority, weakest area, action | Gives managers one cross-functional action queue instead of separate reports |

## Active Milestone 2 agents

| Agent | Owner | Main input | Main output |
| --- | --- | --- | --- |
| Staff Agent | Nandini | Employees, turnover, satisfaction, complaints | Staff status, insight, recommendation |
| Marketing Agent | RajaShri | Marketing spend, revenue, orders, conversion | Efficiency, category, alert, insight, recommendation |
| Inventory Agent | Nirma | Stock, reorder, freshness, and wastage data | Action, priority, explanation, replenishment quantity |
| Inventory Forecasting | Nirma | Monthly SKU units sold | Three-month moving-average demand forecast |
| Performance Dashboard | Narayanadas | Milestone 1 results plus all four Milestone 2 outputs | Interactive analysis and downloadable reports |

The detailed implementation handoff is in `docs/MILESTONE2_DASHBOARD.md`.

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

## Streamlit Cloud deployment

The dashboard first loads `data/raw/franchiseops_filtered_outlet_data.csv`. If a deployment excludes `data/raw/`, it automatically falls back to `data/processed/outlet_performance_intelligence.csv`, which contains the same required source measures. Keep at least one of these files in the deployed GitHub branch.

After pushing changes, use **Reboot app** in Streamlit Cloud so it checks out the latest commit.

## Regenerate agent outputs

```bash
python staff_agent/staff_agent.py
python src/marketing_agent/marketing_agent.py
python inventory_agent/inventory_agent/inventory_agent.py
python forecasting/demand_forecasting.py
python scripts/build_milestone3_outputs.py
```

The first four commands use `data/raw/FranchiseOps_AI_Milestone2_Inventory_Dataset.xlsx`. The Milestone 3 command uses `data/raw/FranchiseOps_AI_Milestone2_Milestone3_Combined_Dataset.xlsx` and writes six validated CSV outputs used by the dashboard.

## Run tests

```bash
pytest -q
```

## Project structure

```text
FranchiseOps-AI/
├── app.py
├── staff_agent/
│   ├── staff_agent.py
│   └── staff_agent_output.csv
├── inventory_agent/inventory_agent/inventory_agent.py
├── forecasting/demand_forecasting.py
├── src/
│   ├── analytics.py
│   ├── data_loader.py
│   ├── milestone2_loader.py
│   ├── milestone3/
│   │   ├── data_preparation.py
│   │   ├── staff_workforce.py
│   │   ├── marketing_effectiveness.py
│   │   ├── operational_insights.py
│   │   └── loader.py
│   └── marketing_agent/marketing_agent.py
├── data/
│   ├── raw/
│   │   ├── franchiseops_filtered_outlet_data.csv
│   │   ├── FranchiseOps_AI_Milestone2_Inventory_Dataset.xlsx
│   │   └── FranchiseOps_AI_Milestone2_Milestone3_Combined_Dataset.xlsx
│   └── processed/
│       ├── marketing_agent_output.csv
│       ├── inventory_agent_output.csv
│       ├── demand_forecast_output.csv
│       └── m3_*.csv
├── docs/
│   ├── MILESTONE1_HANDOFF.md
│   ├── MILESTONE2_DASHBOARD.md
│   └── MILESTONE3_DASHBOARD.md
├── tests/
└── requirements.txt
```

## Data notes

The Milestone 3 source workbook contains 30,120 rows, including 120 deliberate duplicate outlet/SKU/month test rows. Preparation deterministically keeps the first record, producing 30,000 unique monthly rows. The prepared data contains 750 outlets, 40 months, 30,000 unique campaigns, no missing Milestone 3 fields, and a maximum engagement-rate reconciliation difference of 0.005 percentage points caused by two-decimal source rounding. The dashboard validates every schema, key, category, score, priority, and common outlet join before display.
