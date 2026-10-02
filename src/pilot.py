"""Milestone 1 only; standard library, bounded sequential requests, no scoring."""
import argparse, csv, datetime as dt, html, json, os, re, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError
from email.utils import parsedate_to_datetime

ROOT = Path(__file__).resolve().parents[1]
AUDIT = []
SECRETS = []

def save_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(obj, ensure_ascii=False, indent=2)
    for secret in SECRETS:
        payload = payload.replace(secret, '[REDACTED]')
    path.write_text(payload, encoding='utf-8')

def csv_write(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

def audit(source, route, status, dates, text_available, timestamp, limitations):
    AUDIT.append(dict(source=source, route=route, status=status, date_coverage_tested=dates,
                      text_availability=text_available, timestamp_availability=timestamp, limitations=limitations))

def fetch(url, headers=None):
    # Never log URLs or exception messages: Guardian credentials are query parameters.
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={'User-Agent':'Assignment4-AccessPilot/1.0', **(headers or {})}), timeout=25) as r:
                return json.load(r), 'success'
        except HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == 2:
                return None, f'HTTP {e.code}'
            retry = e.headers.get('Retry-After')
            delay = 2 ** attempt
            if retry:
                try: delay = float(retry)
                except ValueError:
                    try: delay = max(0, (parsedate_to_datetime(retry)-dt.datetime.now(dt.timezone.utc)).total_seconds())
                    except Exception: return None, 'Retry-After unparseable; stopped'
            if delay > 60: return None, 'Retry-After exceeds pilot wait budget; stopped without retry'
            time.sleep(max(0, delay))
        except Exception as e:
            if attempt == 2: return None, type(e).__name__
            time.sleep(2 ** attempt)

def plain(s): return html.unescape(re.sub('<[^>]+>', ' ', s or '')).strip()

