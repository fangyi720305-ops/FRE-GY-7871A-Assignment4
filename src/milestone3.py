"""Milestone 3 only: deterministic local scoring, review selection, aggregation.
Run from project root. No network requests, market reads, or per-record inference APIs.
"""
import sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.local-packages'))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.local-packages' / 'mpl-config'))
import csv, json, re, html, hashlib, random, statistics, importlib.metadata
from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import vaderSentiment.vaderSentiment as vader_module

OUT = ROOT / 'outputs'; DATA = ROOT / 'data' / 'processed'
ET = ZoneInfo('America/New_York')
START, END = date(2026,9,8), date(2026,9,30)
METHOD_VERSION = 'vader-english-clean-v1'
RULES = json.loads((ROOT / 'src' / 'framing_rules.json').read_text(encoding='utf-8'))
CATS = list(RULES['categories'])
def digest(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def dump(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def csvread(path):
    with path.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def csvwrite(path,rows,fields=None):
    fields = fields or list(rows[0])
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for row in rows: w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items() if k in fields})
def clean(s):
    s=html.unescape(re.sub(r'</?[A-Za-z][^>]*>', ' ', s or ''))
    s=re.sub(r'https?://\S+|www\.\S+', 'URL', s,flags=re.I)
    return re.sub(r'\s+', ' ', s).strip()
def primary(row,channel):
    if channel=='X': return row['text'],clean(row['text'])
    headline,trail=row['headline'],row.get('trail_text','')
    h,t=clean(headline),clean(trail)
    if t.casefold().startswith(h.casefold()): t=t[len(h):].lstrip(' .:–—-')
    return headline+'\n'+trail, h+(' '+t if t else '')
def sentiment_label(v): return 'positive' if v>=.05 else 'negative' if v<=-.05 else 'neutral'

def framing(text):
    evidence=[]; excluded=[]
    for category,patterns in RULES['categories'].items():
        for rule in patterns:
            for m in re.finditer(rule['pattern'],text,re.I):
                left=max(text.rfind(x,0,m.start()) for x in '.!?;\n')+1
                nexts=[text.find(x,m.end()) for x in '.!?;\n']; right=min([x for x in nexts if x>=0] or [len(text)])
                clause=text[left:right].strip(); context=text[max(left,m.start()-100):min(right,m.end()+100)]
                exclusions=[x for x in RULES['context_exclusions'] if re.search(x['pattern'],context,re.I)]
                if exclusions:
                    excluded.append({'category':category,'rule_id':rule['id'],'phrase':m.group(),'span':[m.start(),m.end()],'reason':[x['reason'] for x in exclusions]}); continue
                # Evidence stance is conservative: an affirmative mention alone is not endorsement.
                prefix=text[max(left,m.start()-65):m.start()]
                if re.search(RULES['stance']['rejects'],prefix,re.I): stance='rejects'
                elif re.search(RULES['stance']['reports'],clause,re.I) or re.search(r'[“”"]',clause): stance='reports'
                elif re.search(RULES['stance']['endorses'],clause,re.I): stance='endorses'
                else: stance='uncertain'
                evidence.append({'category':category,'rule_id':rule['id'],'phrase':m.group(),'span':[m.start(),m.end()],'context':context,'stance':stance})
    flags={c:any(e['category']==c for e in evidence) for c in CATS}
    risk=[e for e in evidence if e['category']!='benefits_opportunity']
    stances=sorted(set(e['stance'] for e in risk))
    return {**flags,'unclassified':not any(flags.values()),'risk_stance':stances or ['not_applicable'],'framing_evidence':evidence,'excluded_evidence':excluded}

