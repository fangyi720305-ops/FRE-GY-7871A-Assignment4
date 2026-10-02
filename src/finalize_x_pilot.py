import csv,json,datetime as dt,re
from pathlib import Path
P=Path(r'D:\School Work\FRE-GY 7871 NLP\Assignment 4')
status=json.loads((P/'outputs/x_browser_status.json').read_text(encoding='utf-8'))
f=P/'data/processed/x_boundary_examples.jsonl';rows=[json.loads(l) for l in f.read_text(encoding='utf-8').splitlines() if l.strip()]
orders={}
for r in rows:
 m=re.search(r'x.com/([^/]+)/status/(\d+)',r['original_url']);r['author_handle']=m[1];r['author_identifier']=m[1];r['post_id']=m[2]
 r['id_encoded_timestamp']=dt.datetime.fromtimestamp(((int(m[2])>>22)+1288834974657)/1000,dt.timezone.utc).isoformat()
 r['sample_date']=r['requested_date'];r['record_type']='post';r['window_status']='provisional 2026';r['quote_relationships_status']='not fully extracted in diagnostic; do not treat quote text as enclosing text'
 orders[r['requested_date']]=orders.get(r['requested_date'],0)+1;r['result_order']=orders[r['requested_date']]
 r['boundary_status']='outside requested UTC and Eastern calendar date';r['eligible_for_analysis']=False
f.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
with (P/'data/processed/x_boundary_examples.csv').open('w',newline='',encoding='utf-8-sig') as file:
 w=csv.DictWriter(file,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
counts=[]
for a in status['audit']:
 dates=a['date'];d=[r for r in rows if r['requested_date']==dates]
 counts.append(dict(date=dates,qualified_posts=a['qualified'],qualified_text_complete=0,qualified_timestamp_complete=0,excluded_timestamp_encounters=a['outside_requested_UTC_date'],cached_unique_boundary_examples=len(d),boundary_example_text_present=sum(bool(r['text']) for r in d),boundary_example_timestamp_present=sum(bool(r['publication_timestamp']) for r in d),boundary_example_truncated=sum(r['text_truncated'] for r in d),status='Latest search visible; no eligible posts within bounded pilot'))
with (P/'outputs/x_browser_pilot_counts.csv').open('w',newline='',encoding='utf-8-sig') as file:
 w=csv.DictWriter(file,fieldnames=list(counts[0]));w.writeheader();w.writerows(counts)
audit=dict(platform='X',route='logged-in Chrome dedicated profile; Playwright visible Latest searches',status='authenticated search and DOM extraction work; requested date samples not obtained',date_coverage_tested='2026-09-08;2026-09-19;2026-09-30 (provisional)',text_availability='6 out-of-window original text examples cached; 0 qualified in-date records',timestamp_availability='6 machine-readable timestamps; corroborated by status ID creation times',limitations='Date-filter mismatch; encounter counts may include repeat visibility during scrolling; no archive coverage claim; original-detail timestamps may belong to quotes, not enclosing post')
with (P/'social_access_audit.csv').open('a',newline='',encoding='utf-8-sig') as file:csv.DictWriter(file,fieldnames=list(audit)).writerow(audit)
print(json.dumps({'counts':counts,'complete_in_window':0,'cached_outside_window':len(rows)},indent=2))
