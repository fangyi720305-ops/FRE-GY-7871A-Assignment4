# Access evidence and blockers

Checked October 1, 2026. Only .env existed in Assignment 4 before this task; no authoritative screenshot or reference files were available there. Nearby assignment files belong to earlier assignments and were not substituted.

## Event evidence

Located candidate original URL: https://x.com/EvanHub/status/2097497037956891126 . Original web reader returned HTTP 403, so no genuine original post text was saved. ID time calculation: `(2097497037956891126 >> 22) + 1288834974657` milliseconds after Unix epoch = 2026-09-09T01:27:18.116Z = 2026-09-08 21:27:18.116 Eastern.

Supporting discovery page: https://www.thinkfacility.com/blog/anthropic-researcher-jacob-coxon-quits-gambling-with-our-lives/ reports September 8, 9:27 pm Eastern and the 2026 event context. https://www.cougarboard.com/board/message.html?id=37754453&source=rss links the candidate ID and attributes the post to Evan Hubinger with September 9, 2026 UTC date. These are secondary evidence for locating the post, not additional news sources or X observations. Their quoted text was not inserted in the pilot corpus. The assignment screenshot is required to verify the quoted-post match; year 2026 remains provisional for collection.

## X

No recognized bearer credentials found in project .env or process environment. Direct original URL failed HTTP 403. Three broad dated public searches (beginning/middle/end) returned no results. No genuine X records retrieved; x_pilot.csv contains only its header. This establishes neither isolated-original access nor corpus access. Full-archive API, logged-in browser search, exports, and third-party scrapers were not successfully tested; untested routes are labeled in the audit. Testing stopped after bounded discovery, without infrastructure or access bypass.

Official documentation: https://docs.x.com/x-api/posts/search/introduction says recent search covers seven days and full-archive search covers the historical archive. Recent search cannot cover this full September window on October 1. A valid bearer credential with full-archive access and sufficient provider entitlement may resolve access but remains untested. Alternatively supply a provenance-documented dated export in the schema specified in analysis_plan.md. Neither option guarantees a representative daily corpus until retrieved and audited.

## Guardian and market

Guardian route https://content.guardianapis.com/search ; documentation https://open-platform.theguardian.com/documentation/ . Successful raw payloads are cached; headline/trail/body and timestamps are inspected separately. Broad queries produced incidental mentions; end-date oldest results initially had no explicit headline/trail candidates, prompting one narrow newest-first pilot request. No relevance scoring or sentiment has been performed.

Market route https://query1.finance.yahoo.com/v8/finance/chart/{symbol} . All six symbols returned actual close and adjclose values, including September 4 preceding close and September 8/18/30. Adjusted close is the vendor-supplied dividend/split-adjusted series; the exact factor convention is not independently reconciled. Raw dividend/split events are preserved for later validation. It is not a separately built total-return index. No basket returns calculated.

## Milestone 2 readiness

Guardian and market access verified for provisional 2026 samples. Full collection is blocked by missing authoritative assignment materials/year confirmation and lack of a verified X historical corpus. Do not automatically replace X. No final report or full analysis was produced.