def main():
    p=argparse.ArgumentParser(); p.add_argument('--year',type=int,required=True)
    p.add_argument('--provisional',action='store_true'); args=p.parse_args(); year=args.year
    env={}
    if (ROOT/'.env').exists():
        for line in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines():
            m=re.match(r'^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$',line)
            if m: env[m[1]]=m[2].strip('\"\'')
    key=os.environ.get('GUARDIAN_API_KEY') or env.get('GUARDIAN_API_KEY')
    token=next((os.environ.get(n) or env.get(n) for n in ['X_BEARER_TOKEN','TWITTER_BEARER_TOKEN','X_API_BEARER_TOKEN'] if os.environ.get(n) or env.get(n)),None)
    SECRETS.extend(v for v in [key,token] if v)
    for name in ['src','data/raw','data/processed','outputs','report']: (ROOT/name).mkdir(parents=True,exist_ok=True)
    records={}; query='"artificial intelligence" OR "generative AI" OR Anthropic OR ChatGPT OR "machine learning" OR OpenAI'
    for day, narrow in [(8,False),(19,False),(30,False),(30,True)]:
        date=f'{year}-09-{day:02d}'; cache=ROOT/f'data/raw/guardian_{date}{"_focused" if narrow else ""}.json'
        params=dict(q='"artificial intelligence" OR "generative AI" OR Anthropic OR ChatGPT' if narrow else query,**{'from-date':date,'to-date':date,'page-size':10,'show-fields':'headline,trailText,bodyText','order-by':'newest' if narrow else 'oldest','api-key':key or ''})
        obj,status=(json.loads(cache.read_text(encoding='utf-8')),'cached success') if cache.exists() else fetch('https://content.guardianapis.com/search?'+urlencode(params)) if key else (None,'missing credential')
        if obj and obj.get('response',{}).get('status')=='ok':
            save_json(cache,obj); results=obj['response'].get('results',[])
            article_count=0
            for r in results:
                if r.get('type')!='article': continue
                article_count+=1; fields=r.get('fields',{}); headline=plain(fields.get('headline') or r.get('webTitle')); trail=plain(fields.get('trailText'))
                relevant=bool(re.search(r'\b(artificial intelligence|generative AI|AI|Anthropic|ChatGPT|machine learning|OpenAI|Claude)\b',headline+' '+trail,re.I))
                records[r['id']]=dict(id=r['id'],headline=headline,trail_text=trail,published_at=r.get('webPublicationDate'),url=r.get('webUrl'),body_text=fields.get('bodyText',''),ai_relevance_candidate=relevant,relevance_status='candidate; manual review pending' if relevant else 'no headline/trail keyword; manual review pending',pilot_date=date,window_status='provisional' if args.provisional else 'confirmed')
            audit('Guardian','Open Platform /search focused newest' if narrow else 'Open Platform /search',status,date,f'{article_count} articles; fields inspected','webPublicationDate',f'Total hits {obj["response"].get("total")}; first 10 only; non-articles excluded; relevance not validated')
        else: audit('Guardian','Open Platform /search',status,date,'none','none','No successful sample')
        time.sleep(1)
    fields=['id','headline','trail_text','published_at','url','body_text','ai_relevance_candidate','relevance_status','pilot_date','window_status']
    csv_write(ROOT/'data/processed/guardian_pilot.csv',list(records.values()),fields)
    xrows=[]
    if token:
        for day in [8,19,30]:
            date=f'{year}-09-{day:02d}'; end=(dt.date(year,9,day)+dt.timedelta(days=1)).isoformat()
            params={'query':'("artificial intelligence" OR "generative AI" OR Anthropic OR ChatGPT OR OpenAI) lang:en -is:retweet','start_time':date+'T04:00:00Z','end_time':end+'T04:00:00Z','max_results':10,'tweet.fields':'created_at,author_id','expansions':'author_id','user.fields':'username'}
            obj,status=fetch('https://api.x.com/2/tweets/search/all?'+urlencode(params),{'Authorization':'Bearer '+token})
            if obj and obj.get('data'):
                save_json(ROOT/f'data/raw/x_{date}.json',obj); users={u['id']:u['username'] for u in obj.get('includes',{}).get('users',[])}
                for r in obj['data']:
                    xrows.append(dict(id=r['id'],text=r['text'],author_id=r.get('author_id',''),author=users.get(r.get('author_id'),''),timestamp=r.get('created_at',''),url='https://x.com/i/web/status/'+r['id']))
            audit('X','API v2 full-archive search',status,date,'original text' if obj and obj.get('data') else 'none','created_at requested','Pilot only; daily corpus completeness unverified')
    else: audit('X','API v2 full-archive search','untested: no bearer credential','Sep 8/19/30','none','none','Only Guardian key found in project .env; no recognized X bearer environment variables')
    csv_write(ROOT/'data/processed/x_pilot.csv',xrows,['id','text','author_id','author','timestamp','url'])
    prices=[]
    start=int(dt.datetime(year,9,3,tzinfo=dt.timezone.utc).timestamp()); end=int(dt.datetime(year,10,1,tzinfo=dt.timezone.utc).timestamp())
    for symbol in ['NVDA','MSFT','GOOGL','AMZN','META','SPY']:
        params={'period1':start,'period2':end,'interval':'1d','events':'div,splits','includeAdjustedClose':'true'}
        obj,status=fetch(f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?'+urlencode(params))
        usable=[]
        if obj and obj.get('chart',{}).get('result'):
            save_json(ROOT/f'data/raw/market_{symbol}_{year}.json',obj)
            r=obj['chart']['result'][0]; q=r['indicators']['quote'][0]; adj=r['indicators'].get('adjclose',[{}])[0].get('adjclose',[])
            from zoneinfo import ZoneInfo
            for i,t in enumerate(r.get('timestamp',[])):
                date=dt.datetime.fromtimestamp(t,ZoneInfo('America/New_York')).date().isoformat()
                close=q.get('close',[])[i]; ac=adj[i] if i<len(adj) else None
                if close is not None and ac is not None:
                    row=dict(symbol=symbol,date=date,close=close,adjusted_close=ac,source='Yahoo Finance chart',adjustment='vendor adjclose; intended dividend/split adjustment; factors not independently verified',window_status='provisional' if args.provisional else 'confirmed')
                    usable.append(row)
            # Keep preceding close and three observation dates, not full analysis.
            before=[r for r in usable if r['date']<f'{year}-09-08']; dates=[f'{year}-09-{d:02d}' for d in [8,18,30]]
            selected=([before[-1]] if before else [])+[r for r in usable if r['date'] in dates]; prices.extend(selected)
            audit('Market',f'Yahoo chart {symbol}',status,';'.join(r['date'] for r in selected),'not applicable','exchange-local dates',f'Adjusted sample rows {len(selected)}; preceding close '+(before[-1]['date'] if before else 'MISSING'))
        else: audit('Market',f'Yahoo chart {symbol}',status,f'{year}-09-03 to 09-30','not applicable','none','No usable adjusted daily-price sample')
        time.sleep(1)
    csv_write(ROOT/'data/processed/market_pilot.csv',prices,['symbol','date','close','adjusted_close','source','adjustment','window_status'])
    audit('X','Original post via web reader','failed: HTTP 403','candidate Sep 8 Eastern / Sep 9 UTC 2026','not retrieved','post ID supplies candidate UTC time','https://x.com/EvanHub/status/2097497037956891126; no original observation saved')
    audit('X','Web search dated broad AI queries','no results','2026-09-08;2026-09-19;2026-09-30','none','none','Search snippets never counted as dataset')
    audit('X','Third-party scrapers / browser logged-in search','untested','','none','none','No scraping infrastructure or restriction bypass attempted')
    csv_write(ROOT/'source_access_audit.csv',AUDIT,list(AUDIT[0]))
    save_json(ROOT/'outputs/pilot_summary.json',{'year':year,'window_status':'provisional' if args.provisional else 'confirmed','guardian_articles':len(records),'x_posts':len(xrows),'market_rows':len(prices),'audit':AUDIT})
    print(json.dumps({'guardian_articles':len(records),'x_posts':len(xrows),'market_rows':len(prices),'statuses':[(r['route'],r['status']) for r in AUDIT]},indent=2))

if __name__=='__main__': main()
