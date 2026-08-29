# Milestone 1 Integration Handoff

## Completed integration

All supplied team work is connected to the existing Performance Dashboard without redesigning its UI/UX.

| Owner area | Integrated result |
| --- | --- |
| Sales & Outlet Data | Excel workbook, notebook, median imputation, duplicate removal, schema/range checks, monthly history |
| Outlet Benchmarking | Aggregate KPIs, six individual ranks, weighted benchmark score, benchmark rank, percentile category |
| Performance Score | Seven component scores, weighted overall score, health category, and performance rank |
| Outlet Performance Agent | Outlet assessment, operating issue detection, alert priority, explainable insight, and recommendation |
| Performance Dashboard | Existing five tabs and visual design connected to the complete 750-outlet dataset |
| Integration & Testing | Output consistency checks, data-quality tests, analytics tests, and Streamlit startup/filter tests |

## Important data-grain decision

The sales workbook contains monthly operating records. The supplied benchmarking and performance-score files contain one 40-month summary per outlet. The dashboard therefore uses:

- monthly records for dates, filters, revenue trends, ratings, complaints, conversion, and peer revenue comparison;
- supplied 40-month benchmark and performance outputs for official scores, global ranks, categories, and score drivers;
- the selected month's operating values plus official scores for agent prioritization.

This keeps each teammate's intended output intact and avoids presenting a monthly calculation as the supplied global score.

## Demonstration flow

1. Open **Overview** to show network revenue, health mix, and the performance matrix.
2. Filter by region or outlets; rankings and all views update to the selected scope.
3. Open **Benchmarking** to inspect all selected outlets and download the report.
4. Open **Outlet Analysis** to show history, seven score drivers, and the agent assessment.
5. Open **Agent Insights** to review the top 50 prioritized cards and download the complete queue.
6. Open **Methodology & Quality** to explain weights, thresholds, 2,288 imputations, 120 duplicate removals, and validation status.

## Verified integrated state

- 30,120 source rows
- 30,000 cleaned outlet-month rows
- 750 outlets
- 40 months (January 2023 through April 2026)
- 2,288 imputed numeric cells
- 120 duplicate operating rows removed
- 0 missing required values after cleaning
- 0 duplicate outlet-month rows after cleaning
- 0 outlet identity conflicts
- Supplied performance scores reproduced from supplied benchmark output to 0.01 tolerance

Run `pytest -q` before the final demonstration.
