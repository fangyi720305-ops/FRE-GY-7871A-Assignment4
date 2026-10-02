const fs=require('fs'), path=require('path');
const root=path.resolve(__dirname,'..');
const runtime='C:/Users/fangyi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright';
const {chromium}=require(runtime);
const dates=['2026-09-08','2026-09-19','2026-09-30'];
const queries=['("artificial intelligence" OR "generative AI" OR Anthropic) lang:en -filter:retweets'];
const out=path.join(root,'data','processed'), logs=path.join(root,'outputs');
const profile=path.join(root,'.browser-profile','x-pilot');
fs.mkdirSync(out,{recursive:true});fs.mkdirSync(logs,{recursive:true});
const jsonl=path.join(out,'x_browser_pilot.jsonl');
const csvfile=path.join(out,'x_browser_pilot.csv');
const statusfile=path.join(logs,'x_browser_status.json');
const seen=new Map();
if(fs.existsSync(jsonl))for(const line of fs.readFileSync(jsonl,'utf8').split(/\r?\n/).filter(Boolean)){const r=JSON.parse(line);seen.set(r.post_id,r);}
const fields=['platform','post_id','original_url','author_handle','author_identifier','text','publication_timestamp','query','retrieved_at','result_order','sample_date','record_type','text_truncated','language_status','quote_relationships','boundary_status','window_status','retrieval_method'];
function csv(){const esc=v=>'"'+String(typeof v==='object'?JSON.stringify(v):v??'').replaceAll('"','""')+'"';fs.writeFileSync(csvfile,'\ufeff'+fields.join(',')+'\r\n'+[...seen.values()].map(r=>fields.map(k=>esc(r[k])).join(',')).join('\r\n'));}
const audit=[];
function status(state,details={}){fs.writeFileSync(statusfile,JSON.stringify({state,updated_at:new Date().toISOString(),...details},null,2));console.log(JSON.stringify({state,...details}));}
function save(r){if(seen.has(r.post_id))return;seen.set(r.post_id,r);fs.appendFileSync(jsonl,JSON.stringify(r)+'\n');csv();}
async function denied(page){
 const body=await page.locator('body').innerText().catch(()=> '');
 if(/verify you are human|authenticate your account|unusual activity|account (?:is )?(?:locked|suspended)|access denied|rate limit exceeded|too many requests|captcha|confirm your identity/i.test(body))return 'CAPTCHA/account challenge/access denial/rate limit';
 return null;
}
async function extract(page){return page.locator('article[data-testid="tweet"]').evaluateAll(nodes=>nodes.map((a,idx)=>{
 // A tweet's own header precedes its primary tweetText. Quote containers are usually links.
 const texts=[...a.querySelectorAll('[data-testid="tweetText"]')];
 const primary=texts.find(n=>!n.closest('[role="link"]'));
 const t=primary||texts[0];
 const quoteNodes=[...a.querySelectorAll('[role="link"]')].filter(n=>n.querySelector('[data-testid="tweetText"]'));
 const isQuote=n=>quoteNodes.some(q=>q.contains(n));
 const time=[...a.querySelectorAll('time[datetime]')].find(n=>!isQuote(n));
 const anchor=time?.closest('a[href*="/status/"]');const href=anchor?.getAttribute('href')||'';
 const match=href.match(/^\/([^/]+)\/status\/(\d+)/);
 const quotes=quoteNodes.map(q=>{const qt=q.querySelector('time');const qa=qt?.closest('a[href*="/status/"]')||q.querySelector('a[href*="/status/"]');return {text:q.querySelector('[data-testid="tweetText"]')?.innerText||'',status_url:qa?.href||null,publication_timestamp:qt?.getAttribute('datetime')||null,relationship:'quoted post',metadata_status:'unavailable fields remain null; never infer enclosing author/time'};});
 return {post_id:match?.[2]||null,author_handle:match?.[1]||null,original_url:match?'https://x.com/'+match[1]+'/status/'+match[2]:null,text:t?.innerText||'',publication_timestamp:time?.getAttribute('datetime')||null,text_truncated:!!a.querySelector('[data-testid="tweet-text-show-more-link"]')||/\bShow more\b/.test(t?.innerText||''),dom_language:t?.getAttribute('lang')||null,quote_relationships:quotes,result_order:idx+1,ambiguous_container:!primary};
 }));}
