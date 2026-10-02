# Assignment 4 — Milestone 1 access pilot

Windows PowerShell, from this project folder:

```powershell
py -3 src\pilot.py --year 2026 --provisional
```

The script uses Python's standard library. If `py` is unavailable, use a Python 3.10+ executable (with zoneinfo/tzdata support on Windows). On this machine the tested executable is:

```powershell
& 'C:\Users\fangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\src\pilot.py --year 2026 --provisional
```

Keep `--provisional` until assignment materials confirm the year; changing the year does not verify it. `.env` is preserved and excluded from Git. Actual Guardian variable: `GUARDIAN_API_KEY`. Recognized optional X variables: `X_BEARER_TOKEN`, `TWITTER_BEARER_TOKEN`, `X_API_BEARER_TOKEN`. Existing process environment takes precedence. The script never logs request URLs or exception messages, caches successful Guardian JSON without keys, and uses at most two retries. A Retry-After over 60 seconds stops that route without violating the delay.

Files: raw API responses in data/raw; unscored Guardian article records, X schema-only CSV when unavailable, and small price CSV in data/processed; audit at project root; summary in outputs. Broad Guardian records include false positives deliberately flagged for review. No scoring or final report is generated. Re-running uses Guardian caches but refreshes market and credential-enabled X requests; X can incur provider charges if credentials are added. Market raw responses span a short September window to verify preceding close and trading-calendar availability; the cleaned pilot keeps four dates per symbol.

Read source_access_audit.csv, analysis_plan.md, and outputs/access_notes.md before Milestone 2. Guardian caches use the API's calendar date filters; final source/timezone alignment must be explicit.

Social dependency audit: social_access_audit.csv; outputs/social_dependency_status.md; outputs/social_daily_coverage.csv. Partial originals are in data/processed/social_discovery_examples.csv and must not be scored. Do not rerun failed probes without changed access conditions.

## Milestone 2 complete
Use MILESTONE2_README.md for collection/validation commands and frozen sampling rules. Clean datasets: data/processed/guardian_clean.csv (186), x_clean.csv/jsonl (458), market_panel.csv (108). All 23 X days have observations; Sep 14 and 16 have 19 posts, other days 20. Exact-text sensitivity corpus contains 448 records. Coverage and validation audits are in outputs; summary is outputs/milestone2_summary.json. Year 2026 remains provisional. No sentiment, returns, Granger tests or final report were produced.

## Milestone 3 completed
Local VADER scoring and transparent multi-label framing completed for 186 Guardian and 458 X records across all 23 Eastern calendar dates. Fixed 40-record Codex review: general sentiment agreement 50% Guardian, 75% X; final exact framing agreement 60%/65%. No independent human validation. One safety-phrase variant correction applied, remaining errors retained as limitations. Scores are text sentiment in AI-related material, not validated AI-specific attitudes. The 448-record X exact-text sensitivity and equal-channel daily combined series are saved. Read MILESTONE3_README.md and outputs/milestone3_limitations.md for commands, outputs and caveats. Year remains provisional; X is a bounded search sample. Ready for exploratory Milestone 4 only after timing/lag rules are frozen. No market returns, Granger tests or final report were produced. Earlier milestone notes above describe historical states.

## Milestone 4 completed
Cached adjusted returns and timestamp-aligned sentiment completed under frozen milestone4_spec.json. Basket cumulative return 3.56%; SPY -0.74%. Primary one-lag change model: n=14, coefficient=0.0188726, F=0.820487, unadjusted p=0.384449. Six planned tests and manual/statsmodels cross-checks saved; full session grid retained. September 8 sentiment is unavailable due to uncollected September 4–7; text after final close excluded. Read MILESTONE4_README.md and outputs/milestone4_findings.md. Generic text sentiment, weak validation, bounded X sampling, unadjusted exploratory comparisons and provisional 2026 remain material caveats. Ready for cautious Milestone 5 drafting with assignment/year verification unresolved; no final report written.
