import json,csv,datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
P=Path(r'D:\School Work\FRE-GY 7871 NLP\Assignment 4')
rows=[json.loads(l) for l in (P/'data/processed/x_browser_pilot.jsonl').read_text(encoding='utf-8').splitlines() if l]
counts=[]
for date in ['2026-09-08','2026-09-19','2026-09-30']:
 r=[x for x in rows if x['sample_date']==date]
 counts.append(dict(date=date,qualified_posts=len(r),text_complete=sum(bool(x['text']) and not x['text_truncated'] for x in r),timestamp_complete=sum(bool(x['publication_timestamp']) for x in r),author_status_matched=sum(x['matching_header'] for x in r),actual_eastern_day_matches=sum(dt.datetime.fromisoformat(x['publication_timestamp'].replace('Z','+00:00')).astimezone(ZoneInfo('America/New_York')).date().isoformat()==date for x in r),adjacent_utc_day_posts=sum(x['utc_timestamp'][:10]!=date for x in r)))
with (P/'outputs/x_date_debug_counts.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=list(counts[0]));w.writeheader();w.writerows(counts)
checks=json.loads((P/'outputs/x_fixed_original_checks.json').read_text())
assert len(rows)==len({r['post_id'] for r in rows}), 'duplicate IDs'
assert all(c['own_timestamp_match'] and c['author_match'] and c['text_match'] for c in checks), 'original match unverified'
assert all(c['qualified_posts']==10 and c['text_complete']==10 and c['actual_eastern_day_matches']==10 for c in counts)
audit=dict(platform='X',route='authenticated Latest; corrected date endpoints and Eastern validator',status='success: bounded qualified pilot',date_coverage_tested='2026-09-08;2026-09-19;2026-09-30 provisional',text_availability='30 complete original texts',timestamp_availability='30 machine-readable timestamps; original/UTC/Eastern preserved',limitations='10/date; three originals matched; no full archive or representativeness guarantee; assignment year provisional')
with (P/'social_access_audit.csv').open('a',newline='',encoding='utf-8-sig') as f:csv.DictWriter(f,fieldnames=list(audit)).writerow(audit)
print(json.dumps({'date_counts':counts,'original_checks':checks,'dedup_pass':True},indent=2))
