"""Cached-data-only Milestone 4. No collection, scoring, tuning, or final report."""
import sys,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.local-packages'))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.local-packages'/'mpl-config'))
import csv,json,hashlib,math,statistics,importlib.metadata
from datetime import date,datetime,time,timedelta,timezone
from zoneinfo import ZoneInfo
import numpy as np
from scipy.stats import f as fdistribution
from statsmodels.regression.linear_model import OLS
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
DATA=ROOT/'data'/'processed'; OUT=ROOT/'outputs'; ET=ZoneInfo('America/New_York')
SYMBOLS=['NVDA','MSFT','GOOGL','AMZN','META','SPY']; COMPANIES=SYMBOLS[:5]
def readcsv(p):
    with p.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def dump(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def csvwrite(p,rows):
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in rows: w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})
def hashfile(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def iso(d): return d.isoformat()
def days(lo,hi): return [lo+timedelta(days=i) for i in range((hi-lo).days+1)]
def close(d): return datetime.combine(d,time(16),ET)
def mean(g): return statistics.mean(r['compound'] for r in g) if g else None
def pct(x): return f'{100*x:.2f}%'
def statsfmt(x): return 'unavailable' if x is None else f'{x:.6g}'

def returns():
    sessions=[d for d in days(date(2026,9,4),date(2026,9,30)) if d.weekday()<5 and d!=date(2026,9,7)]
    prices=readcsv(DATA/'market_panel.csv'); lookup={(r['symbol'],r['date']):float(r['adjusted_close']) for r in prices}
    assert len(prices)==len(lookup)==108
    assert set(lookup)=={(s,str(d)) for s in SYMBOLS for d in sessions}
    assert all(math.isfinite(p) and p>0 for p in lookup.values())
    individual=[]; panel=[]; growth={s:1. for s in SYMBOLS}; bg=sg=spreadg=1.
    for i,d in enumerate(sessions):
        if i==0:
            panel.append({'session_date':str(d),'previous_session_date':None,'basket_return':None,'spy_return':None,'spread_return':None,'basket_cumulative_return':0.,'spy_cumulative_return':0.,'spread_synthetic_cumulative_return':0.,'basket_minus_spy_cumulative_difference':0.})
            for s in SYMBOLS: individual.append({'symbol':s,'session_date':str(d),'previous_session_date':None,'adjusted_close':lookup[s,str(d)],'previous_adjusted_close':None,'simple_return':None,'cumulative_return':0.})
            continue
        previous=sessions[i-1]; rets={s:lookup[s,str(d)]/lookup[s,str(previous)]-1 for s in SYMBOLS}
        for s,r in rets.items():
            growth[s]*=1+r
            assert math.isclose(growth[s]-1,lookup[s,str(d)]/lookup[s,str(sessions[0])]-1,abs_tol=1e-12)
            individual.append({'symbol':s,'session_date':str(d),'previous_session_date':str(previous),'adjusted_close':lookup[s,str(d)],'previous_adjusted_close':lookup[s,str(previous)],'simple_return':r,'cumulative_return':growth[s]-1})
        basket=sum(rets[s] for s in COMPANIES)/5; spy=rets['SPY']; spread=basket-spy
        bg*=1+basket; sg*=1+spy; spreadg*=1+spread
        panel.append({'session_date':str(d),'previous_session_date':str(previous),**{s+'_return':rets[s] for s in COMPANIES},'basket_return':basket,'spy_return':spy,'spread_return':spread,'basket_cumulative_return':bg-1,'spy_cumulative_return':sg-1,'spread_synthetic_cumulative_return':spreadg-1,'basket_minus_spy_cumulative_difference':bg-sg})
    csvwrite(DATA/'individual_returns.csv',individual); csvwrite(DATA/'return_panel.csv',panel)
    summary={'sessions_with_returns':17,'preceding_close':'2026-09-04','first_return':'2026-09-08','last_return':'2026-09-30','basket_cumulative_return':bg-1,'spy_cumulative_return':sg-1,'cumulative_performance_difference':bg-sg,'synthetic_compounded_spread':spreadg-1,'individual_cumulative_returns':{s:growth[s]-1 for s in SYMBOLS},'daily_rebalancing':True,'basket_weights':{s:.2 for s in COMPANIES},'price_convention':'Cached vendor dividend/split adjusted closes; adjustments not independently rebuilt','spread_convention':'Daily basket return minus SPY return. Its compounded synthetic index is not a self-financing strategy or the difference between cumulative basket and SPY returns.'}
    dump(OUT/'return_summary.json',summary)
    return sessions,panel,summary

def align(sessions,records):
    coverage={'Guardian':{r['date']:r for r in readcsv(OUT/'guardian_daily_coverage.csv')},'X':{r['date']:r for r in readcsv(OUT/'x_daily_coverage.csv')}}
    dedupids={r['post_id'] for r in readcsv(DATA/'x_unique_text_sensitivity.csv')}; assert len(dedupids)==448
    valid_status=lambda r: bool(r) and not any(w in r.get('status','').lower() for w in ['failure','uncompleted','access denied']) and (r.get('pagination_complete','True')=='True')
    for r in records:
        t=datetime.fromisoformat(r['publication_timestamp'].replace('Z','+00:00')); assert t.tzinfo is not None
        r['_et']=t.astimezone(ET); assert str(r['_et'].date())==r['eastern_date']
    grid=[]; audit=[]; assignment=[]; xsplit=[]
    for idx,d in enumerate(sessions[1:]):
        lo,hi=close(sessions[idx]),close(d); required=[str(x) for x in days(lo.date(),hi.date())]
        row={'session_index':idx,'session_date':str(d),'previous_session_date':str(sessions[idx]),'window_start_exclusive':iso(lo),'window_end_inclusive':iso(hi),'required_calendar_dates':required}
        for channel,key in [('Guardian','guardian'),('X','x')]:
            missing=[x for x in required if not valid_status(coverage[channel].get(x))]
            shortfalls=[x for x in required if channel=='X' and coverage[channel].get(x) and int(coverage[channel][x]['shortfall'])>0]
            group=[r for r in records if r['channel']==channel and lo<r['_et']<=hi]
            rawmean=mean(group); complete=not missing
            available=complete and bool(group)
            row.update({key+'_count':len(group),key+'_raw_window_mean':rawmean,key+'_mean':rawmean if available else None,key+'_collection_coverage_complete':complete,key+'_available':available,key+'_missing_calendar_dates':missing,key+'_sampling_shortfall_dates':shortfalls,key+'_max_timestamp':max((iso(r['_et']) for r in group),default=None)})
            status='available_bounded_sample' if available and channel=='X' else 'available' if available else 'incomplete_collection_window' if missing else 'no_observations_in_sample_window'
            row[key+'_status']=status
            audit.append({'session_date':str(d),'channel':channel,'window_start_exclusive':iso(lo),'window_end_inclusive':iso(hi),'raw_record_count':len(group),'raw_mean_compound':rawmean,'primary_available':available,'status':status,'missing_collection_dates':missing,'sampling_shortfall_dates':shortfalls,'coverage_definition':'Completed collection protocol by intersected calendar date; not exhaustive source/intraday coverage'})
            for r in group:
                assignment.append({'channel':channel,'record_id':r['record_id'],'publication_timestamp':r['publication_timestamp'],'eastern_timestamp':iso(r['_et']),'assigned_session_date':str(d),'assigned_session_index':idx,'primary_window_available':available,'excluded_reason':None if available else status,'kept_in_x_dedup':r['record_id'] in dedupids if channel=='X' else True})
            if channel=='X':
                unique=[r for r in group if r['record_id'] in dedupids]
                row['x_dedup_count']=len(unique); row['x_mean_dedup']=mean(unique) if complete and unique else None
        row['combined_mean']=.5*(row['guardian_mean']+row['x_mean']) if row['guardian_mean'] is not None and row['x_mean'] is not None else None
        row['combined_mean_dedup']=.5*(row['guardian_mean']+row['x_mean_dedup']) if row['guardian_mean'] is not None and row['x_mean_dedup'] is not None else None
        grid.append(row)
    for r in records:
        if r['_et']>close(sessions[-1]): assignment.append({'channel':r['channel'],'record_id':r['record_id'],'publication_timestamp':r['publication_timestamp'],'eastern_timestamp':iso(r['_et']),'assigned_session_date':None,'assigned_session_index':None,'primary_window_available':False,'excluded_reason':'after_final_session_close_no_matching_return','kept_in_x_dedup':r['record_id'] in dedupids if r['channel']=='X' else True})
    assert len(assignment)==len(records) and len({(r['channel'],r['record_id']) for r in assignment})==len(records)
    for d in days(date(2026,9,8),date(2026,9,30)):
        g=[r for r in records if r['channel']=='X' and r['_et'].date()==d]
        pre=[r for r in g if r['_et']<=close(d)]; post=[r for r in g if r['_et']>close(d)]
        xsplit.append({'eastern_date':str(d),'is_trading_session':d in sessions,'x_n':len(g),'at_or_before_16_et_n':len(pre),'after_16_et_n':len(post),'after_16_et_share':len(post)/len(g) if g else None,'note':'16:00 is a clock split only on nontrading days; counts describe the bounded sample, not platform activity'})
    csvwrite(DATA/'aligned_sentiment_sessions.csv',grid); csvwrite(OUT/'sentiment_window_audit.csv',audit); csvwrite(OUT/'record_session_assignment.csv',assignment); csvwrite(OUT/'excluded_records_market_analysis.csv',[r for r in assignment if not r['primary_window_available']]); csvwrite(OUT/'x_time_sampling.csv',xsplit)
    return grid,assignment,audit,xsplit

def regress(grid,spec):
    tests=[]; designs=[]; details={}
    for test in [spec['primary']]+spec['secondary']:
        name=test['name']; L=test['lags']; ykey=test['outcome']; skey=test['sentiment']; usable=[]; excluded=[]
        for i,r in enumerate(grid):
            reason=None
            if i<L: reason='insufficient_previous_grid_sessions'
            elif any(grid[i-j][ykey] is None for j in range(L+1)): reason='missing_outcome_or_return_lag'
            elif any(grid[i-j]['delta_'+skey] is None for j in range(1,L+1)): reason='missing_adjacent_sentiment_change_lag'
            if reason:
                excluded.append({'session_date':r['session_date'],'reason':reason}); designs.append({'test':name,'session_date':r['session_date'],'usable':False,'exclusion_reason':reason}); continue
            y=r[ykey]; rlags=[grid[i-j][ykey] for j in range(1,L+1)]; slags=[grid[i-j]['delta_'+skey] for j in range(1,L+1)]
            for j in range(1,L+1):
                a,b=grid[i-j],grid[i-j-1]
                assert a['session_index']==b['session_index']+1
                assert math.isclose(a['delta_'+skey],a[skey]-b[skey],abs_tol=1e-12)
                # All text underlying a lagged change must be known by prior close.
                for lagrow in [a,b]:
                    channels=['guardian'] if skey=='guardian_mean' else ['x'] if skey=='x_mean' else ['guardian','x']
                    for channel in channels:
                        assert lagrow[channel+'_collection_coverage_complete']
                        latest=lagrow[channel+'_max_timestamp']
                        if latest: assert datetime.fromisoformat(latest)<=datetime.fromisoformat(r['window_start_exclusive'])
            design={'test':name,'session_date':r['session_date'],'usable':True,'exclusion_reason':None,'outcome':y,**{f'return_lag_{j}':rlags[j-1] for j in range(1,L+1)},**{f'sentiment_change_lag_{j}':slags[j-1] for j in range(1,L+1)},'predictor_latest_possible_timestamp':grid[i-1]['window_end_inclusive']}
            designs.append(design); usable.append((r['session_date'],y,[1.]+rlags,[1.]+rlags+slags))
        base={'test':name,'outcome':ykey,'sentiment_series':skey,'lags':L,'n':len(usable),'usable_dates':[x[0] for x in usable],'residual_df_unrestricted':len(usable)-(1+2*L),'residual_df_restricted':len(usable)-(1+L),'joint_numerator_df':L,'p_values_adjustment':'none; exploratory comparisons','status':'pending','fragility':'Very short sample; two-lag sensitivity especially fragile' if L==2 else 'Very short sample and measurement error'}
        try:
            if base['residual_df_unrestricted']<=0: raise ValueError('No positive residual degrees of freedom')
            y=np.array([x[1] for x in usable]); xr=np.array([x[2] for x in usable]); xu=np.array([x[3] for x in usable]); br,_,rankr,_=np.linalg.lstsq(xr,y,rcond=None); bu,_,ranku,_=np.linalg.lstsq(xu,y,rcond=None)
            if rankr!=xr.shape[1] or ranku!=xu.shape[1]: raise ValueError('Rank-deficient design')
            rssr=float(np.dot(y-xr@br,y-xr@br)); rssu=float(np.dot(y-xu@bu,y-xu@bu)); df=len(y)-ranku; q=ranku-rankr
            f=((rssr-rssu)/q)/(rssu/df); p=float(fdistribution.sf(f,q,df))
            sr=OLS(y,xr).fit(); su=OLS(y,xu).fit(); smf,smp,smq=su.compare_f_test(sr)
            R=np.zeros((L,xu.shape[1])); R[:,1+L:]=np.eye(L); joint=su.f_test(R)
            assert np.allclose(bu,su.params,atol=1e-12,rtol=1e-9)
            assert math.isclose(f,float(smf),abs_tol=1e-10,rel_tol=1e-9) and math.isclose(p,float(smp),abs_tol=1e-10,rel_tol=1e-9)
            assert math.isclose(f,float(joint.fvalue),abs_tol=1e-10,rel_tol=1e-9) and math.isclose(p,float(joint.pvalue),abs_tol=1e-10,rel_tol=1e-9) and int(smq)==L
            base.update({'status':'estimated_crosscheck_passed','restricted_rss':rssr,'unrestricted_rss':rssu,'joint_f':f,'p_value':p,'statsmodels_joint_f':float(smf),'statsmodels_p_value':float(smp),'manual_statsmodels_max_coefficient_difference':float(np.max(np.abs(bu-su.params))),'unrestricted_r_squared':float(su.rsquared),'restricted_r_squared':float(sr.rsquared),'design_condition_number':float(np.linalg.cond(xu)),**{f'sentiment_coefficient_lag_{j}':float(bu[L+j]) for j in range(1,L+1)}})
            details[name]={'test':base,'all_coefficients':{'constant':float(bu[0]),**{f'return_lag_{j}':float(bu[j]) for j in range(1,L+1)},**{f'sentiment_change_lag_{j}':float(bu[L+j]) for j in range(1,L+1)}},'sentiment_coefficient_units':'Decimal outcome return per 1-unit increase in lagged VADER compound change','excluded_sessions':excluded,'residuals':[{ 'session_date':x[0],'unrestricted_residual':float(e),'restricted_residual':float(er)} for x,e,er in zip(usable,y-xu@bu,y-xr@br)]}
        except Exception as e:
            base.update({'status':'failed_or_not_estimable','error':type(e).__name__+': '+str(e),'joint_f':None,'p_value':None}); details[name]={'test':base,'excluded_sessions':excluded}
        tests.append(base)
    csvwrite(OUT/'granger_exploratory_tests.csv',tests); csvwrite(OUT/'regression_design_audit.csv',designs); dump(OUT/'granger_test_details.json',details)
    return tests

def correlations(grid):
    rows=[]
    for series in ['guardian_mean','x_mean','combined_mean','combined_mean_dedup']:
        for transform in ['level','change']:
            key=series if transform=='level' else 'delta_'+series
            for outcome in ['basket_return','spread_return']:
                for h in [0,1]:
                    pairs=[(r[key],grid[i+h][outcome],r['session_date'],grid[i+h]['session_date']) for i,r in enumerate(grid) if i+h<len(grid) and r[key] is not None and grid[i+h][outcome] is not None]
                    value=float(np.corrcoef([x[0] for x in pairs],[x[1] for x in pairs])[0,1]) if len(pairs)>2 and np.std([x[0] for x in pairs])>0 and np.std([x[1] for x in pairs])>0 else None
                    rows.append({'sentiment_series':series,'transform':transform,'outcome':outcome,'relationship':'contemporaneous_association' if h==0 else 'next_session_association_not_forecast_validation','horizon_sessions':h,'n':len(pairs),'pearson_r':value,'sentiment_dates':[x[2] for x in pairs],'return_dates':[x[3] for x in pairs],'inference':'descriptive only; no p-value; no controls'})
    csvwrite(OUT/'descriptive_correlations.csv',rows); return rows

def figures(panel,grid):
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(11,5))
    for key,label,color in [('basket_cumulative_return','Equal-weight AI basket','#176a9a'),('spy_cumulative_return','SPY','#bd542c')]: ax.plot([date.fromisoformat(r['session_date']) for r in panel],[100*r[key] for r in panel],marker='o',markersize=4,label=label,color=color)
    ax.axhline(0,color='#666',lw=.8); ax.set_ylabel('Compounded adjusted-price return (%)'); ax.set_title('Cached adjusted-price performance\nSeptember 4 close–September 30, 2026 (year provisional)',loc='left'); ax.legend(); ax.grid(axis='y',alpha=.2); ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d')); ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    fig.text(.08,.025,'Basket: NVDA, MSFT, GOOGL, AMZN, META • 20% weights, daily rebalancing • Vendor adjustments not independently rebuilt.',fontsize=9); fig.tight_layout(rect=(0,.06,1,1)); fig.savefig(OUT/'m4_cumulative_returns.png',dpi=180); fig.savefig(OUT/'m4_cumulative_returns.svg'); plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(11,7),sharex=True,gridspec_kw={'height_ratios':[3,1]})
    for key,label,color in [('guardian_mean','Guardian','#176a9a'),('x_mean','X','#bd542c'),('combined_mean','Combined (half each)','#4c8058')]: axes[0].plot([date.fromisoformat(r['session_date']) for r in grid],[r[key] if r[key] is not None else np.nan for r in grid],marker='o',markersize=4,label=label,color=color)
    axes[0].axhline(0,color='#666',lw=.8); axes[0].set_ylabel('Mean VADER compound'); axes[0].set_title('Text sentiment aligned to market-session closes\nSeptember 8–30, 2026 (year provisional)',loc='left'); axes[0].legend(ncol=3,fontsize=10); axes[0].grid(axis='y',alpha=.2)
    ds=[date.fromisoformat(r['session_date']) for r in grid]
    for k,label,color in [('guardian_count','Guardian window n','#176a9a'),('x_count','X window n','#bd542c')]: axes[1].plot(ds,[r[k] if r[k.replace('count','available')] else np.nan for r in grid],marker='o',markersize=3,color=color,label=label)
    axes[1].set_ylabel('Sample n'); axes[1].legend(ncol=2,fontsize=9); axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%b %d')); axes[1].xaxis.set_major_locator(mdates.DayLocator(interval=2)); axes[1].grid(axis='y',alpha=.2)
    for ax in axes: ax.axvspan(datetime(2026,9,7,18),datetime(2026,9,8,18),color='#999',alpha=.15)
    fig.text(.08,.018,'Windows: (previous close, current close], Eastern time; weekend content included. Sep 8 unavailable (incomplete collection).\nUnsmoothed values • X: bounded search sample • Generic sentiment, weak validation; not validated AI attitudes.',fontsize=9)
    fig.tight_layout(rect=(0,.075,1,1)); fig.savefig(OUT/'m4_aligned_sentiment.png',dpi=180); fig.savefig(OUT/'m4_aligned_sentiment.svg'); plt.close(fig)

