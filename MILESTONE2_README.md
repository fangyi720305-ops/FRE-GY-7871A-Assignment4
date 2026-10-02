# Milestone 2 — local collection and validation

Working window: September 8–30, 2026 inclusive in America/New_York. **Year remains provisional.** Collection rules were saved in `collection_rules.json` before collection, returns, or sentiment. Guardian remains the sole news source. X is a bounded Latest-search sample, not representative public opinion or complete archive coverage.

From this folder in Windows PowerShell (close ordinary Chrome using the dedicated profile first):

```powershell
& 'C:\Users\fangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' .\src\x_collect_m2.cjs
& 'C:\Users\fangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\src\collect_m2.py
& 'C:\Users\fangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\src\finish_m2.py
```

No per-post model/API inference, new collection library, paid API, sentiment, returns, Granger tests, or report generation runs. Shared X extraction/readiness/safety code is in `src/x_debug.cjs`. Login remains in the Git-ignored dedicated profile; `.env` is preserved. No authenticated HTML dumps or network logs are saved.

## Frozen sampling and resume

X query order contains the pilot's single neutral broad query: `("artificial intelligence" OR "generative AI" OR Anthropic) lang:en -filter:retweets`. Latest is checked. Target is 20 unique qualified posts per Eastern day, counting eligible pilot records. Maximum 100 unique inspected posts, 10 modest scrolls per query/day, 2.5-second scroll waits, and 10 original-post expansions per day. Stop at target or fixed effort limit. Actual publication timestamps determine dates; `since:DATE until:DATE` is an empirically useful retrieval aid in this session, not a universal endpoint assumption. Adjacent UTC dates are retained when they convert to the requested Eastern day.

Global ID deduplication, complete English enclosing text, matching enclosing author/status/time, and explicit AI discussion in enclosing text are required. Reposts, identifiable promoted/recommended items, unrelated matches and unresolved truncation are excluded. Quotes remain relationships, not independently counted observations. No sentiment-based selection. One unrelated pilot record was excluded and 29 reused. Exact text duplicates across distinct IDs are flagged, retained in the main ID-based sample, and removed only in a separate sensitivity dataset.

Raw extracted successful X records are appended to `data/processed/x_m2.jsonl`; clean validated records are in `x_clean.jsonl`/`.csv`. Day audit and checkpoints support resuming interrupted collection. Completed days, including effort-limited shortfalls, are not retried automatically. Resume can encounter changed/personalized results; record query, retrieval time and order as acquisition provenance. Do not extend limits to eliminate shortfalls. Stop on actual interface challenges/access denial; public post words are excluded from challenge detection.

## Guardian screening and pagination

Preserve the broad pilot query and retrieve the AI topic tag through all reported pages over the UTC envelope September 8–October 1. Actual Eastern timestamps control final inclusion. Pilot caches are reused as existing records; complete-query pagination caches are reused on rerun and only missing pages are fetched. Larger paginated responses can naturally repeat existing pilot IDs; IDs deduplicate the clean corpus.

Tag resolution corrected the provisional slug to `technology/artificialintelligenceai`, confirmed by the saved Guardian tag catalogue. The initial zero-result slug response is retained. This is a tag identifier correction within the frozen AI-topic scope, not an added news source or a sentiment-dependent query change.

Screen headline plus trail for substantive AI/entity/application coverage. Never use body-only incidental mentions for inclusion. Keep non-article/out-of-window/incidental exclusions with reasons, body text, URLs, original timestamps and request provenance. Thirty examples were stratified by inclusion and window third and reviewed together. Calibration excluded reader solicitations and included explicit driverless/self-driving applications; these are recorded in the validation output. Data/text scoring remains undone. A small stratified review is not a population accuracy estimate.

`finish_m2.py` applies the recorded review-derived rules without changing acquisition queries. Retrieval caches remain unchanged. Keyword screening is reproducible but cannot establish perfect relevance recall; ambiguous framing is for Milestone 3 validation.

## Market panel

Reuse six successful Yahoo chart caches; no repeat access test is necessary. Save daily close and vendor `adjclose` from September 4 through September 30. Expected calendar: weekdays excluding September 7 Labor Day, giving 18 sessions per symbol (108 rows), including the preceding close and 17 assignment-window sessions. Check symbol/date uniqueness, expected sessions, null/nonpositive prices and adjustment-event presence. Never impute.

Vendor adjusted prices reflect dividend/split adjustment; cached raw dividends/splits are retained in `outputs/market_adjustment_events.json`. No split events occur in the cached interval; dividend events occur for NVDA, GOOGL, META and SPY. Adjustment factors are not independently rebuilt into a total-return index. No returns have been viewed/calculated.

## Outputs

Clean corpora: `data/processed/guardian_clean.csv`, `x_clean.csv`/`.jsonl`, `market_panel.csv`. Full Guardian screening decisions: `guardian_screened.csv`. X exact-text sensitivity corpus: `x_unique_text_sensitivity.csv`.

Daily coverage: `outputs/guardian_daily_coverage.csv`, `x_daily_coverage.csv`, `market_daily_coverage.csv`. They distinguish successful collection, zero included results under specified screening, effort-limited sample shortfalls, nontrading sessions, and access failures/uncompleted days. Zero included items is not a claim of zero platform discussion.

Validation and pagination: `guardian_relevance_validation.csv`, `guardian_pagination_audit.json`, `x_validation_failures.csv`, `x_exact_text_duplicates.csv`, `market_coverage.csv`, and `milestone2_summary.json` in outputs. Earlier pilot original-page checks are preserved and reused rather than repeated.

Stop before Milestone 3. Sentiment scoring and AI-risk framing require the documented sampling/year caveats and separate validation.