let context;
(async()=>{
 status('launching');
 context=await chromium.launchPersistentContext(profile,{headless:false,channel:'chrome',viewport:{width:1280,height:900}});
 const page=context.pages()[0]||await context.newPage();
 await page.goto('https://x.com/home',{waitUntil:'domcontentloaded',timeout:45000}).catch(()=>{});
 status('waiting_for_manual_login',{instructions:'Sign in manually in the dedicated Chrome window. No passwords or cookies are collected. Collector begins when normal authenticated navigation appears.'});
 const deadline=Date.now()+10*60*1000;
 while(Date.now()<deadline){
  const d=await denied(page);if(d){status('stopped_challenge',{reason:d});return;}
  if(await page.locator('[data-testid="SideNav_AccountSwitcher_Button"]').count())break;
  await page.waitForTimeout(2000);
 }
 if(!(await page.locator('[data-testid="SideNav_AccountSwitcher_Button"]').count())){status('login_not_completed');return;}
 status('authenticated_pilot_starting');
 for(const date of dates){
  const existing=[...seen.values()].filter(r=>r.sample_date===date&&r.boundary_status==='within UTC date'&&!r.text_truncated);
  if(existing.length>=10){audit.push({date,status:'cached qualified sample',qualified:existing.length});continue;}
  const end=new Date(Date.parse(date+'T00:00:00Z')+86400000).toISOString().slice(0,10);
  let eligible=existing.length,order=0,otherDate=0,incomplete=0;
  for(const base of queries){
   const query=base+' since:'+date+' until:'+end;
   await page.goto('https://x.com/search?'+new URLSearchParams({q:query,src:'typed_query',f:'live'}),{waitUntil:'domcontentloaded',timeout:45000}).catch(()=>{});
   await page.waitForTimeout(4000);let d=await denied(page);if(d){audit.push({date,status:'stopped',reason:d});status('stopped_challenge',{audit});return;}
   const latest=page.getByRole('tab',{name:'Latest',exact:true});
   if(await latest.count())await latest.click();
   if(!(await latest.count())||await latest.getAttribute('aria-selected')!=='true'){audit.push({date,status:'Latest ordering unverified; stopped'});status('search_failed',{audit});return;}
   let previous=seen.size,emptyRounds=0;
   for(let scroll=0;scroll<6&&eligible<10;scroll++){
    d=await denied(page);if(d){status('stopped_challenge',{reason:d,audit});return;}
    const found=await extract(page);
    for(let r of found){
     if(!r.post_id||seen.has(r.post_id))continue;order++;
     if(!r.text||!r.publication_timestamp||r.ambiguous_container){incomplete++;continue;}
     if(!Number.isFinite(Date.parse(r.publication_timestamp))){incomplete++;continue;}
     if(new Date(r.publication_timestamp).toISOString().slice(0,10)!==date){otherDate++;continue;}
     if(r.dom_language!=='en'){incomplete++;continue;}
     if(r.text_truncated){
      // Normal original navigation, no network interception or authenticated dump.
      const original=await context.newPage();await original.goto(r.original_url,{waitUntil:'domcontentloaded',timeout:30000}).catch(()=>{});await original.waitForTimeout(2500);
      d=await denied(original);if(d){await original.close();status('stopped_challenge',{reason:d,audit});return;}
      const full=(await extract(original)).find(p=>p.post_id===r.post_id);await original.close();
      if(full&&!full.text_truncated&&!full.ambiguous_container&&full.publication_timestamp===r.publication_timestamp)r={...r,text:full.text,text_truncated:false,quote_relationships:full.quote_relationships};
      if(r.text_truncated){incomplete++;continue;}
     }
     const record={...r,author_identifier:r.author_handle,platform:'X',record_type:'post',query,retrieved_at:new Date().toISOString(),result_order:order,sample_date:date,language_status:'page tweetText lang=en; manual review pending',boundary_status:'within UTC date',window_status:'provisional 2026',retrieval_method:'normal authenticated X Latest search; visible individual post DOM'};
     delete record.ambiguous_container;delete record.dom_language;save(record);eligible++;if(eligible>=10)break;
    }
    if(seen.size===previous)emptyRounds++;else emptyRounds=0;previous=seen.size;
    if(emptyRounds>=2)break;
    await page.mouse.wheel(0,650);await page.waitForTimeout(3500);
   }
  }
  audit.push({date,status:eligible?'pilot retrieved':'no qualified results',qualified:eligible,outside_requested_UTC_date:otherDate,incomplete_or_language_unverified:incomplete,max_eligible:10,ordering:'Latest',date_boundary:'since inclusive/until exclusive intended; actual timestamps individually checked against UTC calendar day; Eastern-day alignment unresolved'});
  status('pilot_progress',{audit});await page.waitForTimeout(5000);
 }
 csv();status('pilot_complete',{audit,total_unique_records:seen.size,archive_coverage:'not established'});
})().catch(e=>{status('error',{error_type:e.name,reason:'Browser operation failed; raw errors suppressed to avoid authentication leakage'});}).finally(async()=>{csv();if(context)await context.close().catch(()=>{});});
