# Milestone 3 — local sentiment and framing

Run from `D:\School Work\FRE-GY 7871 NLP\Assignment 4` in PowerShell:

```powershell
$m3Python = 'C:\Users\fangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $m3Python .\src\milestone3.py
& $m3Python .\src\finalize_m3.py
```

Both scripts are local and do not read market prices or fetch data. Installed project-local packages: vaderSentiment 3.3.2 and matplotlib 3.10.8 in Git-ignored `.local-packages`. If recreating the environment, install those versions with `& $m3Python -m pip install --target .local-packages vaderSentiment==3.3.2 matplotlib==3.10.8`; this is unnecessary for normal reruns. Use Python 3.12 with tzdata support; cache/method hashes detect score-setting or lexicon changes.

VADER defaults and compound thresholds (+0.05/−0.05 inclusive) are frozen in outputs/scoring_method.json with lexicon/emoji SHA256 hashes. Rule dictionary: src/framing_rules.json and outputs/framing_rules.json. No alternate models or tuning. The append-only sentiment/framing caches are keyed by analyzed text hash and method/dictionary hash. Changing input content produces a new cache entry; unchanged inputs reuse scores.

Primary record files: data/processed/guardian_scored.csv, x_scored.csv, scored_records.jsonl. Sensitivity record file: x_unique_text_scored.csv. They retain original and analyzed text, original and UTC/Eastern timestamps, URLs, query/order provenance, categories, evidence spans/context and uncertain/report/reject/endorse stance. Nested quote relationships remain separate.

Daily outputs: outputs/daily_channel_sentiment.csv, daily_combined_sentiment.csv, daily_channel_sensitivity.csv, daily_combined_sensitivity.csv, duplicate_sensitivity_comparison.csv. Explicit record denominators are included. Compound means are unweighted within channel/day; combined means use half of each observed channel mean. The exact-text sensitivity reuses the frozen 448-record input.

Validation: outputs/validation_sample.json fixes the 40-ID diagnostic sample. Initial automatic labels are preserved; outputs/validation_reviews.json contains Codex judgments, and validation_ledger.csv compares them with initial/final rules. No independent human validation. src/save_m3_reviews.py documents the one-time judgments and one variant correction; rerunning the normal scoring command never generates new reviewed judgments. Existing reviews must not be silently reused if analyzed texts change. Full findings: outputs/validation_summary.json and milestone3_limitations.md. One correction and affected IDs: framing_correction_audit.json; initial dictionary: framing_rules_initial.json.

Draft figures: outputs/daily_sentiment_draft.png/svg and framing_shares_draft.png/svg. Figures use unsmoothed daily values, a sentiment zero line, explicit sample sizes, and overlapping framing categories. Summary: outputs/milestone3_summary.json. Integrity checks: outputs/milestone3_integrity.json. Collection inputs and credentials remain unchanged.

Readiness is limited to exploratory Milestone 4. Generic text sentiment is not validated AI attitude. X is a bounded search sample; year 2026 is provisional. Stop before returns alignment, Granger tests and final-report writing.
