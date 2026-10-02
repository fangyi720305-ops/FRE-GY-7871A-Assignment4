"""Local validation/coverage only: no sentiment, returns or tests of causality."""
import csv,json,re,hashlib,datetime as dt,collections
from pathlib import Path
from zoneinfo import ZoneInfo
P=Path(__file__).resolve().parents[1];ET=ZoneInfo('America/New_York');DATES=[(dt.date(2026,9,8)+dt.timedelta(days=i)).isoformat() for i in range(23)]
def read(name):return list(csv.DictReader((P/name).open(encoding='utf-8-sig')))
def write(name,rows,fields=None):
 with (P/name).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 guardian=read('data/processed/guardian_screened.csv');review=read('outputs/guardian_relevance_validation.csv')
 for i,r in enumerate(review):
  label=r['included']=='True';reason='agrees: headline/trail substantive AI topic' if label else 'agrees: insufficient substantive AI topic in headline/trail'
  if r['headline'].startswith('Parents and carers:'):label=False;reason='disagrees: reader solicitation, not substantive news article'
  elif r['headline'].startswith('Why I can') and 'driverless car' in r['headline']:label=True;reason='disagrees: self-driving vehicles are a substantive AI application in headline/trail'
  r.update(review_label=str(label),review_reason=reason,review_method='stratified batch headline/trail adjudication; no scoring API')
 write('outputs/guardian_relevance_validation.csv',review)
 corrections=0
 for r in guardian:
  before=r['included']=='True';included=before
  if r['content_type']=='article' and r['eastern_date'] in DATES:
   if re.search(r'\b(driverless|self-driving)\b',r['headline']+' '+r['trail_text'],re.I):included=True;r['relevance_reason']='included: explicit autonomous-driving AI application in headline/trail'
   if re.search(r'(?:\blet us know[.!]?\s*$|^tell us\b|\bshare your experiences\b|\bwe want to hear\b)',r['trail_text'],re.I):included=False;r['relevance_reason']='excluded: reader callout/solicitation, not substantive article'
  r['included']=str(included);corrections+=before!=included
 included=[r for r in guardian if r['included']=='True']
 write('data/processed/guardian_screened.csv',guardian);write('data/processed/guardian_clean.csv',included)
 pagination=json.loads((P/'outputs/guardian_pagination_audit.json').read_text(encoding='utf-8'))
 complete=all(sum(x['returned'] for x in pagination if x['route']==route)==next(x['total'] for x in pagination if x['route']==route) for route in ['broad','tag_resolved'])
 gd=[dict(date=d,candidate_articles=sum(r['eastern_date']==d and r['content_type']=='article' for r in guardian),included_articles=sum(r['eastern_date']==d for r in included),status='successful collection' if any(r['eastern_date']==d for r in included) else 'genuine zero included results under frozen queries/screening',pagination_complete=complete) for d in DATES]
 write('outputs/guardian_daily_coverage.csv',gd)
 # Global post-ID uniqueness and exact-text duplicates are independent.
 f=P/'data/processed/x_m2.jsonl';x=[json.loads(l) for l in f.read_text(encoding='utf-8').splitlines() if l.strip()];seen=set();valid=[];errors=[]
 for r in x:
  reason=None;match=re.match(r'^https://x.com/([^/]+)/status/(\d+)$',r['original_url']);stamp=dt.datetime.fromisoformat(r['publication_timestamp'].replace('Z','+00:00'));day=stamp.astimezone(ET).date().isoformat()
  if r['post_id'] in seen:reason='duplicate post ID'
  elif not match or match[2]!=r['post_id'] or match[1].lower()!=r['author_identifier'].lower() or not r.get('matching_header'):reason='author/status mismatch'
  elif day not in DATES or day!=r['sample_date']:reason='timestamp/day eligibility failure'
  elif abs((((int(r['post_id'])>>22)+1288834974657)/1000)-stamp.timestamp())>2:reason='status-ID creation time conflicts with page timestamp'
  elif not r['text'] or r.get('text_truncated'):reason='incomplete text'
  elif r.get('language')!='en':reason='English metadata unavailable'
  elif r.get('promoted') or r.get('reposted') or r.get('recommended'):reason='repost/promoted/recommended'
  elif not re.search(r'\b(artificial intelligence|generative AI|AI|Anthropic|OpenAI|ChatGPT|Claude|Gemini|machine learning|LLMs?|large language models?)\b',r['text'],re.I):reason='no enclosing-text AI relevance'
  if reason:errors.append(dict(post_id=r['post_id'],reason=reason));continue
  seen.add(r['post_id']);r['eastern_date']=day;r['exact_text_hash']=hashlib.sha256(r['text'].encode()).hexdigest();valid.append(r)
 groups=collections.defaultdict(list)
 for r in valid:groups[r['exact_text_hash']].append(r['post_id'])
 for r in valid:r['exact_text_duplicate_count']=len(groups[r['exact_text_hash']])
 fields=['platform','post_id','original_url','author_identifier','text','publication_timestamp','utc_timestamp','eastern_timestamp','eastern_date','query','retrieved_at','result_order','sample_date','text_truncated','language_status','quote_relationships','retrieval_method','window_status','exact_text_hash','exact_text_duplicate_count']
 write('data/processed/x_clean.csv',[{k:json.dumps(r[k],ensure_ascii=False) if isinstance(r.get(k),list) else r.get(k,'') for k in fields} for r in valid],fields)
 (P/'data/processed/x_clean.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in valid),encoding='utf-8')
 write('outputs/x_validation_failures.csv',errors,['post_id','reason'])
 duplicates=[dict(text_hash=h,post_ids=';'.join(ids),count=len(ids)) for h,ids in groups.items() if len(ids)>1]
 write('outputs/x_exact_text_duplicates.csv',duplicates,['text_hash','post_ids','count'])
 unique=[];hashseen=set()
 for r in valid:
  if r['exact_text_hash'] not in hashseen:hashseen.add(r['exact_text_hash']);unique.append(r)
 write('data/processed/x_unique_text_sensitivity.csv',[{k:json.dumps(r[k],ensure_ascii=False) if isinstance(r.get(k),list) else r.get(k,'') for k in fields} for r in unique],fields)
 af=P/'outputs/x_m2_collection_audit.json';audit=json.loads(af.read_text(encoding='utf-8')) if af.exists() else []
 ad={r['date']:r for r in audit};xd=[]
 for d in DATES:
  n=sum(r['eastern_date']==d for r in valid);a=ad.get(d);status='successful collection' if n>=20 else 'sampling shortfall' if a and a.get('unique_inspected',0)>0 else 'genuine zero results' if a and a.get('no_results') else 'access failure or uncompleted day'
  xd.append(dict(date=d,qualified_posts=n,target=20,shortfall=max(0,20-n),status=status,unique_inspected=a.get('unique_inspected','') if a else '',exact_text_unique=len({r['exact_text_hash'] for r in valid if r['eastern_date']==d})))
 write('outputs/x_daily_coverage.csv',xd)
 market=read('data/processed/market_panel.csv');ma=read('outputs/market_coverage.csv');market_valid=len(market)==108 and all(not r['missing_dates'] and r['duplicates']=='0' and r['nonpositive_prices']=='0' for r in ma)
 md=[]
 for i in range(27):
  d=(dt.date(2026,9,4)+dt.timedelta(days=i)).isoformat();md.append(dict(date=d,price_observations=sum(r['date']==d for r in market),status='nontrading session' if dt.date.fromisoformat(d).weekday()>=5 or d=='2026-09-07' else 'successful collection' if sum(r['date']==d for r in market)==6 else 'missing prices'))
 write('outputs/market_daily_coverage.csv',md)
 summary=dict(x_records=len(valid),x_days_at_target=sum(r['qualified_posts']>=20 for r in xd),x_shortfall_dates=[r['date'] for r in xd if r['shortfall']],x_validation_failures=len(errors),x_exact_duplicate_groups=len(duplicates),x_exact_duplicate_extra_records=sum(r['count']-1 for r in duplicates),guardian_candidates=len(guardian),guardian_clean=len(included),guardian_daily_min=min(r['included_articles'] for r in gd),guardian_daily_max=max(r['included_articles'] for r in gd),guardian_zero_dates=[r['date'] for r in gd if not r['included_articles']],guardian_pagination_complete=complete,guardian_validation_reviewed=len(review),guardian_initial_review_agreement=sum(r['review_label']==r['included'] for r in review),guardian_screen_corrections=corrections,market_records=len(market),market_complete=market_valid,year_status='provisional 2026; authoritative assignment evidence unavailable',readiness='ready for Milestone 3 with documented sampling limits' if not errors and market_valid and complete and all(r['qualified_posts'] for r in xd) else 'collection/validation gaps remain')
 (P/'outputs/milestone2_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