def document(summary,tests,corr):
    primary=tests[0]; table='\n'.join(f"| {r['test']} | {r['n']} | {r['residual_df_unrestricted']} | {statsfmt(r.get('sentiment_coefficient_lag_1'))} | {statsfmt(r.get('sentiment_coefficient_lag_2'))} | {statsfmt(r.get('joint_f'))} | {statsfmt(r.get('p_value'))} | {r['status']} |" for r in tests)
    cr={(r['transform'],r['horizon_sessions']):r['pearson_r'] for r in corr if r['sentiment_series']=='combined_mean' and r['outcome']=='basket_return'}
    memo=f'''# Milestone 4 findings memo — exploratory, not final report

The specification was frozen in milestone4_spec.json before return/regression results were calculated. Only cached prices and existing record-level compound scores were used. The original assignment screenshot/methodological PDFs remain unavailable; 2026 is provisional. X is a bounded Latest-search sample, not representative public opinion. These are exploratory text-sentiment measures, not validated AI attitudes.

## Returns and alignment

The daily-rebalanced, equal-weight five-company basket compounded to {pct(summary['returns']['basket_cumulative_return'])}; SPY to {pct(summary['returns']['spy_cumulative_return'])}, from September 4 close through September 30. Their cumulative performance difference is {100*summary['returns']['cumulative_performance_difference']:.2f} percentage points. Individual returns use vendor-adjusted close ratios; cached dividends/splits were audited in Milestone 2 but adjustments are not independently reconstructed. No price imputation.

Seventeen return sessions are retained. Sentiment windows are (previous session close, current session close], with Eastern 16:00 closes and intervening weekend text included. September 8 is unavailable for primary sentiment because September 4–7 collection is absent; its observed September 8 texts are preserved in the exclusion audit. {summary['coverage']['after_final_close_exclusions']} records after September 30 close have no study return session. Completeness means intersected calendar dates have completed the frozen collection protocol, not complete platform/intraday coverage. X's September 14/16 daily shortfalls (19/20) remain flagged observed bounded samples. Empty channel windows would have missing means, not zero.

{summary['coverage']['combined_available_sessions']} combined windows are available. X clock-split counts: {summary['coverage']['x_at_or_before_16_count']} at/before 16:00 and {summary['coverage']['x_after_16_count']} after 16:00 across all study dates; nontrading days use this only as a clock split. The strong imbalance is a consequence of capped Latest sampling and can shift apparent information timing. Counts are not total discussion volume. The 448-record exact-text sensitivity uses identical timestamp assignment and session grid.

## Frozen regressions

Primary: basket return_t = constant + basket return_(t−1) + Δcombined sentiment_(t−1). Changes use adjacent valid trading sessions only. The full grid is shifted before eligibility filtering; missing rows never make nonadjacent sessions consecutive. All text in predictors is timestamped at or before the previous session close. One-lag coefficients are decimal-return changes per 1-unit change in lagged compound sentiment.

| Test | n | Unrestricted residual df | Sentiment lag 1 | Sentiment lag 2 | Joint F | Unadjusted p | Status |
|---|---:|---:|---:|---:|---:|---:|---|
{table}

All six planned tests were attempted, with usable dates, exclusions, coefficients, RSS and residuals saved. Successful manual least-squares/RSS F calculations match statsmodels OLS compare_f_test and joint f_test. The two-lag model restricts both sentiment coefficients jointly and retains the same two return lags in both nested models; its F test has no single coefficient sign. No alternative lags, baskets or scoring variants were searched.

Primary result: n={primary['n']}, sentiment-change coefficient {statsfmt(primary.get('sentiment_coefficient_lag_1'))}, F={statsfmt(primary.get('joint_f'))}, p={statsfmt(primary.get('p_value'))}. These are in-sample incremental-predictability tests, not out-of-sample forecast validation. P-values are unadjusted across six exploratory comparisons. Conventional F inference assumes appropriate regression errors; homoskedasticity/serial independence and stationarity have not been established with this short series. No stationarity claim is made and no significance implies causation.

## Description and limitations

The saved correlation table separates same-session associations from sentiment_t versus return_(t+1), for levels and changes, basket and spread. Combined sentiment level correlations with basket returns are {statsfmt(cr['level',0])} contemporaneously and {statsfmt(cr['level',1])} for the next session. Combined sentiment-change correlations are {statsfmt(cr['change',0])} contemporaneously and {statsfmt(cr['change',1])} for the next session. Correlations have no controls or inferential p-values. They are not the nested-regression test. The return and sentiment figures use unsmoothed values and retain the incomplete first window. The test p-values offer no compelling evidence of incremental prediction in this small sample; this does not establish absence of a relationship. Two-lag coefficient signs differ from the one-lag estimate, illustrating specification fragility rather than a directional conclusion from the joint F statistic.

General sentiment validation was weak: Codex agreement 50% Guardian and 75% X on 20 records/channel; framing agreement 60%/65%. There were no independent human labels. Negation, quotations, sarcasm, implicit framing, company-directed criticism and unrelated emotional language cause errors. Framing was not used as a new predictor. Measurement error, daily caps, query bias, small channel window counts, the short sample and provisional year materially limit interpretation. Statistical associations cannot establish genuine AI attitudes or channel bias.

Ready to assemble a cautious 5–6-page Milestone 5 report from these saved artifacts, with authoritative assignment/year evidence still unresolved. No final report has been written.
'''
    (OUT/'milestone4_findings.md').write_text(memo,encoding='utf-8')
    readme='''# Milestone 4 — cached returns and session-aligned sentiment

Run in PowerShell from `D:\\School Work\\FRE-GY 7871 NLP\\Assignment 4`:

```powershell
& 'C:\\Users\\fangyi\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' .\\src\\milestone4.py
& 'C:\\Users\\fangyi\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' .\\src\\verify_m4.py
```

This script uses only cached market_panel.csv, scored_records.jsonl, the 448-ID sensitivity corpus and saved coverage audits. It does not import or run Milestone 3 scoring, collect data, access credentials, or call inference APIs. Project-local statsmodels/scipy/patsy provide the regression cross-check; versions are recorded in outputs/milestone4_summary.json. Existing NumPy/pandas/matplotlib are reused.

Specification and hash: milestone4_spec.json and outputs/milestone4_spec_sha256.txt. The script refuses a changed spec hash. Do not add lags or variants based on p-values. Full input hashes are checked before/after running in milestone4_integrity.json.

Data: data/processed/individual_returns.csv, return_panel.csv, aligned_sentiment_sessions.csv and analysis_session_grid.csv. Return panel includes September 4 baseline, individual/company/basket/SPY/spread simple returns and compounded performance. Synthetic compounded spread is separately labeled; cumulative basket-minus-SPY performance difference is also saved. The 17-row analysis grid retains the unavailable September 8 sentiment and all session indices.

Audits: outputs/sentiment_window_audit.csv, record_session_assignment.csv, excluded_records_market_analysis.csv, x_time_sampling.csv and regression_design_audit.csv. Dates, boundary inclusion, original timestamps and no-future-text checks are explicit. Complete collection means every intersected Eastern calendar date completed the frozen source protocol, with capped X sampling and 19/20 shortfalls flagged; it does not mean exhaustive historical coverage. Empty sample windows retain missing means.

Results: outputs/return_summary.json, descriptive_correlations.csv, granger_exploratory_tests.csv, granger_test_details.json, milestone4_summary.json and milestone4_findings.md. Coefficients use decimal return per unit of compound change. Joint F tests compare nested models with identical usable dates. P-values are conventional and unadjusted; no out-of-sample validation or stationarity claim.

Figures: outputs/m4_cumulative_returns.png/svg and m4_aligned_sentiment.png/svg. Year remains provisional; X is a bounded search sample; measures have weak validation. Ready for cautious Milestone 5 drafting, subject to assignment/year confirmation. Stop before final report writing.
'''
    (ROOT/'MILESTONE4_README.md').write_text(readme,encoding='utf-8')
    memo_path=OUT/'milestone4_findings.md'
    with memo_path.open('a',encoding='utf-8') as f:
        f.write('\nCalendar and test-method references: [NYSE trading hours and holiday calendar](https://www.nyse.com/trade/hours-calendars); [statsmodels nested-model F-test documentation](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.compare_f_test.html). These reference checks fetched no prices or text and did not recollect data.\n')
    for name in ['README.md','analysis_plan.md']:
        p=ROOT/name; t=p.read_text(encoding='utf-8'); marker='\n## Milestone 4 completed\n'
        if marker in t: t=t.split(marker)[0]
        p.write_text(t+marker+f"Cached adjusted returns and timestamp-aligned sentiment completed under frozen milestone4_spec.json. Basket cumulative return {pct(summary['returns']['basket_cumulative_return'])}; SPY {pct(summary['returns']['spy_cumulative_return'])}. Primary one-lag change model: n={primary['n']}, coefficient={statsfmt(primary.get('sentiment_coefficient_lag_1'))}, F={statsfmt(primary.get('joint_f'))}, unadjusted p={statsfmt(primary.get('p_value'))}. Six planned tests and manual/statsmodels cross-checks saved; full session grid retained. September 8 sentiment is unavailable due to uncollected September 4–7; text after final close excluded. Read MILESTONE4_README.md and outputs/milestone4_findings.md. Generic text sentiment, weak validation, bounded X sampling, unadjusted exploratory comparisons and provisional 2026 remain material caveats. Ready for cautious Milestone 5 drafting with assignment/year verification unresolved; no final report written.\n",encoding='utf-8')

