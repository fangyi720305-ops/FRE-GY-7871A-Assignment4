"""Local manual capture of visible X posts. No passwords/cookies/network calls."""
import csv,json,re,datetime as dt,webbrowser,argparse
from pathlib import Path
P=Path(__file__).resolve().parents[1]; OUT=P/'data/processed';OUT.mkdir(parents=True,exist_ok=True)
BASE='("artificial intelligence" OR "generative AI" OR Anthropic) lang:en -filter:retweets'
DATES=['2026-09-08','2026-09-19','2026-09-30']
def main():
 p=argparse.ArgumentParser();p.add_argument('--date',choices=DATES,required=True);args=p.parse_args(); date=args.date
 end=date;query=BASE+' since:'+date+' until:'+end
 from urllib.parse import urlencode
 print('Use the dedicated X browser profile. Paste this URL in its address bar:')
 print('https://x.com/search?'+urlencode({'q':query,'f':'live'}));print('Select Latest. Capture first 10 eligible English posts in displayed order, skipping duplicates. No cherry-picking.')
 file=OUT/'x_manual_pilot.jsonl';rows=[json.loads(l) for l in file.read_text(encoding='utf-8').splitlines() if l] if file.exists() else []
 seen={r['post_id'] for r in rows};qualified=sum(r['sample_date']==date for r in rows)
 while qualified<10:
  url=input('Original post URL (blank to stop): ').strip()
  if not url:break
  match=re.match(r'^https://(?:www\.)?(?:x|twitter)\.com/([^/]+)/status/(\d+)(?:[/?].*)?$',url)
  if not match:print('Use an original handle/status/ID URL.');continue
  handle,id=match.groups()
  if id in seen:print('Already saved.');continue
  stamp=input('Actual full publication timestamp with timezone (ISO 8601; do not infer from filter): ').strip()
  try:
   timestamp=dt.datetime.fromisoformat(stamp.replace('Z','+00:00'))
   from zoneinfo import ZoneInfo
   assert timestamp.tzinfo is not None and timestamp.astimezone(ZoneInfo('America/New_York')).date().isoformat()==date
  except Exception:print('Exact timezone-aware timestamp in requested Eastern day required.');continue
  if input('Is full enclosing-post text visible and English? [yes/no]: ').strip().lower()!='yes':print('Skipped incomplete/non-English post.');continue
  print('Paste full enclosing-post text only; finish with a line containing END. Exclude quote text.')
  lines=[]
  while True:
   line=input()
   if line=='END':break
   lines.append(line)
  text='\n'.join(lines).strip()
  if not text:continue
  try:order=int(input('Displayed result order (positive integer): '));assert order>0
  except Exception:print('Invalid order; record not saved.');continue
  quote=input('Quoted original status URL if visible (blank if none/unknown): ').strip()
  r=dict(platform='X',post_id=id,author_handle=handle,author_identifier=handle,original_url=f'https://x.com/{handle}/status/{id}',text=text,publication_timestamp=timestamp.astimezone(dt.timezone.utc).isoformat(),query=query,retrieved_at=dt.datetime.now(dt.timezone.utc).isoformat(),result_order=order,sample_date=date,text_truncated=False,quote_relationships=[{'status_url':quote,'relationship':'quoted post'}] if quote else [],retrieval_method='manual visible-post capture from dedicated logged-in X Latest search',window_status='provisional 2026',language_status='manually confirmed English',record_type='post')
  rows.append(r);seen.add(id);qualified+=1
  with file.open('a',encoding='utf-8') as f:f.write(json.dumps(r,ensure_ascii=False)+'\n')
  with (OUT/'x_manual_pilot.csv').open('w',newline='',encoding='utf-8-sig') as f:
   w=csv.DictWriter(f,fieldnames=list(r));w.writeheader();w.writerows({**x,'quote_relationships':json.dumps(x['quote_relationships'])} for x in rows)
  print(f'Saved. {qualified}/10 on {date}.')
if __name__=='__main__':main()
