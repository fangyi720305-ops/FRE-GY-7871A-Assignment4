# Milestone 4 — cached returns and session-aligned sentiment

Run in PowerShell from `D:\School Work\FRE-GY 7871 NLP\Assignment 4`:

```powershell
& 'C:\Users\fangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\src\milestone4.py
& 'C:\Users\fangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\src\verify_m4.py
```

This script uses only cached market_panel.csv, scored_records.jsonl, the 448-ID sensitivity corpus and saved coverage audits. It does not import or run Milestone 3 scoring, collect data, access credentials, or call inference APIs. Project-local statsmodels/scipy/patsy provide the regression cross-check; versions are recorded in outputs/milestone4_summary.json. Existing NumPy/pandas/matplotlib are reused.

Specification and hash: milestone4_spec.json and outputs/milestone4_spec_sha256.txt. The script refuses a changed spec hash. Do not add lags or variants based on p-values. Full input hashes are checked before/after running in milestone4_integrity.json.

Data: data/processed/individual_returns.csv, return_panel.csv, aligned_sentiment_sessions.csv and analysis_session_grid.csv. Return panel includes September 4 baseline, individual/company/basket/SPY/spread simple returns and compounded performance. Synthetic compounded spread is separately labeled; cumulative basket-minus-SPY performance difference is also saved. The 17-row analysis grid retains the unavailable September 8 sentiment and all session indices.

Audits: outputs/sentiment_window_audit.csv, record_session_assignment.csv, excluded_records_market_analysis.csv, x_time_sampling.csv and regression_design_audit.csv. Dates, boundary inclusion, original timestamps and no-future-text checks are explicit. Complete collection means every intersected Eastern calendar date completed the frozen source protocol, with capped X sampling and 19/20 shortfalls flagged; it does not mean exhaustive historical coverage. Empty sample windows retain missing means.

Results: outputs/return_summary.json, descriptive_correlations.csv, granger_exploratory_tests.csv, granger_test_details.json, milestone4_summary.json and milestone4_findings.md. Coefficients use decimal return per unit of compound change. Joint F tests compare nested models with identical usable dates. P-values are conventional and unadjusted; no out-of-sample validation or stationarity claim.

Figures: outputs/m4_cumulative_returns.png/svg and m4_aligned_sentiment.png/svg. Year remains provisional; X is a bounded search sample; measures have weak validation. Ready for cautious Milestone 5 drafting, subject to assignment/year confirmation. Stop before final report writing.
