# Logged-in X pilot — Windows

Profile: `.browser-profile/x-pilot`, Git ignored. Sign into the visible dedicated Chrome window manually. No passwords/cookies are requested in chat or copied from other profiles. Browser profile contains authentication state locally; do not share or commit it. No authenticated HTML dumps, screenshots, traces, HAR, or network logs are saved.

From Assignment 4 in PowerShell:

```powershell
& 'C:\Users\fangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' .\src\x_browser_pilot.cjs
```

Requires installed Chrome and the existing bundled Playwright; no API purchase. The browser waits up to 10 minutes for manual login. It closes at pilot completion, failure, or login timeout; rerun reuses the dedicated profile and cached qualified records. Do not rerun a blocked route without a concrete change. CAPTCHA/account challenges, explicit denial and rate limits stop the pilot. User must resolve login manually; no bypass is attempted.

Fixed query: `("artificial intelligence" OR "generative AI" OR Anthropic) lang:en -filter:retweets`, plus `since`/`until` for September 8, 19 and 30, provisionally 2026. Latest selection must be verified. Sample first 10 qualified English full-text posts per date in displayed order; maximum six scrolls, slow sequential navigation. This narrow fixed query is neutral about sentiment but misses discussion using other AI names. A future collection may predeclare an expanded fixed query set; do not alter queries mid-pilot to choose sentiment.

Records are scoped to tweet containers. Enclosing status link/time supplies ID and author. Quote relationships stay separate; ambiguous containers are excluded. Truncated posts are visited normally and accepted only if full text becomes available. English uses the page's language tag and needs manual review. `since`/`until` are intended inclusive/exclusive boundaries; eligibility checks actual ISO timestamps against the requested UTC day. This does not establish X's exact filter timezone; final Eastern-day analysis remains unresolved. Date-filter leakage is counted.

Incremental deduplicated JSONL/CSV: `data/processed/x_browser_pilot.*`. Status/counts: `outputs/x_browser_status.json`. Cached successful IDs are reused. No complete archive coverage is claimed. 2026 remains provisional pending authoritative assignment/event verification.

If search works but extraction does not, capture manually from the same browser and queries:

```powershell
& 'C:\Users\fangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\src\x_manual_capture.py --date 2026-09-08
```

Repeat for 2026-09-19 and 2026-09-30. Helper prints the URL to paste into the dedicated Chrome window; it does not use a different profile. Supply exact original timestamps with timezone, original URLs, complete enclosing text and displayed order. Exclude uncertain timestamps, images without text, non-English/truncated records. Save quote URLs separately. Output `x_manual_pilot.*` reuses manual IDs. Deduplicate against browser output by post ID before combining sources; never add their counts blindly.

No sentiment or full-window collection runs in either script. Normal search may be personalized, incomplete, ranked or capped despite Latest; daily counts from this pilot describe retrieved samples only.

## Google login restriction — October 1, 2026
User reported Google's "browser may not be secure" refusal during Google sign-in for X in Playwright Chrome. This is a login/access restriction, not evidence that authenticated X search fails. Automated session ended with a generic browser-operation error before any posts were collected. No automated retry of Google login, security weakening, cookie extraction, or restriction bypass was attempted.
Ordinary Chrome was then launched with the same dedicated profile, without automation. Manual Google login and normal X search remain pending. Do not relaunch Playwright while ordinary Chrome is using this profile. If normal login works, use normal Latest search and x_manual_capture.py; the route is not yet verified.

## Corrected pilot (supersedes earlier UTC/exclusive-end assumptions)
See outputs/x_date_debug_result.md. Verified 10 complete genuine records each on Sep 8/19/30 Eastern. Query uses since:DATE until:DATE under empirically observed inclusive Eastern end-date behavior; each actual timestamp is independently validated in America/New_York. The fixed collector needs src/x_debug.cjs alongside it. Successful cached dates are skipped. No full collection or sentiment has run.
