"""Independent integrity checks; no extra specifications or statistical tests."""
import csv,json,math,hashlib
from pathlib import Path
from datetime import datetime,time,date,timedelta
from zoneinfo import ZoneInfo
R=Path(__file__).resolve().parents[1]; D=R/'data'/'processed'; O=R/'outputs'; ET=ZoneInfo('America/New_York')
def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
price={(x['symbol'],x['date']):float(x['adjusted_close']) for x in read(D/'market_panel.csv')}
ind=read(D/'individual_returns.csv'); panel=read(D/'return_panel.csv'); aligned=read(D/'analysis_session_grid.csv'); assignments=read(O/'record_session_assignment.csv'); design=read(O/'regression_design_audit.csv'); tests=read(O/'granger_exploratory_tests.csv')
records=[json.loads(x) for x in (D/'scored_records.jsonl').read_text(encoding='utf-8').splitlines()]; lookup={(r['channel'],r['record_id']):r for r in records}
ids={r['post_id'] for r in read(D/'x_unique_text_sensitivity.csv')}
assert len(panel)==18 and len(aligned)==17 and len(ind)==108
assert panel[0]['session_date']=='2026-09-04' and panel[1]['previous_session_date']=='2026-09-04' and panel[1]['session_date']=='2026-09-08'
growth=1.; spy=1.
for row in panel[1:]:
    company=[price[s,row['session_date']]/price[s,row['previous_session_date']]-1 for s in ['NVDA','MSFT','GOOGL','AMZN','META']]
    r=sum(company)/5; benchmark=price['SPY',row['session_date']]/price['SPY',row['previous_session_date']]-1
    assert math.isclose(r,float(row['basket_return']),abs_tol=1e-12)
    assert math.isclose(benchmark,float(row['spy_return']),abs_tol=1e-12)
    assert math.isclose(r-benchmark,float(row['spread_return']),abs_tol=1e-12)
    growth*=1+r; spy*=1+benchmark
    assert math.isclose(growth-1,float(row['basket_cumulative_return']),abs_tol=1e-12) and math.isclose(spy-1,float(row['spy_cumulative_return']),abs_tol=1e-12)
assignment={(r['channel'],r['record_id']):r for r in assignments}; assert len(assignment)==len(records)
for key,r in lookup.items():
    t=datetime.fromisoformat(r['publication_timestamp'].replace('Z','+00:00')).astimezone(ET); a=assignment[key]
    if a['assigned_session_date']:
        w=next(x for x in aligned if x['session_date']==a['assigned_session_date'])
        assert datetime.fromisoformat(w['window_start_exclusive'])<t<=datetime.fromisoformat(w['window_end_inclusive'])
    else: assert t>datetime(2026,9,30,16,tzinfo=ET)
for row in aligned:
    for channel,key in [('Guardian','guardian'),('X','x')]:
        group=[lookup[(a['channel'],a['record_id'])] for a in assignments if a['assigned_session_date']==row['session_date'] and a['channel']==channel]
        assert len(group)==int(row[key+'_count'])
        if row[key+'_mean']:
            assert math.isclose(sum(r['compound'] for r in group)/len(group),float(row[key+'_mean']),abs_tol=1e-12)
        else: assert row['session_date']=='2026-09-08'
        if channel=='X':
            subset=[r for r in group if r['record_id'] in ids]; assert len(subset)==int(row['x_dedup_count'])
            if row['x_mean_dedup']: assert math.isclose(sum(r['compound'] for r in subset)/len(subset),float(row['x_mean_dedup']),abs_tol=1e-12)
    if row['combined_mean']:
        assert math.isclose(float(row['combined_mean']),.5*(float(row['guardian_mean'])+float(row['x_mean'])),abs_tol=1e-12)
    i=int(row['session_index'])
    for series in ['guardian_mean','x_mean','combined_mean','combined_mean_dedup']:
        value=row['delta_'+series]
        if value:
            assert i>0 and row[series] and aligned[i-1][series]
            assert math.isclose(float(value),float(row[series])-float(aligned[i-1][series]),abs_tol=1e-12)
for r in design:
    if r['usable']=='True':
        row=next(x for x in aligned if x['session_date']==r['session_date']); i=int(row['session_index'])
        assert datetime.fromisoformat(r['predictor_latest_possible_timestamp'])<=datetime.fromisoformat(row['window_start_exclusive'])
        test=next(x for x in tests if x['test']==r['test']); skey=test['sentiment_series']; L=int(test['lags'])
        for lag in range(1,L+1):
            assert int(aligned[i-lag]['session_index'])==i-lag
            assert aligned[i-lag]['delta_'+skey]
            assert math.isclose(float(r['sentiment_change_lag_'+str(lag)]),float(aligned[i-lag]['delta_'+skey]),abs_tol=1e-12)
for r in tests:
    used=[d for d in design if d['test']==r['test'] and d['usable']=='True']; assert len(used)==int(r['n'])
    assert [d['session_date'] for d in used]==json.loads(r['usable_dates'])
    assert int(r['residual_df_unrestricted'])==int(r['n'])-(1+2*int(r['lags']))
integrity=json.loads((O/'milestone4_integrity.json').read_text(encoding='utf-8'))
assert all(hashlib.sha256((R/k).read_bytes()).hexdigest()==v for k,v in integrity['input_hashes_before'].items())
integrity['independent_output_checks']={'return_ratios_compounding':True,'all_original_timestamp_assignments':True,'window_means_and_counts':True,'dedup_ids_means':True,'full_grid_adjacent_delta_and_lag_values':True,'predictor_availability_before_target_window':True,'test_dates_and_degrees_of_freedom':True,'existing_inputs_unchanged':True}
(O/'milestone4_integrity.json').write_text(json.dumps(integrity,indent=2),encoding='utf-8')
print('Independent arithmetic, timestamp, adjacency, sensitivity and input-preservation checks passed.')
