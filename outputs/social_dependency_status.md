# Social dependency — blocked

Checked October 1, 2026; provisional observation window September 8–30, 2026. Prior X failures reused without repeat unauthenticated attempts. No paid requests, account creation, messages, access bypass, or sentiment analysis.

**Preferred source:** X remains the preferred assignment source, conditional on a suitable dated export or verified free historical entitlement. **No currently tested source supports full collection.** Reddit is the strongest fallback candidate because original discussion text is discoverable, but only isolated examples were retrieved, with incomplete metadata. Facebook provided no usable dated data.

## Retrieved counts

- X: 0 in-window original records. No credentials/export available in the project. Two public dataset descriptions checked: warint/tweets-ai ends July 19, 2021; SinclairSchneider/tweets_sample_2026 ends July 27, 2026. The latter metadata and README were downloaded; its viewer shows original text/date/author fields, but it has no declared September coverage. No claim of exhaustively ruling out all possible datasets.
- Facebook: 0 original dated records. Broad AI searches for September 8/19/30 returned no results. MetaAI page HTTP 200 was a login/access response, not a successful corpus retrieval. No authenticated API tested.
- Reddit: 3 partial original-page examples, discovered on September 8, 19, and 30. Two have self-text, one is an image-only meme with a title. Authors and original URLs were verified on original pages. Exact publication timestamps could not be obtained. Discovery-date labels are separately retained, never promoted to timestamps. **0 records satisfy all required fields.** No comments collected. `social_pilot.csv` is schema-only; `social_discovery_examples.csv` contains partial originals and is explicitly ineligible for analysis.

All 23 dates lack qualified observations; these are missing data, not evidence of zero discussion. Three discovery dates cannot establish daily corpus feasibility. Search-engine selection, subreddit communities, moderation/deletion, image exclusion, variable visibility, and the technical-support example introduce substantial bias. A generated Reddit news digest was inspected for links only and excluded as an original opinion observation. No quoted news tweets were substituted.

## What resolves the dependency

**Best no-charge route: a user-supplied X corpus export** covering the full window, from broad queries such as `(AI OR "artificial intelligence" OR "generative AI" OR Anthropic OR ChatGPT OR OpenAI OR Claude OR Gemini)`, without risk-only filtering. Supply UTF-8 CSV or JSONL with `platform, post_id, text, publication_timestamp, author_identifier, original_url, retrieval_method, collection_query`; IDs as strings, complete original text, ISO 8601 timestamp with UTC/offset. Include query/date boundaries, retrieval provenance, pagination/sampling limits, and retweet/reply/quote indicators. An ordinary personal X account archive typically contains that account's own activity, not a general AI-discussion corpus; it cannot be assumed sufficient. ID-only datasets need authorized text hydration and do not resolve this blocker themselves.

**X API alternative:** valid `X_BEARER_TOKEN` (or supported equivalent), authorized for `/2/tweets/search/all`, plus confirmed existing no-charge entitlement adequate for this task. Do not add a billed token and run the pilot automatically. No-charge entitlement is unverified; recent seven-day search cannot supply the entire window.

**Reddit fallback:** an approved Reddit research-access account/project (the current academic route is Reddit for Researchers), or a provenance-documented export meeting the same schema plus `record_type`, `title`, `self_text`, subreddit, and parent/link IDs for comments. If an approved OAuth Data API route is supplied, its client ID/secret and approved token need local configuration; OAuth alone does not demonstrate historical search completeness. Research access/export must be tested on all three anchor dates, then daily counts audited. No application was submitted on your behalf.

**Facebook fallback:** an authorized research or Page-scoped historical export/API with full text, original IDs/URLs, authors and timestamps. A personal archive/login or access to a single Page does not establish general AI discourse. Authenticated API routes remain untested.

Full collection and sentiment remain paused until a corpus with genuine complete records is verified. Assignment-year confirmation is also still outstanding. User authorization now permits platform alternatives if X cannot provide historical data; Guardian remains the sole news source.

## Evidence

- X historical/recent API scope: https://docs.x.com/x-api/posts/search/introduction
- Old AI dataset: https://github.com/warint/tweets-ai
- 2026 dataset date range/schema: https://huggingface.co/datasets/SinclairSchneider/tweets_sample_2026 (cached README and metadata in data/raw)
- Reddit academic access: https://support.reddithelp.com/hc/en-us/articles/49381918834964-Reddit-for-Researchers-Program
- Original Reddit URLs and acquisition queries: data/processed/social_discovery_examples.csv
- Actual local request outcomes: outputs/social_route_tests.json and outputs/reddit_html_routes.json

Additional exploration stopped within the approximately 20-minute budget. The saved scripts are bounded access probes, not corpus collectors; do not repeatedly rerun failed routes without changed access conditions.
