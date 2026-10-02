"""Milestone 2 local Guardian pagination/relevance and market validation; no scoring."""
import csv,json,re,hashlib,time,datetime as dt,os
from pathlib import Path
from zoneinfo import ZoneInfo
import pilot
P=Path(__file__).resolve().parents[1];ET=ZoneInfo('America/New_York')
RULES=json.loads((P/'collection_rules.json').read_text(encoding='utf-8'));records={};acq=[]
DATES=[(dt.date(2026,9,8)+dt.timedelta(days=i)).isoformat() for i in range(23)]
def write(name,rows,fields=None):pilot.csv_write(P/name,rows,fields or list(rows[0]) if rows else fields or ['date','status'])
def ingest(obj,route):
 for r in obj.get('response',{}).get('results',[]):
  if 'webPublicationDate' not in r:continue
  f=r.get('fields',{});old=records.get(r['id'],{})
  ts=r.get('webPublicationDate','');day=dt.datetime.fromisoformat(ts.replace('Z','+00:00')).astimezone(ET).date().isoformat() if ts else ''
  headline=pilot.plain(f.get('headline') or r.get('webTitle'));trail=pilot.plain(f.get('trailText'));text=headline+' '+trail
  term=re.search(r'\b(artificial intelligence|generative AI|AI|Anthropic|OpenAI|ChatGPT|Claude|Gemini|machine learning|LLMs?|large language models?)\b',text,re.I)
  ambiguous=re.search(r'\b(gemini)\b',text,re.I) and not re.search(r'\b(AI|Google|model|chatbot|artificial|intelligence)\b',text,re.I)
  reason='included: explicit substantive AI/entity in headline/trail'
  if r.get('type')!='article':reason='excluded: non-article'
  elif day not in DATES:reason='excluded: outside Eastern window'
  elif not term:reason='excluded: no substantive headline/trail AI term'
  elif ambiguous:reason='excluded: ambiguous Gemini without AI context'
  records[r['id']]=dict(id=r['id'],content_type=r.get('type'),headline=headline,trail_text=trail,publication_timestamp=ts,eastern_date=day,url=r.get('webUrl',''),body_text=f.get('bodyText') or old.get('body_text',''),included=reason.startswith('included'),relevance_reason=reason,acquisition_provenance=old.get('acquisition_provenance',[])+[route],year_status='provisional')
