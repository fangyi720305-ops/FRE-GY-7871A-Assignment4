// Bounded pilot using verified Eastern-day endpoint behavior; no full collection.
const fs=require('fs'),path=require('path');const {chromium}=require('C:/Users/fangyi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');const {extract,ready,challenge}=require('./x_debug.cjs');
const root=path.resolve(__dirname,'..'),out=path.join(root,'outputs'),data=path.join(root,'data/processed');
const file=path.join(data,'x_browser_pilot.jsonl'),csvfile=path.join(data,'x_browser_pilot.csv');const seen=new Map();if(fs.existsSync(file))for(const line of fs.readFileSync(file,'utf8').split('\n').filter(Boolean)){const r=JSON.parse(line);seen.set(r.post_id,r);}
const eastern=s=>new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).format(new Date(s));
function csv(){const rows=[...seen.values()];const fields=['platform','post_id','original_url','author_identifier','text','publication_timestamp','utc_timestamp','eastern_timestamp','query','retrieved_at','result_order','sample_date','text_truncated','language_status','quote_relationships','retrieval_method','window_status'];const esc=v=>'"'+String(typeof v==='object'?JSON.stringify(v):v??'').replaceAll('"','""')+'"';fs.writeFileSync(csvfile,'\ufeff'+fields.join(',')+'\r\n'+rows.map(r=>fields.map(k=>esc(r[k])).join(',')).join('\r\n'));}
function save(r){if(seen.has(r.post_id))return;seen.set(r.post_id,r);fs.appendFileSync(file,JSON.stringify(r)+'\n');csv();}
(async()=>{const c=await chromium.launchPersistentContext(path.join(root,'.browser-profile/x-pilot'),{headless:false,channel:'chrome',viewport:{width:1280,height:900}});const audit=[];
try{for(const date of ['2026-09-08','2026-09-19','2026-09-30']){
 let accepted=[...seen.values()].filter(r=>r.sample_date===date&&r.eastern_timestamp?.slice(0,10)===date&&!r.text_truncated).length;
 if(accepted>=10){audit.push({date,qualified:accepted,status:'cached success'});continue;}
 const q='("artificial intelligence" OR "generative AI" OR Anthropic) lang:en -filter:retweets since:'+date+' until:'+date;
 const p=await c.newPage();await p.goto('https://x.com/search?'+new URLSearchParams({q,f:'live',src:'typed_query'}),{waitUntil:'domcontentloaded',timeout:30000});const state=await ready(p,q);
 if(state.url_query!==q||state.search_box!==q||state.selected_tab!=='true')throw new Error('QueryStateMismatch');
 const visited=new Set();const rejected={};let order=0;
 for(let scroll=0;scroll<=5&&visited.size<50&&accepted<10;scroll++){
 await challenge(p);for(let r of await extract(p)){
  if(!r.post_id||visited.has(r.post_id))continue;visited.add(r.post_id);order++;
  let reason=null;const stamp=r.publication_timestamp;const utc=stamp&&Number.isFinite(Date.parse(stamp))?new Date(stamp).toISOString():null;const et=utc?eastern(utc):null;
  if(r.promoted)reason='promoted';else if(!r.matching_header)reason='author/status mismatch';else if(!r.text||!utc)reason='missing text/time';else if(et.slice(0,10)!==date)reason='out of Eastern day';else if(r.language!=='en')reason='English unverified';
  if(!reason&&r.text_truncated){const original=await c.newPage();await original.goto(r.original_url,{waitUntil:'domcontentloaded',timeout:30000});await original.locator('[data-testid="primaryColumn"] article').first().waitFor({timeout:12000}).catch(()=>{});await challenge(original);const full=(await extract(original)).find(x=>x.post_id===r.post_id&&x.matching_header&&x.publication_timestamp===stamp);
   await original.close();if(full&&!full.text_truncated)r={...r,text:full.text,text_truncated:false,quote_relationships:full.quote_relationships};else reason='truncated/unmatched original';}
  if(reason){rejected[reason]=(rejected[reason]||0)+1;continue;}
  if(!seen.has(r.post_id)){save({...r,platform:'X',utc_timestamp:utc,eastern_timestamp:et,query:q,retrieved_at:new Date().toISOString(),result_order:order,sample_date:date,language_status:'page lang=en; manual sentiment/relevance validation pending',window_status:'provisional 2026; analytical day America/New_York',retrieval_method:'authenticated Latest; individual enclosing post; same-day until empirically verified',record_type:'post'});accepted++;}
  if(accepted>=10||visited.size>=50)break;
 }
 if(scroll<5&&accepted<10){const box=await p.locator('[data-testid="primaryColumn"]').boundingBox();if(box)await p.mouse.move(box.x+box.width/2,600);await p.mouse.wheel(0,850);await p.waitForTimeout(2200);}
 }
 audit.push({date,qualified:accepted,unique_inspected:visited.size,rejected,...state,query:q,boundary_rule:'actual publication timestamp converted to America/New_York must equal requested day; observed until includes that local day',status:accepted?'pilot retrieved':'no qualified sample'});console.log(JSON.stringify({date,qualified:accepted,unique_inspected:visited.size,rejected}));await p.close();await new Promise(res=>setTimeout(res,2500));
 }
 fs.writeFileSync(path.join(out,'x_browser_fixed_audit.json'),JSON.stringify(audit,null,2));csv();
 // Verify three eligible original pages using ID matched extraction, not first time.
 const checks=[];for(const r of [...seen.values()].filter(r=>r.eastern_timestamp).slice(0,3)){
 const p=await c.newPage();await p.goto(r.original_url,{waitUntil:'domcontentloaded'});await p.locator('[data-testid="primaryColumn"] article').first().waitFor({timeout:12000}).catch(()=>{});await challenge(p);const original=(await extract(p)).find(x=>x.post_id===r.post_id&&x.matching_header);checks.push({id:r.post_id,url:r.original_url,search_timestamp:r.publication_timestamp,original_timestamp:original?.publication_timestamp||null,author_match:original?.author_identifier===r.author_identifier,text_match:original?.text===r.text,own_timestamp_match:original?.publication_timestamp===r.publication_timestamp});await p.close();}
 fs.writeFileSync(path.join(out,'x_fixed_original_checks.json'),JSON.stringify(checks,null,2));console.log(JSON.stringify({original_checks:checks}));
}finally{csv();await c.close();}})().catch(e=>console.log(JSON.stringify({stopped:true,error_type:e.name,reason:e.message==='AccessChallenge'?'account challenge/access denial':'operation failed; raw error suppressed'})));
