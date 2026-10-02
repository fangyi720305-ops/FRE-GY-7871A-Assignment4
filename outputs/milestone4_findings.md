# Milestone 4 findings memo — exploratory, not final report

The specification was frozen in milestone4_spec.json before return/regression results were calculated. Only cached prices and existing record-level compound scores were used. The original assignment screenshot/methodological PDFs remain unavailable; 2026 is provisional. X is a bounded Latest-search sample, not representative public opinion. These are exploratory text-sentiment measures, not validated AI attitudes.

## Returns and alignment

The daily-rebalanced, equal-weight five-company basket compounded to 3.56%; SPY to -0.74%, from September 4 close through September 30. Their cumulative performance difference is 4.29 percentage points. Individual returns use vendor-adjusted close ratios; cached dividends/splits were audited in Milestone 2 but adjustments are not independently reconstructed. No price imputation.

Seventeen return sessions are retained. Sentiment windows are (previous session close, current session close], with Eastern 16:00 closes and intervening weekend text included. September 8 is unavailable for primary sentiment because September 4–7 collection is absent; its observed September 8 texts are preserved in the exclusion audit. 21 records after September 30 close have no study return session. Completeness means intersected calendar dates have completed the frozen collection protocol, not complete platform/intraday coverage. X's September 14/16 daily shortfalls (19/20) remain flagged observed bounded samples. Empty channel windows would have missing means, not zero.

16 combined windows are available. X clock-split counts: 0 at/before 16:00 and 458 after 16:00 across all study dates; nontrading days use this only as a clock split. The strong imbalance is a consequence of capped Latest sampling and can shift apparent information timing. Counts are not total discussion volume. The 448-record exact-text sensitivity uses identical timestamp assignment and session grid.

## Frozen regressions

Primary: basket return_t = constant + basket return_(t−1) + Δcombined sentiment_(t−1). Changes use adjacent valid trading sessions only. The full grid is shifted before eligibility filtering; missing rows never make nonadjacent sessions consecutive. All text in predictors is timestamped at or before the previous session close. One-lag coefficients are decimal-return changes per 1-unit change in lagged compound sentiment.

| Test | n | Unrestricted residual df | Sentiment lag 1 | Sentiment lag 2 | Joint F | Unadjusted p | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| primary_combined_basket_1lag | 14 | 11 | 0.0188726 | unavailable | 0.820487 | 0.384449 | estimated_crosscheck_passed |
| secondary_combined_spread_1lag | 14 | 11 | 0.00850977 | unavailable | 0.477303 | 0.503965 | estimated_crosscheck_passed |
| secondary_guardian_basket_1lag | 14 | 11 | 0.0170116 | unavailable | 0.493524 | 0.496957 | estimated_crosscheck_passed |
| secondary_x_basket_1lag | 14 | 11 | 0.01553 | unavailable | 0.892375 | 0.365122 | estimated_crosscheck_passed |
| sensitivity_dedup_combined_basket_1lag | 14 | 11 | 0.0201966 | unavailable | 0.887551 | 0.366372 | estimated_crosscheck_passed |
| sensitivity_combined_basket_2lag | 13 | 8 | -0.012364 | -0.0434036 | 1.02674 | 0.400953 | estimated_crosscheck_passed |

All six planned tests were attempted, with usable dates, exclusions, coefficients, RSS and residuals saved. Successful manual least-squares/RSS F calculations match statsmodels OLS compare_f_test and joint f_test. The two-lag model restricts both sentiment coefficients jointly and retains the same two return lags in both nested models; its F test has no single coefficient sign. No alternative lags, baskets or scoring variants were searched.

Primary result: n=14, sentiment-change coefficient 0.0188726, F=0.820487, p=0.384449. These are in-sample incremental-predictability tests, not out-of-sample forecast validation. P-values are unadjusted across six exploratory comparisons. Conventional F inference assumes appropriate regression errors; homoskedasticity/serial independence and stationarity have not been established with this short series. No stationarity claim is made and no significance implies causation.

## Description and limitations

The saved correlation table separates same-session associations from sentiment_t versus return_(t+1), for levels and changes, basket and spread. Combined sentiment level correlations with basket returns are 0.251305 contemporaneously and 0.0849105 for the next session. Combined sentiment-change correlations are 0.105488 contemporaneously and 0.225306 for the next session. Correlations have no controls or inferential p-values. They are not the nested-regression test. The return and sentiment figures use unsmoothed values and retain the incomplete first window. The test p-values offer no compelling evidence of incremental prediction in this small sample; this does not establish absence of a relationship. Two-lag coefficient signs differ from the one-lag estimate, illustrating specification fragility rather than a directional conclusion from the joint F statistic.

General sentiment validation was weak: Codex agreement 50% Guardian and 75% X on 20 records/channel; framing agreement 60%/65%. There were no independent human labels. Negation, quotations, sarcasm, implicit framing, company-directed criticism and unrelated emotional language cause errors. Framing was not used as a new predictor. Measurement error, daily caps, query bias, small channel window counts, the short sample and provisional year materially limit interpretation. Statistical associations cannot establish genuine AI attitudes or channel bias.

Ready to assemble a cautious 5–6-page Milestone 5 report from these saved artifacts, with authoritative assignment/year evidence still unresolved. No final report has been written.

Calendar and test-method references: [NYSE trading hours and holiday calendar](https://www.nyse.com/trade/hours-calendars); [statsmodels nested-model F-test documentation](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.compare_f_test.html). These reference checks fetched no prices or text and did not recollect data.