def main():
 env={}
 for l in (P/'.env').read_text(encoding='utf-8-sig').splitlines():
  m=re.match(r'^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$',l)
  if m:env[m[1]]=m[2].strip('\"\'')
 key=os.environ.get('GUARDIAN_API_KEY') or env.get('GUARDIAN_API_KEY');pilot.SECRETS.append(key)
 for cache in sorted((P/'data/raw').glob('guardian_*.json')):ingest(json.loads(cache.read_text(encoding='utf-8')),{'cache':cache.name,'method':'existing pilot cache'})
 for route in ['broad','tag','tag_resolved']:
  page=1;pages=1
  while page<=pages:
   params={'from-date':'2026-09-08','to-date':'2026-10-01','page-size':50,'show-fields':'headline,trailText,bodyText','order-by':'oldest','page':page}
   params.update({'q':RULES['guardian']['queries_in_order'][0]} if route=='broad' else {'tag':'technology/artificialintelligenceai' if route=='tag_resolved' else 'technology/artificialintelligence'})
   cache=P/f'data/raw/guardian_m2_{route}_page{page:03}.json'
   if cache.exists():obj=json.loads(cache.read_text(encoding='utf-8'));status='cached'
   else:obj,status=pilot.fetch('https://content.guardianapis.com/search?'+__import__('urllib.parse',fromlist=['urlencode']).urlencode({**params,'api-key':key}))
   if not obj or obj.get('response',{}).get('status')!='ok':acq.append(dict(route=route,page=page,status=status,total=None,pages=None,returned=0));break
   if not cache.exists():pilot.save_json(cache,obj)
   response=obj['response'];pages=response.get('pages',0);acq.append(dict(route=route,page=page,status=status,total=response.get('total'),pages=pages,returned=len(response.get('results',[]))))
   ingest(obj,{'cache':cache.name,'method':'Guardian Open Platform search','parameters':params,'retrieved_at':dt.datetime.now(dt.timezone.utc).isoformat()});page+=1;time.sleep(1)
 included=[r for r in records.values() if r['included']]
 write('data/processed/guardian_screened.csv',[{**r,'acquisition_provenance':json.dumps(r['acquisition_provenance'])} for r in records.values()])
 write('data/processed/guardian_clean.csv',[{**r,'acquisition_provenance':json.dumps(r['acquisition_provenance'])} for r in included])
 pilot.save_json(P/'outputs/guardian_pagination_audit.json',acq)
 complete=all(any(x['route']==route for x in acq) and sum(x['returned'] for x in acq if x['route']==route)==next(x['total'] for x in acq if x['route']==route) for route in ['broad','tag_resolved'])
 daily=[dict(date=d,candidate_articles=sum(r['eastern_date']==d and r['content_type']=='article' for r in records.values()),included_articles=sum(r['eastern_date']==d for r in included),status='successful collection' if any(r['eastern_date']==d for r in included) and complete else 'genuine zero included results under frozen retrieval/screening' if complete else 'access/pagination incomplete',pagination_complete=complete) for d in DATES]
 write('outputs/guardian_daily_coverage.csv',daily)
 # Deterministic stratification by inclusion and window third, no sentiment/returns.
 samples=[]
 for include in [True,False]:
  for band,(lo,hi) in enumerate([(8,15),(16,23),(24,30)]):
   bucket=[r for r in records.values() if r['included']==include and r['content_type']=='article' and r['eastern_date'] in DATES and lo<=int(r['eastern_date'][-2:])<=hi]
   bucket.sort(key=lambda r:hashlib.sha256(r['id'].encode()).hexdigest())
   samples.extend([{k:r[k] for k in ['id','headline','trail_text','eastern_date','included','relevance_reason']}|{'band':band,'review_label':'','review_reason':''} for r in bucket[:5]])
 write('outputs/guardian_relevance_validation.csv',samples)
 prices=[];expected=[dt.date(2026,9,4)+dt.timedelta(days=i) for i in range(27) if (dt.date(2026,9,4)+dt.timedelta(days=i)).weekday()<5 and (dt.date(2026,9,4)+dt.timedelta(days=i))!=dt.date(2026,9,7)]
 expected=[d.isoformat() for d in expected];market_audit=[];events=[]
 for symbol in RULES['market']['symbols']:
  obj=json.loads((P/f'data/raw/market_{symbol}_2026.json').read_text(encoding='utf-8'));r=obj['chart']['result'][0];quote=r['indicators']['quote'][0];adj=r['indicators']['adjclose'][0]['adjclose'];rows=[]
  for i,t in enumerate(r['timestamp']):
   d=dt.datetime.fromtimestamp(t,ET).date().isoformat()
   if '2026-09-04'<=d<='2026-09-30':rows.append(dict(symbol=symbol,date=d,close=quote['close'][i],adjusted_close=adj[i],source='Yahoo chart cached',adjustment_convention='vendor dividend/split-adjusted adjclose; factors not independently rebuilt',raw_cache=f'market_{symbol}_2026.json',year_status='provisional'))
  missing=[d for d in expected if not any(x['date']==d and x['close'] is not None and x['adjusted_close'] is not None for x in rows)];duplicates=len(rows)-len({x['date'] for x in rows});market_audit.append(dict(symbol=symbol,expected_sessions=len(expected),rows=len(rows),missing_dates=';'.join(missing),duplicates=duplicates,nonpositive_prices=sum(x['close'] is not None and x['close']<=0 or x['adjusted_close'] is not None and x['adjusted_close']<=0 for x in rows)))
  prices.extend(rows);events.append(dict(symbol=symbol,events=r.get('events',{}),exchange_timezone=r.get('meta',{}).get('exchangeTimezoneName')))
 write('data/processed/market_panel.csv',prices);write('outputs/market_coverage.csv',market_audit);pilot.save_json(P/'outputs/market_adjustment_events.json',events)
 pilot.save_json(P/'outputs/m2_local_summary.json',{'guardian_candidates':len(records),'guardian_included':len(included),'guardian_pagination_complete':complete,'guardian_validation_sample':len(samples),'market_rows':len(prices),'market_expected_sessions':len(expected),'market_audit':market_audit})
 print(json.dumps({'guardian_candidates':len(records),'guardian_included':len(included),'pagination_complete':complete,'validation_sample':len(samples),'market_rows':len(prices),'market_missing':sum(bool(r['missing_dates']) for r in market_audit)},indent=2))
if __name__=='__main__':main()