def load_records():
    sources={'Guardian':csvread(DATA/'guardian_clean.csv'),'X':[json.loads(x) for x in (DATA/'x_clean.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]}
    result=[]
    for channel,rows in sources.items():
        for row in rows:
            raw,analyzed=primary(row,channel)
            utc=datetime.fromisoformat(row['publication_timestamp'].replace('Z','+00:00')).astimezone(timezone.utc)
            eastern=utc.astimezone(ET)
            assert START<=eastern.date()<=END and str(eastern.date())==row['eastern_date']
            result.append({'channel':channel,'record_id':row.get('post_id') or row['id'],'original_text':raw,'analyzed_text':analyzed,'text_hash':digest(analyzed),'publication_timestamp':row['publication_timestamp'],'utc_timestamp':utc.isoformat(),'eastern_timestamp':eastern.isoformat(),'eastern_date':str(eastern.date()),'url':row.get('original_url') or row['url'],'author_identifier':row.get('author_identifier',''),'query_provenance':row.get('query') or row.get('acquisition_provenance',''),'result_order':row.get('result_order',''),'quote_relationships':row.get('quote_relationships',[]),'exact_text_hash':row.get('exact_text_hash','')})
    assert len({(r['channel'],r['record_id']) for r in result})==len(result)
    return result

def select_validation(rows):
    # Fixed random priorities, then coverage quotas; this is a diagnostic stratified sample.
    selected=[]
    for channel in ['Guardian','X']:
        pool=[r for r in rows if r['channel']==channel]; random.Random(787103).shuffle(pool)
        picked=[]
        predicates=[('sentiment:'+x,lambda r,x=x:r['sentiment_class']==x,3) for x in ['negative','neutral','positive']]
        predicates += [('framing:'+x,lambda r,x=x:r[x],2) for x in CATS+['unclassified']]
        predicates += [('stance:rejects',lambda r:'rejects' in r['risk_stance'],1),('stance:reports',lambda r:'reports' in r['risk_stance'],1)]
        for stratum,predicate,quota in predicates:
            for r in [r for r in pool if predicate(r) and r not in picked][:min(quota,20-len(picked))]:
                r=dict(r); r['selection_stratum']=stratum; picked.append(r)
        # picked copies differ from source; explicitly exclude already-selected IDs.
        unique=[]; seen=set()
        for r in picked:
            if r['record_id'] not in seen: unique.append(r); seen.add(r['record_id'])
        for r in pool:
            if len(unique)==20: break
            if r['record_id'] not in seen:
                r=dict(r); r['selection_stratum']='fixed_seed_fill'; unique.append(r); seen.add(r['record_id'])
        assert len(unique)==20
        selected+=unique
    return selected

def aggregate(rows):
    result=[]
    for day in (START+timedelta(days=n) for n in range((END-START).days+1)):
        for channel in ['Guardian','X']:
            group=[r for r in rows if r['channel']==channel and r['eastern_date']==str(day)]; n=len(group)
            result.append({'eastern_date':str(day),'channel':channel,'record_count':n,'sentiment_denominator':n,'mean_compound':statistics.mean(r['compound'] for r in group) if n else None,**{x+'_share':sum(r['sentiment_class']==x for r in group)/n if n else None for x in ['positive','negative','neutral']},'framing_denominator':n,**{c+'_share':sum(r[c] for r in group)/n if n else None for c in CATS+['unclassified']},'coverage_status':'observed_bounded_sample' if n and channel=='X' else 'observed' if n else 'missing_not_neutral'})
    return result
def combined(daily):
    result=[]
    for day in sorted(set(r['eastern_date'] for r in daily)):
        g,x=[next(r for r in daily if r['eastern_date']==day and r['channel']==c) for c in ['Guardian','X']]
        result.append({'eastern_date':day,'guardian_count':g['record_count'],'x_count':x['record_count'],'combined_mean_compound':.5*g['mean_compound']+.5*x['mean_compound'] if g['record_count'] and x['record_count'] else None,'weight_guardian':.5,'weight_x':.5})
    return result
def overall(rows):
    return {c:{'n':len(g:= [r for r in rows if r['channel']==c]),'mean_compound':statistics.mean(r['compound'] for r in g),'sentiment_shares':{k:sum(r['sentiment_class']==k for r in g)/len(g) for k in ['positive','negative','neutral']},'framing_shares':{k:sum(r[k] for r in g)/len(g) for k in CATS+['unclassified']}} for c in ['Guardian','X']}

def charts(daily,summary):
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(11,5))
    for channel,color in [('Guardian','#176a9a'),('X','#bd542c')]:
        group=[r for r in daily if r['channel']==channel]
        ax.plot([date.fromisoformat(r['eastern_date']) for r in group],[r['mean_compound'] for r in group],marker='o',markersize=4,label=f"{channel} (n={summary[channel]['n']})",color=color)
    ax.axhline(0,color='#555555',linewidth=.9); ax.set_ylabel('Mean VADER compound'); ax.set_title('Text sentiment in AI-related material\nDaily values, September 8–30, 2026 (year provisional)',loc='left')
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d')); ax.legend(); ax.grid(axis='y',alpha=.2)
    fig.text(.09,.025,'Eastern calendar days • Unsmoothed values • X: bounded search sample; counts do not measure discussion volume.',fontsize=9)
    fig.tight_layout(rect=(0,.05,1,1)); fig.savefig(OUT/'daily_sentiment_draft.png',dpi=180); fig.savefig(OUT/'daily_sentiment_draft.svg'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,5.6)); labels=['Existential / safety','Economic / social','Benefits / opportunity','Investment / valuation','Unclassified']; keys=CATS+['unclassified']
    for j,(channel,color) in enumerate([('Guardian','#176a9a'),('X','#bd542c')]):
        vals=[100*summary[channel]['framing_shares'][k] for k in keys]; positions=[i+(-.19 if j==0 else .19) for i in range(len(keys))]
        bars=ax.barh(positions,vals,height=.36,color=color,label=f"{channel} (denominator n={summary[channel]['n']})")
        for b,v in zip(bars,vals): ax.text(v+.5,b.get_y()+b.get_height()/2,f'{v:.1f}%',va='center',fontsize=10)
    ax.set_yticks(range(len(keys)),labels); ax.invert_yaxis(); ax.set_xlim(0,max(55,max(b.get_width() for b in ax.patches)+12)); ax.set_xlabel('Share of channel records (%)'); ax.set_title('Rule-matched AI framing by channel\nSeptember 8–30, 2026 (year provisional)',loc='left'); ax.legend(loc='upper right'); ax.grid(axis='x',alpha=.15)
    fig.text(.025,.025,'Categories can overlap; shares do not sum to 100%. Unclassified means no rule match.\nRisk mentions do not imply negative sentiment. X is a bounded search sample.',fontsize=9)
    fig.tight_layout(rect=(0,.07,1,1)); fig.savefig(OUT/'framing_shares_draft.png',dpi=180); fig.savefig(OUT/'framing_shares_draft.svg'); plt.close(fig)

def main():
    OUT.mkdir(exist_ok=True); analyzer=SentimentIntensityAnalyzer()
    module=Path(vader_module.__file__).parent
    hashes={name:hashlib.sha256((module/name).read_bytes()).hexdigest() for name in ['vader_lexicon.txt','emoji_utf8_lexicon.txt']}
    method={'method_version':METHOD_VERSION,'package':'vaderSentiment','package_version':importlib.metadata.version('vaderSentiment'),'lexicon_hashes_sha256':hashes,'lexicon_version':'bundled with vaderSentiment 3.3.2','thresholds':{'positive_min':.05,'negative_max':-.05},'settings':'Default SentimentIntensityAnalyzer; no lexicon edits; default punctuation, capitalization, negation and emoji handling','cleaning':'HTML tags removed, HTML entities decoded, http(s)/www URLs replaced with URL, whitespace collapsed; punctuation/negation/emojis retained; Guardian repeated leading headline removed from trail','primary_text':{'X':'original enclosing post text only','Guardian':'headline plus cleaned trail; body excluded'},'metric_name':'text sentiment in AI-related material','source':'https://github.com/cjhutto/vaderSentiment','year_status':'2026 provisional','timezone':'America/New_York','rule_version':RULES['version'],'rule_sha256':digest(json.dumps(RULES,sort_keys=True)),'validation_seed':787103,'market_data_read':False}
    methodkey=digest(json.dumps({k:v for k,v in method.items() if k not in ['rule_version','rule_sha256','validation_seed']},sort_keys=True))
    cachepath=DATA/'sentiment_cache.jsonl'; cache={}
    if cachepath.exists():
        for line in cachepath.read_text(encoding='utf-8').splitlines():
            r=json.loads(line); cache[r['key']]=r['scores']
    framecache=DATA/'framing_cache.jsonl'; cachedframes={}
    if framecache.exists():
        for line in framecache.read_text(encoding='utf-8').splitlines():
            if line.strip():
                entry=json.loads(line); cachedframes[entry['key']]=entry['labels']
    rows=load_records(); new=0
    with cachepath.open('a',encoding='utf-8') as f:
        for r in rows:
            key=digest(r['text_hash']+methodkey)
            if key not in cache:
                cache[key]=analyzer.polarity_scores(r['analyzed_text']); f.write(json.dumps({'key':key,'text_hash':r['text_hash'],'method_key':methodkey,'scores':cache[key]})+'\n'); new+=1
            scores=cache[key]; r.update({'compound':scores['compound'],'vader_positive':scores['pos'],'vader_negative':scores['neg'],'vader_neutral':scores['neu'],'sentiment_class':sentiment_label(scores['compound']),'sentiment_method':METHOD_VERSION,'framing_method':RULES['version']})
            framekey=digest(r['text_hash']+method['rule_sha256'])
            r.update(cachedframes[framekey] if framekey in cachedframes else framing(r['analyzed_text']))
    # Persist framing cache under both text hash and full dictionary version/hash.
    framecache=DATA/'framing_cache.jsonl'; existing=set()
    if framecache.exists(): existing={json.loads(x)['key'] for x in framecache.read_text(encoding='utf-8').splitlines() if x.strip()}
    with framecache.open('a',encoding='utf-8') as f:
        for r in rows:
            key=digest(r['text_hash']+method['rule_sha256'])
            if key not in existing:
                f.write(json.dumps({'key':key,'text_hash':r['text_hash'],'rule_version':RULES['version'],'rule_sha256':method['rule_sha256'],'labels':{k:r[k] for k in CATS+['unclassified','risk_stance','framing_evidence','excluded_evidence']}},ensure_ascii=False)+'\n'); existing.add(key)
    with (DATA/'scored_records.jsonl').open('w',encoding='utf-8') as f:
        for r in rows: f.write(json.dumps(r,ensure_ascii=False)+'\n')
    for c in ['Guardian','X']: csvwrite(DATA/(c.lower()+'_scored.csv'),[r for r in rows if r['channel']==c])
    samplepath=OUT/'validation_sample.json'
    if not samplepath.exists(): dump(samplepath,select_validation(rows))
    sample=json.loads(samplepath.read_text(encoding='utf-8'))
    assert len(sample)==40 and len({(r['channel'],r['record_id']) for r in sample})==40
    byid={(r['channel'],r['record_id']):r for r in rows}
    assert all((r['channel'],r['record_id']) in byid and r['analyzed_text']==byid[(r['channel'],r['record_id'])]['analyzed_text'] and r['compound']==byid[(r['channel'],r['record_id'])]['compound'] for r in sample), 'Review manifest text or sentiment changed: preserve old reviews and obtain a new reviewed manifest before reusing labels.'
    daily=aggregate(rows); csvwrite(OUT/'daily_channel_sentiment.csv',daily); basecombined=combined(daily); csvwrite(OUT/'daily_combined_sentiment.csv',basecombined)
    ids={r['post_id'] for r in csvread(DATA/'x_unique_text_sensitivity.csv')}; sensitive=[r for r in rows if r['channel']=='Guardian' or r['record_id'] in ids]; assert len(ids)==448
    csvwrite(DATA/'x_unique_text_scored.csv',[r for r in sensitive if r['channel']=='X'])
    sdaily=aggregate(sensitive); csvwrite(OUT/'daily_channel_sensitivity.csv',sdaily); scombined=combined(sdaily); csvwrite(OUT/'daily_combined_sensitivity.csv',scombined)
    comparison=[]
    for b,s in zip(basecombined,scombined):
        bx=next(r for r in daily if r['channel']=='X' and r['eastern_date']==b['eastern_date']); sx=next(r for r in sdaily if r['channel']=='X' and r['eastern_date']==b['eastern_date'])
        comparison.append({'eastern_date':b['eastern_date'],'x_primary_n':b['x_count'],'x_unique_text_n':s['x_count'],'x_primary_mean':bx['mean_compound'],'x_unique_text_mean':sx['mean_compound'],'x_mean_change':sx['mean_compound']-bx['mean_compound'],'combined_primary_mean':b['combined_mean_compound'],'combined_unique_text_mean':s['combined_mean_compound'],'combined_mean_change':s['combined_mean_compound']-b['combined_mean_compound'],**{k+'_share_change':sx[k+'_share']-bx[k+'_share'] for k in CATS+['unclassified','positive','negative','neutral']}})
    csvwrite(OUT/'duplicate_sensitivity_comparison.csv',comparison)
    summary={'overall':overall(rows),'sensitivity_overall':overall(sensitive),'daily_coverage':{c:{'days_observed':sum(r['record_count']>0 for r in daily if r['channel']==c),'min_n':min(r['record_count'] for r in daily if r['channel']==c),'max_n':max(r['record_count'] for r in daily if r['channel']==c)} for c in ['Guardian','X']},'duplicate_sensitivity':{'removed':458-448,'max_absolute_daily_x_mean_change':max(abs(r['x_mean_change']) for r in comparison),'max_absolute_daily_combined_mean_change':max(abs(r['combined_mean_change']) for r in comparison)},'year_status':'2026 provisional','missing_dates':[],'review_status':'pending','readiness':'pending validation'}
    reviews=OUT/'validation_reviews.json'
    if reviews.exists():
        reviewed=json.loads(reviews.read_text(encoding='utf-8')); assert len(reviewed)==40
        ledger=[]
        for a in sample:
            j=next(r for r in reviewed if r['channel']==a['channel'] and r['record_id']==a['record_id']); current=next(r for r in rows if r['channel']==a['channel'] and r['record_id']==a['record_id'])
            ledger.append({'channel':a['channel'],'record_id':a['record_id'],'selection_stratum':a['selection_stratum'],'analyzed_text':a['analyzed_text'],'reviewer_type':'Codex','independent_human_review':False,'automated_compound':a['compound'],'automated_sentiment':a['sentiment_class'],'reviewed_sentiment':j['sentiment'],'sentiment_agrees':a['sentiment_class']==j['sentiment'],'initial_framing':[c for c in CATS if a[c]],'final_framing':[c for c in CATS if current[c]],'reviewed_framing':j['framing'],'initial_framing_exact_agrees':set(c for c in CATS if a[c])==set(j['framing']),'final_framing_exact_agrees':set(c for c in CATS if current[c])==set(j['framing']),'automated_risk_stance':current['risk_stance'],'reviewed_risk_stance':j['risk_stance'],'ai_attitude':j['ai_attitude'],'review_notes':j['notes']})
        csvwrite(OUT/'validation_ledger.csv',ledger)
        summary['validation']={c:{'n':len(g:=[r for r in ledger if r['channel']==c]),'sentiment_agreement':sum(r['sentiment_agrees'] for r in g)/len(g),'initial_framing_exact_agreement':sum(r['initial_framing_exact_agrees'] for r in g)/len(g),'final_framing_exact_agreement':sum(r['final_framing_exact_agrees'] for r in g)/len(g)} for c in ['Guardian','X']}
        summary['review_status']='40 Codex-reviewed judgments; no independent human validation'; summary['readiness']='Milestone 3 complete; Milestone 4 can begin under documented sentiment, sampling, timing and provisional-year limitations'
    dump(OUT/'scoring_method.json',method); dump(OUT/'milestone3_summary.json',summary); charts(daily,summary['overall'])
    print(json.dumps({'records':len(rows),'new_sentiment_cache_entries':new,'review_status':summary['review_status'],'overall':summary['overall'],'sensitivity':summary['duplicate_sensitivity']},ensure_ascii=False))
if __name__=='__main__': main()