def main():
    specpath=ROOT/'milestone4_spec.json'; spec=json.loads(specpath.read_text(encoding='utf-8')); specsha=hashfile(specpath)
    assert specsha.upper()==(OUT/'milestone4_spec_sha256.txt').read_text(encoding='utf-8-sig').strip().upper(),'Frozen specification hash changed'
    inputs=[DATA/'market_panel.csv',DATA/'scored_records.jsonl',DATA/'x_unique_text_sensitivity.csv',OUT/'guardian_daily_coverage.csv',OUT/'x_daily_coverage.csv',OUT/'milestone2_summary.json',OUT/'milestone3_summary.json',OUT/'scoring_method.json']
    before={str(p.relative_to(ROOT)):hashfile(p) for p in inputs}
    sessions,panel,rs=returns(); records=[json.loads(x) for x in (DATA/'scored_records.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]; assert len(records)==644
    grid,assignment,audit,xsplit=align(sessions,records)
    for i,row in enumerate(grid):
        row.update({k:v for k,v in panel[i+1].items() if k not in ['session_date','previous_session_date']})
        for skey in ['guardian_mean','x_mean','combined_mean','combined_mean_dedup']:
            prev=grid[i-1][skey] if i else None
            row['delta_'+skey]=row[skey]-prev if i and row[skey] is not None and prev is not None else None
            row['lag1_delta_'+skey]=grid[i-1]['delta_'+skey] if i else None
        row['lag1_basket_return']=grid[i-1]['basket_return'] if i else None
    assert len(grid)==17 and grid[0]['combined_mean'] is None
    csvwrite(DATA/'analysis_session_grid.csv',grid)
    tests=regress(grid,spec); corr=correlations(grid); figures(panel,grid)
    coverage={'combined_available_sessions':sum(r['combined_mean'] is not None for r in grid),'guardian_available_sessions':sum(r['guardian_mean'] is not None for r in grid),'x_available_sessions':sum(r['x_mean'] is not None for r in grid),'incomplete_first_window':'2026-09-08: uncollected September 4–7','after_final_close_exclusions':sum(r['excluded_reason']=='after_final_session_close_no_matching_return' for r in assignment),'after_final_close_by_channel':{c:sum(r['channel']==c and r['excluded_reason']=='after_final_session_close_no_matching_return' for r in assignment) for c in ['Guardian','X']},'incomplete_window_excluded_records':sum(r['excluded_reason']=='incomplete_collection_window' for r in assignment),'x_at_or_before_16_count':sum(r['at_or_before_16_et_n'] for r in xsplit),'x_after_16_count':sum(r['after_16_et_n'] for r in xsplit),'channel_available_count_ranges':{c:[min(r[c+'_count'] for r in grid if r[c+'_available']),max(r[c+'_count'] for r in grid if r[c+'_available'])] for c in ['guardian','x']},'x_shortfall_dates':['2026-09-14','2026-09-16'],'coverage_note':spec['coverage']}
    packages={p:importlib.metadata.version(p) for p in ['numpy','scipy','statsmodels','patsy','matplotlib']}
    summary={'spec_sha256':specsha,'year_status':'2026 provisional','returns':rs,'coverage':coverage,'tests':tests,'packages':packages,'p_value_adjustment':'none; six exploratory comparisons','score_caveat':'text sentiment in AI-related material, not validated AI attitudes; weak Codex agreement and no independent human labels','x_caveat':'bounded Latest-search sample, not representative public opinion','readiness':'Milestone 4 complete; cautious 5–6-page final report can be drafted next, assignment/year confirmation unresolved','final_report_written':False}
    dump(OUT/'milestone4_summary.json',summary); document(summary,tests,corr)
    after={str(p.relative_to(ROOT)):hashfile(p) for p in inputs}; assert before==after
    integrity={'input_hashes_before':before,'input_hashes_after':after,'unchanged_inputs':before==after,'spec_sha256':specsha,'checks':{'complete_price_grid':True,'simple_return_compounding':True,'equal_weight_daily_basket':True,'session_grid_retained':True,'timestamp_window_matching':True,'no_future_text_in_predictors':True,'lag_changes_adjacent_sessions_only':True,'dedup_same_alignment':True,'missing_not_zero':True,'manual_statsmodels_crosscheck_all_successful_tests':all(t['status']=='estimated_crosscheck_passed' for t in tests)},'attempted_tests':len(tests),'failures':[r['test'] for r in tests if r['status']!='estimated_crosscheck_passed']}
    dump(OUT/'milestone4_integrity.json',integrity)
    print(json.dumps({'basket_cumulative':rs['basket_cumulative_return'],'spy_cumulative':rs['spy_cumulative_return'],'available_combined_windows':coverage['combined_available_sessions'],'excluded_after_final_close':coverage['after_final_close_exclusions'],'tests':[{k:r.get(k) for k in ['test','n','residual_df_unrestricted','sentiment_coefficient_lag_1','sentiment_coefficient_lag_2','joint_f','p_value','status']} for r in tests],'inputs_unchanged':True}))
if __name__=='__main__': main()
