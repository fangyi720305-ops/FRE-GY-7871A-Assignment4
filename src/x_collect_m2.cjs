// Bounded pilot using verified Eastern-day endpoint behavior; no full collection.
const fs=require('fs'),path=require('path');const {chromium}=require('C:/Users/fangyi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');const {extract,ready,challenge}=require('./x_debug.cjs');
const root=path.resolve(__dirname,'..'),out=path.join(root,'outputs'),data=path.join(root,'data/processed');
const file=path.join(data,'x_m2.jsonl'),csvfile=path.join(data,'x_clean.csv');const seen=new Map();if(fs.existsSync(file))for(const line of fs.readFileSync(file,'utf8').split('\n').filter(Boolean)){const r=JSON.parse(line);seen.set(r.post_id,r);}
const eastern=s=>new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).format(new Date(s));
function csv(){const rows=[...seen.values()];const fields=['platform','post_id','original_url','author_identifier','text','publication_timestamp','utc_timestamp','eastern_timestamp','query','retrieved_at','result_order','sample_date','text_truncated','language_status','quote_relationships','retrieval_method','window_status'];const esc=v=>'"'+String(typeof v==='object'?JSON.stringify(v):v??'').replaceAll('"','""')+'"';fs.writeFileSync(csvfile,'\ufeff'+fields.join(',')+'\r\n'+rows.map(r=>fields.map(k=>esc(r[k])).join(',')).join('\r\n'));}
function save(r){if(seen.has(r.post_id))return;seen.set(r.post_id,r);fs.appendFileSync(file,JSON.stringify(r)+'\n');csv();}
(async()=>{const c=await chromium.launchPersistentContext(path.join(root,'.browser-profile/x-pilot'),{headless:false,channel:'chrome',viewport:{width:1280,height:900}});const previousAudit=fs.existsSync(path.join(out,'x_m2_collection_audit.json'))?JSON.parse(fs.readFileSync(path.join(out,'x_m2_collection_audit.json'),'utf8')):[];const audit=[];const checkpointPath=path.join(out,'x_m2_resume_state.json');const checkpoint=fs.existsSync(checkpointPath)?JSON.parse(fs.readFileSync(checkpointPath,'utf8')):{};
try{for(const date of Array.from({length:23},(_,i)=>'2026-09-'+String(i+8).padStart(2,'0'))){
 const completed=previousAudit.find(a=>a.date===date);if(completed){audit.push(completed);continue;}
 let accepted=[...seen.values()].filter(r=>r.sample_date===date&&r.eastern_timestamp?.slice(0,10)===date&&!r.text_truncated).length;
 if(accepted>=20){audit.push({date,qualified:accepted,status:'cached success'});continue;}
 const q='("artificial intelligence" OR "generative AI" OR Anthropic) lang:en -filter:retweets since:'+date+' until:'+date;
 const p=await c.newPage();await p.goto('https://x.com/search?'+new URLSearchParams({q,f:'live',src:'typed_query'}),{waitUntil:'domcontentloaded',timeout:30000});const state=await ready(p,q);
 if(state.url_query!==q||state.search_box!==q||state.selected_tab!=='true')throw new Error('QueryStateMismatch');
 const old=checkpoint[date]||{};const visited=new Set(old.visited||[]);const rejected=old.rejected||{};let order=old.order||0,expansions=old.expansions||0;const store=(scrolls)=>{checkpoint[date]={visited:[...visited],rejected,order,expansions,scrolls_completed:scrolls,updated_at:new Date().toISOString()};fs.writeFileSync(checkpointPath,JSON.stringify(checkpoint,null,2));};
 for(let scroll=old.scrolls_completed||0;scroll<=10&&visited.size<100&&accepted<20;scroll++){
 await challenge(p);for(let r of await extract(p)){
  if(!r.post_id||visited.has(r.post_id))continue;visited.add(r.post_id);order++;
  let reason=null;const stamp=r.publication_timestamp;const utc=stamp&&Number.isFinite(Date.parse(stamp))?new Date(stamp).toISOString():null;const et=utc?eastern(utc):null;
  if(r.promoted)reason='promoted';else if(!r.matching_header)reason='author/status mismatch';else if(!r.text||!utc)reason='missing text/time';else if(et.slice(0,10)!==date)reason='out of Eastern day';else if(r.language!=='en')reason='English unverified';else if(r.reposted)reason='repost';else if(r.recommended)reason='recommended';else if(!/\b(artificial intelligence|generative AI|AI|Anthropic|OpenAI|ChatGPT|Claude|Gemini|machine learning|LLMs?|large language models?)\b/i.test(r.text))reason='no enclosing-text AI relevance';
  if(!reason&&r.text_truncated&&expansions>=10)reason='original expansion effort limit';if(!reason&&r.text_truncated){expansions++;const original=await c.newPage();await original.goto(r.original_url,{waitUntil:'domcontentloaded',timeout:30000});await original.locator('[data-testid="primaryColumn"] article').first().waitFor({timeout:12000}).catch(()=>{});await challenge(original);const full=(await extract(original)).find(x=>x.post_id===r.post_id&&x.matching_header&&x.publication_timestamp===stamp);
   await original.close();if(full&&!full.text_truncated)r={...r,text:full.text,text_truncated:false,quote_relationships:full.quote_relationships};else reason='truncated/unmatched original';}
  if(reason){rejected[reason]=(rejected[reason]||0)+1;store(scroll);continue;}
  if(!seen.has(r.post_id)){save({...r,platform:'X',utc_timestamp:utc,eastern_timestamp:et,query:q,retrieved_at:new Date().toISOString(),result_order:order,sample_date:date,language_status:'page lang=en; manual sentiment/relevance validation pending',window_status:'provisional 2026; analytical day America/New_York',retrieval_method:'authenticated Latest; individual enclosing post; same-day until empirically verified',record_type:'post'});accepted++;}
  store(scroll);if(accepted>=20||visited.size>=100)break;
 }
 if(scroll<10&&accepted<20){const box=await p.locator('[data-testid="primaryColumn"]').boundingBox();if(box)await p.mouse.move(box.x+box.width/2,600);await p.mouse.wheel(0,850);await p.waitForTimeout(2500);store(scroll+1);}
 }
 audit.push({date,qualified:accepted,unique_inspected:visited.size,rejected,...state,query:q,boundary_rule:'actual publication timestamp converted to America/New_York must equal requested day; observed until includes that local day',status:accepted?'pilot retrieved':'no qualified sample'});fs.writeFileSync(path.join(out,'x_m2_collection_audit.json'),JSON.stringify(audit,null,2));await p.close();await new Promise(res=>setTimeout(res,2500));
 }
 fs.writeFileSync(path.join(out,'x_m2_collection_audit.json'),JSON.stringify(audit,null,2));csv();
}finally{csv();await c.close();}})().catch(e=>console.log(JSON.stringify({stopped:true,error_type:e.name,reason:e.message==='AccessChallenge'?'account challenge/access denial':'operation failed; raw error suppressed'})));
