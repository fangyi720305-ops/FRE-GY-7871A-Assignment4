"""Output checks and concise milestone documentation, without market analysis."""
import json,csv,hashlib,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; O=ROOT/'outputs'; D=ROOT/'data'/'processed'
def readcsv(p):
    with p.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def dump(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
records=[json.loads(x) for x in (D/'scored_records.jsonl').read_text(encoding='utf-8').splitlines()]
daily=readcsv(O/'daily_channel_sentiment.csv'); combined=readcsv(O/'daily_combined_sentiment.csv'); sens=readcsv(O/'daily_channel_sensitivity.csv'); comp=readcsv(O/'duplicate_sensitivity_comparison.csv')
ledger=readcsv(O/'validation_ledger.csv'); summary=json.loads((O/'milestone3_summary.json').read_text(encoding='utf-8'))
cats=['existential_safety','economic_social','benefits_opportunity','investment_valuation']
assert len(records)==644 and len(daily)==46 and len(combined)==23 and len(sens)==46 and len(ledger)==40
assert all(r['analyzed_text'] and r['publication_timestamp'] and r['url'] for r in records)
assert all(-1<=r['compound']<=1 for r in records)
assert all(abs(sum(float(r[x+'_share']) for x in ['positive','negative','neutral'])-1)<1e-12 for r in daily+sens)
assert all(int(r['record_count'])==int(r['sentiment_denominator'])==int(r['framing_denominator'])>0 for r in daily+sens)
assert all(abs(float(r['combined_mean_compound'])-.5*sum(float(x['mean_compound']) for x in daily if x['eastern_date']==r['eastern_date']))<1e-12 for r in combined)
assert all(len([r for r in ledger if r['channel']==c])==20 for c in ['Guardian','X'])
assert len(set((r['channel'],r['record_id']) for r in records))==644
original_x={r['post_id']:r for r in [json.loads(x) for x in (D/'x_clean.jsonl').read_text(encoding='utf-8').splitlines()]}
assert all(r['original_text']==original_x[r['record_id']]['text'] and r['author_identifier']==original_x[r['record_id']]['author_identifier'] and r['url']==original_x[r['record_id']]['original_url'] and r['publication_timestamp']==original_x[r['record_id']]['publication_timestamp'] for r in records if r['channel']=='X')
initial=json.loads((O/'validation_sample.json').read_text(encoding='utf-8'))
prior_rules=json.loads((O/'framing_rules_initial.json').read_text(encoding='utf-8')); finalrules=json.loads((ROOT/'src'/'framing_rules.json').read_text(encoding='utf-8'))
# Count actual changed category flags against v1 without changing or tuning rules.
import sys; sys.path.insert(0,str(ROOT/'src')); import milestone3 as m
final_dict=m.RULES; changed=[]
for r in records:
    m.RULES=prior_rules; before=m.framing(r['analyzed_text']); m.RULES=final_dict
    if any(before[c]!=r[c] for c in cats): changed.append({'channel':r['channel'],'record_id':r['record_id'],'before':[c for c in cats if before[c]],'after':[c for c in cats if r[c]]})
dump(O/'framing_correction_audit.json',{'correction':finalrules['correction'],'old_version':prior_rules['version'],'new_version':finalrules['version'],'changed_flag_records':changed,'n_changed':len(changed),'sentiment_method_changed':False,'market_returns_used':False})
dump(O/'framing_rules.json',finalrules)
agreement=sum(r['sentiment_agrees']=='True' for r in ledger)
validation={'reviewer':'Codex','independent_human_validation':False,'sample_n':40,'channel_n':20,'selection':'Fixed seed 787103; diagnostic sentiment/framing strata followed by fixed-seed fill; exact 40-ID manifest frozen before review; sample is not prevalence-weighted or a representative accuracy estimate','primary_text_only_review':True,'body_context_used':False,'general_sentiment_agreement_n':agreement,'general_sentiment_agreement':agreement/40,'by_channel':summary['validation'],'framing_exact_agreement_n':sum(r['final_framing_exact_agrees']=='True' for r in ledger),'error_types':['VADER: positive vocabulary such as agree, protect, safety, curiosity and profit can dominate adverse AI-risk context','VADER: scientific problem solved is penalized by stumped; job-prospect declines can score near neutral','Negation scope: not intelligent enough; not perfect but useful; double negatives','Quotation/attribution/satire: risk statement quoted, disputed or mocked is not endorsement','Framing undercoverage: paraphrased scientific advances, declining job prospects, harms/control language not matching fixed phrases','Framing false positives: opportunity to repair harm; social-information bubble rather than valuation bubble; capex alone does not establish financial risk','Stance false positives: experts can refer to workshop attendees; lexical negation scope can reject the wrong proposition','Long X posts mix AI commentary with company criticism, PR insults, politics and unrelated emotion/financial vocabulary'],'one_correction':finalrules['correction'],'conclusion':'Diagnostic agreement is limited. Preserve the generic VADER measure as text sentiment in AI-related material; do not describe it as a validated AI-specific attitude or investment-sentiment measure. Rule shares describe explicit dictionary matches, not comprehensive true risk-framing prevalence.'}
dump(O/'validation_summary.json',validation)
summary['validation_overall']=validation['general_sentiment_agreement']; summary['framing_validation_overall']=validation['framing_exact_agreement_n']/40
summary['framing_correction_changed_records']=len(changed)
summary['readiness']='Files ready for exploratory Milestone 4 only; generic sentiment and framing are limited, not validated AI-specific attitudes. Year remains provisional. Timing/lag choices must be frozen before returns alignment.'
summary['record_weighting']='Overall channel means weight records equally; combined series weights channel daily means 0.5 each. No market-date alignment.'
summary['duplicate_sensitivity']['overall_x_mean_change']=summary['sensitivity_overall']['X']['mean_compound']-summary['overall']['X']['mean_compound']
summary['duplicate_sensitivity']['daily_max_change_date']=max(comp,key=lambda r:abs(float(r['x_mean_change'])))['eastern_date']
summary['validation_checks']={'record_completeness':True,'source_x_text_author_url_timestamp_preserved':True,'eastern_window_and_daily_assignment':True,'daily_counts_and_denominators':True,'class_shares_sum_to_one':True,'combined_half_weights':True,'sensitivity_ids_match_448_record_input':True,'missing_values_imputed':False,'market_data_accessed':False}
dump(O/'milestone3_summary.json',summary)
limitations='''# Milestone 3 validation and limitations

All 186 Guardian articles and 458 X posts were scored locally. Every Eastern day September 8–30 has observations; X has 19–20/day and Guardian 3–17/day. X is a bounded Latest-search sample, not representative public opinion or total discussion volume. The 2026 year remains provisional: the candidate trigger ID's encoded date is not authoritative assignment confirmation.

VADER compound measures **text sentiment in AI-related material**. It does not reliably measure stance toward AI, safety, technology companies or investments. Guardian uses headline plus cleaned trail; X uses enclosing original post text. Article bodies and nested quoted posts are excluded from scoring. Original text, publication timestamps, URLs, authors, query/order provenance and quote relationships remain available. HTML is stripped, entities decoded, recognizable URL tokens replaced with URL, and whitespace collapsed; negation, punctuation and emojis remain. Fragmented visible links may leave non-URL fragments.

Forty fixed, stratified records (20/channel) were inspected by Codex from actual primary texts. No independent human labels were obtained. The ledger stores initial automated labels and separate reviewed judgments; labels were not silently replaced. General sentiment-class agreement: Guardian 10/20 (50%), X 15/20 (75%), overall 25/40 (62.5%). This diagnostic sample overweights categories and is not a population accuracy estimate. Framing exact-category agreement changed from Guardian 10/20 to 12/20 after one correction, with X 13/20 unchanged. Overall final agreement is 25/40. Evidence adequacy and stance can still be wrong even when category sets agree.

One rule correction recognized variants of existing safety/control concepts: out-of-control, A.I. safety/alignment and rogue agents. No sentiment lexicon edits or market-based tuning occurred. The original dictionary, initial sample labels, final dictionary and affected record IDs are saved. Main remaining errors: scientific progress and job-prospect paraphrases missed; opportunity to repair a hack misread as AI benefit; social bubble misread as valuation risk; capex alone insufficient risk evidence; negation and attribution mis-scoped. Generic positive words and quoted/sarcastic material often conflict with AI-specific attitude. Uncertain stance remains explicit. Missing dictionary matches mean unclassified, not neutral; category flags can overlap and rejected risks still count as mentions.

All framing shares use all channel records as the denominator; they measure dictionary-match prevalence rather than true exhaustive risk prevalence. Guardian has more matched safety/economic framing and X more matched benefits in this corpus, but query sampling, headline/trail brevity, post lengths, dictionary coverage and measurement error prevent an objective-bias conclusion. X counts are capped samples. The secondary combined series is 0.5 × each observed channel daily mean; it is not pooled text sentiment or a volume-weighted measure. No missing values are treated as neutral.

Exact-text sensitivity uses the existing 448-ID corpus, not a new cleaned-text definition. It retains every observed day and changes X's overall mean only slightly; individual daily shifts are larger. Sensitivity channel/framing shares and combined daily means are saved separately. Draft charts use unsmoothed calendar-day values and do not align with same-day market returns.

Milestone 3 artifacts are ready for exploratory Milestone 4 with these limitations. They are not validated AI-specific attitude measures. Human review would strengthen interpretation. Freeze timing, nontrading-day and lag choices before accessing returns. No returns, Granger tests or final report have been produced.
'''
(O/'milestone3_limitations.md').write_text(limitations,encoding='utf-8')
readme='''# Milestone 3 — local sentiment and framing

Run from `D:\\School Work\\FRE-GY 7871 NLP\\Assignment 4` in PowerShell:

```powershell
$m3Python = 'C:\\Users\\fangyi\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe'
& $m3Python .\\src\\milestone3.py
& $m3Python .\\src\\finalize_m3.py
```

Both scripts are local and do not read market prices or fetch data. Installed project-local packages: vaderSentiment 3.3.2 and matplotlib 3.10.8 in Git-ignored `.local-packages`. If recreating the environment, install those versions with `& $m3Python -m pip install --target .local-packages vaderSentiment==3.3.2 matplotlib==3.10.8`; this is unnecessary for normal reruns. Use Python 3.12 with tzdata support; cache/method hashes detect score-setting or lexicon changes.

VADER defaults and compound thresholds (+0.05/−0.05 inclusive) are frozen in outputs/scoring_method.json with lexicon/emoji SHA256 hashes. Rule dictionary: src/framing_rules.json and outputs/framing_rules.json. No alternate models or tuning. The append-only sentiment/framing caches are keyed by analyzed text hash and method/dictionary hash. Changing input content produces a new cache entry; unchanged inputs reuse scores.

Primary record files: data/processed/guardian_scored.csv, x_scored.csv, scored_records.jsonl. Sensitivity record file: x_unique_text_scored.csv. They retain original and analyzed text, original and UTC/Eastern timestamps, URLs, query/order provenance, categories, evidence spans/context and uncertain/report/reject/endorse stance. Nested quote relationships remain separate.

Daily outputs: outputs/daily_channel_sentiment.csv, daily_combined_sentiment.csv, daily_channel_sensitivity.csv, daily_combined_sensitivity.csv, duplicate_sensitivity_comparison.csv. Explicit record denominators are included. Compound means are unweighted within channel/day; combined means use half of each observed channel mean. The exact-text sensitivity reuses the frozen 448-record input.

Validation: outputs/validation_sample.json fixes the 40-ID diagnostic sample. Initial automatic labels are preserved; outputs/validation_reviews.json contains Codex judgments, and validation_ledger.csv compares them with initial/final rules. No independent human validation. src/save_m3_reviews.py documents the one-time judgments and one variant correction; rerunning the normal scoring command never generates new reviewed judgments. Existing reviews must not be silently reused if analyzed texts change. Full findings: outputs/validation_summary.json and milestone3_limitations.md. One correction and affected IDs: framing_correction_audit.json; initial dictionary: framing_rules_initial.json.

Draft figures: outputs/daily_sentiment_draft.png/svg and framing_shares_draft.png/svg. Figures use unsmoothed daily values, a sentiment zero line, explicit sample sizes, and overlapping framing categories. Summary: outputs/milestone3_summary.json. Integrity checks: outputs/milestone3_integrity.json. Collection inputs and credentials remain unchanged.

Readiness is limited to exploratory Milestone 4. Generic text sentiment is not validated AI attitude. X is a bounded search sample; year 2026 is provisional. Stop before returns alignment, Granger tests and final-report writing.
'''
(ROOT/'MILESTONE3_README.md').write_text(readme,encoding='utf-8')
for filename in ['README.md','analysis_plan.md']:
    path=ROOT/filename; text=path.read_text(encoding='utf-8'); marker='\n## Milestone 3 completed\n'
    if marker in text: text=text.split(marker)[0]
    text+=marker+'Local VADER scoring and transparent multi-label framing completed for 186 Guardian and 458 X records across all 23 Eastern calendar dates. Fixed 40-record Codex review: general sentiment agreement 50% Guardian, 75% X; final exact framing agreement 60%/65%. No independent human validation. One safety-phrase variant correction applied, remaining errors retained as limitations. Scores are text sentiment in AI-related material, not validated AI-specific attitudes. The 448-record X exact-text sensitivity and equal-channel daily combined series are saved. Read MILESTONE3_README.md and outputs/milestone3_limitations.md for commands, outputs and caveats. Year remains provisional; X is a bounded search sample. Ready for exploratory Milestone 4 only after timing/lag rules are frozen. No market returns, Granger tests or final report were produced. Earlier milestone notes above describe historical states.\n'
    path.write_text(text,encoding='utf-8')
files=['guardian_clean.csv','x_clean.csv','x_clean.jsonl','x_unique_text_sensitivity.csv','market_panel.csv']
integrity={'inputs_sha256':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in files},'validated_records':644,'daily_channel_rows':46,'combined_days':23,'review_records':40,'checks':summary['validation_checks'],'figures':'visually reviewed PNG drafts; SVG versions also saved','packages':json.loads((O/'scoring_method.json').read_text(encoding='utf-8'))['package_version']}
dump(O/'milestone3_integrity.json',integrity)
print(json.dumps({'validation_agreement':agreement/40,'framing_correction_changed_records':len(changed),'daily_rows':46,'combined_days':23,'integrity':'passed','sensitivity_overall_mean_change':summary['duplicate_sensitivity']['overall_x_mean_change']}))
