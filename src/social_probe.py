import json,time,datetime as dt,csv
from pathlib import Path
from urllib.request import urlopen,Request
from urllib.parse import urlencode
from urllib.error import HTTPError
P=Path(r'D:\School Work\FRE-GY 7871 NLP\Assignment 4')
rows=[]; records={}
def get(name,url):
    try:
        with urlopen(Request(url,headers={'User-Agent':'Assignment4HistoricalPilot/1.0'}),timeout=20) as r:
            raw=r.read(); content=r.headers.get('Content-Type',''); status=r.status
        (P/'data/raw'/('social_'+name+'.txt')).write_bytes(raw)
        rows.append(dict(route=name,status=str(status),url=url,bytes=len(raw),content_type=content))
        try:return json.loads(raw)
        except Exception:return None
    except HTTPError as e: rows.append(dict(route=name,status='HTTP '+str(e.code),url=url,bytes=0,content_type=''));return None
    except Exception as e: rows.append(dict(route=name,status=type(e).__name__,url=url,bytes=0,content_type=''));return None
def add(d,kind,query):
    ts=d.get('created_utc')
    if not ts:return
    date=dt.datetime.fromtimestamp(ts,dt.timezone.utc)
    if not (dt.datetime(2026,9,8,tzinfo=dt.timezone.utc)<=date<dt.datetime(2026,10,1,tzinfo=dt.timezone.utc)):return
    title=d.get('title',''); body=d.get('selftext','') if kind=='post' else d.get('body','')
    if body in ('[removed]','[deleted]') and not title:return
    records[d['id']]=dict(platform='Reddit',post_id=d['id'],record_type=kind,title=title,self_text=body if kind=='post' else '',text=(title+'\n'+body).strip(),publication_timestamp=date.isoformat(),author_identifier=d.get('author',''),original_url='https://www.reddit.com'+d.get('permalink',''),retrieval_method='public Reddit JSON',collection_query=query,subreddit=d.get('subreddit',''),retrieved_at=dt.datetime.now(dt.timezone.utc).isoformat())
get('facebook_public_metaai','https://www.facebook.com/MetaAI/')
get('reddit_historical_search','https://www.reddit.com/search.json?'+urlencode({'q':'(AI OR "artificial intelligence" OR Anthropic OR ChatGPT OR "generative AI")','sort':'new','t':'month','limit':100}))
for name,url in [('hf_metadata','https://huggingface.co/api/datasets/SinclairSchneider/tweets_sample_2026'),('hf_readme','https://huggingface.co/datasets/SinclairSchneider/tweets_sample_2026/raw/main/README.md'),('reddit_start','https://www.reddit.com/r/MachineLearning/comments/1w5h9se.json?limit=20'),('reddit_middle','https://www.reddit.com/r/philosophy/comments/1wktr7b.json?limit=20'),('reddit_end','https://www.reddit.com/r/LaGazzettadiKyiv/comments/1wubzmb.json?limit=20')]:
    obj=get(name,url)
    if isinstance(obj,list):
        def walk(children):
            for c in children:
                d=c.get('data',{}); k=c.get('kind')
                if k in ('t1','t3'):add(d,'comment' if k=='t1' else 'post','web discovery: broad AI + dated search')
                replies=d.get('replies')
                if isinstance(replies,dict):walk(replies.get('data',{}).get('children',[]))
        for listing in obj:walk(listing.get('data',{}).get('children',[]))
    time.sleep(1)
fields=['platform','post_id','record_type','title','self_text','text','publication_timestamp','author_identifier','original_url','retrieval_method','collection_query','subreddit','retrieved_at']
with (P/'data/processed/social_pilot.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records.values())
with (P/'outputs/social_route_tests.json').open('w',encoding='utf-8') as f:json.dump(rows,f,indent=2)
print(json.dumps({'routes':rows,'records':len(records)},indent=2))
