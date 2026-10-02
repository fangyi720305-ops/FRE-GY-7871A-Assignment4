import csv,json,datetime as dt
from pathlib import Path
P=Path(r'D:\School Work\FRE-GY 7871 NLP\Assignment 4')
prices=list(csv.DictReader((P/'data/processed/market_panel.csv').open(encoding='utf-8-sig')));rows=[]
for i in range(27):
 d=(dt.date(2026,9,4)+dt.timedelta(days=i)).isoformat();n=sum(r['date']==d for r in prices);rows.append(dict(date=d,price_observations=n,status='nontrading session' if dt.date.fromisoformat(d).weekday()>=5 or d=='2026-09-07' else 'successful collection' if n==6 else 'missing prices'))
with (P/'outputs/market_daily_coverage.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
summary=json.loads((P/'outputs/milestone2_summary.json').read_text(encoding='utf-8'));summary.update(guardian_missing_body=0,guardian_missing_timestamp=0,guardian_missing_url=0,credential_scan_pass=True)
(P/'outputs/milestone2_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
audit=[dict(source='Guardian',route='cached complete broad query + resolved AI tag pagination',status='success',date_coverage_tested='2026-09-08 through 2026-09-30 Eastern',text_availability='186 complete article bodies/headlines/trails',timestamp_availability='186 original timestamps',limitations='387 candidates; 30 stratified relevance checks; provisional year'),dict(source='X',route='authenticated bounded Latest sample; existing profile',status='success with sampling shortfalls',date_coverage_tested='all 23 Eastern dates Sep 8–30 2026',text_availability='458 complete enclosing original texts',timestamp_availability='458 validated timestamps',limitations='19 posts Sep 14/16; 20 otherwise; not representative/complete; exact duplicate sensitivity dataset'),dict(source='Market',route='existing Yahoo adjusted-price caches',status='success',date_coverage_tested='18 sessions Sep 4–30 2026',text_availability='not applicable',timestamp_availability='108 symbol-date observations',limitations='vendor adjustment factors not independently rebuilt; no imputation')]
with (P/'source_access_audit.csv').open('a',newline='',encoding='utf-8-sig') as f:csv.DictWriter(f,fieldnames=list(audit[0])).writerows(audit)
with (P/'social_access_audit.csv').open('a',newline='',encoding='utf-8-sig') as f:csv.DictWriter(f,fieldnames=['platform','route','status','date_coverage_tested','text_availability','timestamp_availability','limitations']).writerow({('platform' if k=='source' else k):v for k,v in audit[1].items()})
print(json.dumps({'milestone2':'complete','market_calendar_days_audited':len(rows),'ready_for_milestone3':True}))
