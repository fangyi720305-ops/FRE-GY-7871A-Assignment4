# Scope and remaining milestones

## Milestone 1 status

Project initialized. See source_access_audit.csv and outputs/pilot_summary.json for actual retrieval outcomes. Pilot window is explicitly provisional: 2026-09-08 through 2026-09-30.

Candidate trigger: https://x.com/EvanHub/status/2097497037956891126 . Its snowflake decodes to 2026-09-09T01:27:18.116Z, or September 8 at 9:27:18 pm America/New_York. This verifies the date encoded in the located ID, not authorship or original text. Direct original retrieval failed with HTTP 403. Match to the authoritative screenshot is unresolved. No collection year is fully verified yet.

## Milestone 2 — collect and audit

Proceed only after screenshot/year confirmation and an agreed usable X historical route or dated export. Collect Guardian with broad terms, pagination, stable IDs, sequential throttling, raw caches and retrieval timestamps. Expand queries to AI, Claude, Gemini, machine learning, and related AI terms while screening headline/trail relevance. Preserve the broad-query false positives as audit evidence; do not feed them into sentiment. Manually review relevance, deduplicate IDs and near-identical articles, separate news/comment/opinion categories, and audit daily counts, missing bodies, language, and query bias.

X export required fields: id (string), text (complete original text), author_id (string), author/username, timestamp (ISO 8601 with UTC or offset), original URL. Prefer language, retweet/quote/reply indicators, query, retrieval date and acquisition provenance. CSV UTF-8 or JSONL accepted. Must cover every date September 8–30, include benefit and risk discussion, preserve sampling procedure and limitations, and distinguish zero observations from missing days. Quotes in news, snippets, and screenshots are not original observations.

## Milestone 3 — sentiment and framing

Predefine a sentiment method and risk-frame categories; validate stratified manual samples by date/source and label. Separate sentiment toward AI from market expectations and risk coverage. No scores have been computed.

## Milestone 4 — returns and timing

Use vendor adjusted close for close-to-close returns; investigate dividends/splits before treating them as total-return proxies. September 8 return needs September 4 close (September 7 holiday); verified sample availability for all six symbols. Basket daily return is mean of five constituent daily returns; compound it, and compare with SPY using identical dates. Align news/X to America/New_York and the actual market close; the candidate trigger occurs after the September 8 close. Predefine weekend/nontrading-day aggregation and lag direction to avoid look-ahead. Approximately 17 trading observations severely limit Granger testing: use minimal predeclared lags, inspect stationarity, report power limits and multiple testing, and do not infer causality.

## Milestone 5 — report

Interpret validated results; verify every figure, number and source. Prepare the authoritative 5–6 page submission only at this stage.

## Social-access update (October 1, 2026)
User authorizes alternative social platforms if X historical data is unavailable. See outputs/social_dependency_status.md and social_access_audit.csv. No full collection or sentiment is ready: 3 partial Reddit originals, 0 timestamp-qualified social records. Guardian-only analysis remains prohibited.

Logged-in X update: user login succeeded; Latest and visible extraction verified. Zero eligible pilot records for Sep 8/19/30; six out-of-date originals cached separately. Date filtering remains unresolved. See outputs/x_browser_pilot_result.md. Do not proceed to sentiment.

## Verified X route update
The date debug corrected the endpoint/UTC-day assumptions and strengthened readiness, quote matching, and challenge detection. Thirty qualified originals (10 each Sep 8/19/30 Eastern) are saved. Three original pages match author, text, ID, and timestamp. Bounded sampled collection is technically feasible; complete archive coverage, daily representativeness, and provisional year confirmation remain unresolved. See outputs/x_date_debug_result.md. Stop before full collection and sentiment.

## Milestone 2 completed
Frozen collection rules preceded all collection, returns and sentiment outcomes. Guardian: 387 screened candidates, 186 included, 3–17 articles/day across all 23 Eastern dates; complete broad-query and resolved-AI-tag pagination. Thirty stratified relevance examples reviewed; two initial disagreements calibrated the screen (four corpus decisions corrected). X: 458 globally unique original posts; 21 dates at 20, Sep 14 and 16 at 19 within fixed effort limits. Twenty-nine eligible pilot posts reused. Six exact-text duplicate groups (10 extra IDs) flagged; 448 unique-text sensitivity records. All X timestamp/day, ID-time, author/status, English and text checks pass; three prior original-page matches reused. Market: 108 observations, all six symbols across 18 sessions Sep 4–30, no missing/duplicate/nonpositive prices; vendor adjusted-price conventions/events saved, no imputation. One browser timeout resolved by resuming unfinished days. Caches preserved; credential scan passes. Ready for Milestone 3 under provisional-year and bounded-search-sampling caveats. No sentiment scoring, returns analysis, Granger testing or report writing has run.

## Milestone 3 completed
Local VADER scoring and transparent multi-label framing completed for 186 Guardian and 458 X records across all 23 Eastern calendar dates. Fixed 40-record Codex review: general sentiment agreement 50% Guardian, 75% X; final exact framing agreement 60%/65%. No independent human validation. One safety-phrase variant correction applied, remaining errors retained as limitations. Scores are text sentiment in AI-related material, not validated AI-specific attitudes. The 448-record X exact-text sensitivity and equal-channel daily combined series are saved. Read MILESTONE3_README.md and outputs/milestone3_limitations.md for commands, outputs and caveats. Year remains provisional; X is a bounded search sample. Ready for exploratory Milestone 4 only after timing/lag rules are frozen. No market returns, Granger tests or final report were produced. Earlier milestone notes above describe historical states.

## Milestone 4 completed
Cached adjusted returns and timestamp-aligned sentiment completed under frozen milestone4_spec.json. Basket cumulative return 3.56%; SPY -0.74%. Primary one-lag change model: n=14, coefficient=0.0188726, F=0.820487, unadjusted p=0.384449. Six planned tests and manual/statsmodels cross-checks saved; full session grid retained. September 8 sentiment is unavailable due to uncollected September 4–7; text after final close excluded. Read MILESTONE4_README.md and outputs/milestone4_findings.md. Generic text sentiment, weak validation, bounded X sampling, unadjusted exploratory comparisons and provisional 2026 remain material caveats. Ready for cautious Milestone 5 drafting with assignment/year verification unresolved; no final report written.
