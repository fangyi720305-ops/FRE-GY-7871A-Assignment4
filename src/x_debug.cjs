const fs=require('fs'),path=require('path');const {chromium}=require('C:/Users/fangyi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..'),out=path.join(root,'outputs'),data=path.join(root,'data/processed');
const eastern=iso=>new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).format(new Date(iso));
async function challenge(p){const check=await p.evaluate(()=>{let text=document.body.innerText;let postMatches=0;const pattern=/verify you are human|authenticate your account|unusual activity|account (?:is )?(?:locked|suspended)|access denied|rate limit exceeded|too many requests|captcha|confirm your identity/i;for(const a of document.querySelectorAll('article[data-testid="tweet"]')){if(pattern.test(a.innerText))postMatches++;text=text.replace(a.innerText,'');}const match=text.match(pattern);return {interface_match:match?.[0]||null,post_keyword_matches:postMatches};});if(check.post_keyword_matches)console.log(JSON.stringify({safety_check:'challenge keywords found only in public post text unless interface_match set',...check}));if(check.interface_match){fs.writeFileSync(path.join(out,'x_debug_challenge.json'),JSON.stringify({stopped:true,url:p.url(),reason:check.interface_match,checked_at:new Date().toISOString()},null,2));throw new Error('AccessChallenge');}}
async function extract(p){const timeline=p.locator('[data-testid="primaryColumn"] [aria-label="Timeline: Search timeline"]');const scope=await timeline.count()?timeline:p.locator('[data-testid="primaryColumn"]');return scope.locator('article[data-testid="tweet"]').evaluateAll(as=>as.map(a=>{
 const quoteNodes=[...a.querySelectorAll('[role="link"], [data-testid="quoteTweet"]')].filter(q=>q.querySelector('[data-testid="tweetText"]'));
 const own=n=>!quoteNodes.some(q=>q.contains(n));const ownText=[...a.querySelectorAll('[data-testid="tweetText"]')].find(own);
 const header=[...a.querySelectorAll('[data-testid="User-Name"]')].find(own);
 const t=[...a.querySelectorAll('time[datetime]')].find(n=>own(n)&&/^\/[^/]+\/status\/\d+/.test(n.closest('a')?.getAttribute('href')||''));const href=t?.closest('a')?.getAttribute('href')||'';const m=href.match(/^\/([^/]+)\/status\/(\d+)/);
 const handle=header?.innerText.match(/@[A-Za-z0-9_]+/)?.[0]?.slice(1)||null;
 return {post_id:m?.[2]||null,original_url:m?'https://x.com/'+m[1]+'/status/'+m[2]:null,author_identifier:handle,link_author:m?.[1]||null,text:ownText?.innerText||'',publication_timestamp:t?.getAttribute('datetime')||null,language:ownText?.getAttribute('lang')||null,text_truncated:!!a.querySelector('[data-testid="tweet-text-show-more-link"]'),matching_header:!!m&&handle?.toLowerCase()===m[1].toLowerCase(),promoted:/\bPromoted\b/.test(a.innerText),reposted:/\breposted\b/i.test(a.querySelector('[data-testid="socialContext"]')?.innerText||''),recommended:/recommended|because you follow|liked/i.test(a.querySelector('[data-testid="socialContext"]')?.innerText||''),quote_relationships:quoteNodes.filter(q=>!quoteNodes.some(other=>other!==q&&other.contains(q))).map(q=>({text:q.querySelector('[data-testid="tweetText"]')?.innerText||'',status_url:q.querySelector('a[href*="/status/"]')?.href||null,timestamp:q.querySelector('time')?.getAttribute('datetime')||null}))};}));}
async function ready(p,q){
 await p.locator('input[data-testid="SearchBox_Search_Input"]').waitFor({timeout:15000});
 const latest=p.getByRole('tab',{name:'Latest',exact:true});await latest.waitFor({timeout:15000});
 if(await latest.getAttribute('aria-selected')!=='true')await latest.click();
 await p.locator('[data-testid="primaryColumn"] article[data-testid="tweet"]').first().waitFor({timeout:12000}).catch(()=>{});await challenge(p);
 return {final_url:p.url(),url_query:new URL(p.url()).searchParams.get('q'),search_box:await p.locator('input[data-testid="SearchBox_Search_Input"]').inputValue(),selected_tab:await latest.getAttribute('aria-selected'),timeline_labels:await p.locator('[data-testid="primaryColumn"] [aria-label^="Timeline:"]').evaluateAll(ns=>ns.map(n=>n.getAttribute('aria-label'))),no_results:/No results for/.test(await p.locator('[data-testid="primaryColumn"]').innerText())};
}
async function collect(p,q,label,from='2026-09-19',to='2026-09-20',navigate=true){
 const fresh=!p.url().includes('/search');if(navigate)await p.goto('https://x.com/search?'+new URLSearchParams({q,src:'typed_query',f:'live'}),{waitUntil:'domcontentloaded',timeout:30000});
 const state=await ready(p,q);if(state.url_query!==q||state.search_box!==q||state.selected_tab!=='true')throw new Error('SearchStateMismatch');
 const seen=new Map();let missing=0;
 for(let s=0;s<=5&&seen.size<50;s++){
  await challenge(p);for(const r of await extract(p)){
   if(!r.post_id){missing++;continue;}if(seen.has(r.post_id))continue;
   let reason='eligible';if(r.promoted)reason='promoted';else if(!r.matching_header)reason='author/status mismatch';else if(!r.text||!r.publication_timestamp)reason='missing text/time';else if(r.text_truncated)reason='truncated';else if(r.language!=='en')reason='English unverified';
   const utc=r.publication_timestamp&&Number.isFinite(Date.parse(r.publication_timestamp))?new Date(r.publication_timestamp).toISOString():null;
   const et=utc?eastern(utc):null;const localDate=et?.slice(0,10);
   if(reason==='eligible'&&!(localDate>=from&&localDate<to))reason='out of Eastern window';
   seen.set(r.post_id,{...r,platform:'X',query:q,retrieval_time:new Date().toISOString(),result_order:seen.size+1,utc_timestamp:utc,eastern_timestamp:et,eligible:reason==='eligible',rejection_reason:reason,label,retrieval_method:'visible authenticated Latest search; primary results column; post scoped'});if(seen.size>=50)break;
  }
  if(s<5){const box=await p.locator('[data-testid="primaryColumn"]').boundingBox();if(box)await p.mouse.move(box.x+box.width/2,600);await p.mouse.wheel(0,850);await p.waitForTimeout(2200);}
 }
 const records=[...seen.values()];fs.writeFileSync(path.join(data,'x_debug_'+label+'.jsonl'),records.map(r=>JSON.stringify(r)).join('\n')+'\n');
 const reasons={};for(const r of records)reasons[r.rejection_reason]=(reasons[r.rejection_reason]||0)+1;
 const diag={label,submitted_query:q,...state,fresh_page:fresh,unique_records:records.length,counts:reasons,unmatched_containers:missing,first_timestamps:records.slice(0,5).map(r=>({id:r.post_id,utc:r.utc_timestamp,eastern:r.eastern_timestamp}))};
 fs.writeFileSync(path.join(out,'x_debug_'+label+'.json'),JSON.stringify(diag,null,2));console.log(JSON.stringify(diag));return records;
}
async function originals(c,records){const evidence=[];
 for(const r of records.slice(0,3)){
  const p=await c.newPage();await p.goto(r.original_url,{waitUntil:'domcontentloaded'});await p.locator('[data-testid="primaryColumn"] article').first().waitFor({timeout:12000}).catch(()=>{});await challenge(p);
  const detail=await p.locator('[data-testid="primaryColumn"] article[data-testid="tweet"]').evaluateAll((as,id)=>as.map(a=>{
   const quoted=[...a.querySelectorAll('[role="link"], [data-testid="quoteTweet"]')].filter(q=>q.querySelector('[data-testid="tweetText"]'));const own=n=>!quoted.some(q=>q.contains(n));
   const header=[...a.querySelectorAll('[data-testid="User-Name"]')].find(own);const times=[...a.querySelectorAll('time')].filter(own).map(t=>({datetime:t.getAttribute('datetime'),href:t.closest('a')?.getAttribute('href')}));
   const statusLinks=[...a.querySelectorAll('a[href*="/status/"]')].filter(own).filter(x=>new RegExp('/status/'+id+'(?:$|[/?])').test(x.getAttribute('href'))).map(x=>({href:x.getAttribute('href'),text:x.innerText,datetime:x.querySelector('time')?.getAttribute('datetime')||null}));
   return {header:header?.innerText||'',text:[...a.querySelectorAll('[data-testid="tweetText"]')].find(own)?.innerText||'',times,matching_status_links:statusLinks};}),r.post_id);
  evidence.push({id:r.post_id,url:r.original_url,search_author:r.author_identifier,search_time:r.publication_timestamp,search_text:r.text,detail:detail.slice(0,1)});await p.close();await new Promise(res=>setTimeout(res,1800));
 }
 fs.writeFileSync(path.join(out,'x_debug_original_matches.json'),JSON.stringify(evidence,null,2));console.log(JSON.stringify({originals:evidence.map(e=>({id:e.id,header:e.detail[0]?.header,times:e.detail[0]?.times,status_links:e.detail[0]?.matching_status_links,text_matches:e.search_text===e.detail[0]?.text}))}));}
if(require.main===module)(async()=>{const c=await chromium.launchPersistentContext(path.join(root,'.browser-profile/x-pilot'),{headless:false,channel:'chrome',viewport:{width:1280,height:900}});
try{const p=await c.newPage();if(!process.argv.includes('--advanced')){const records=await collect(p,'AI since:2026-09-19 until:2026-09-20','simple');await originals(c,records);}
 await p.goto('https://x.com/search-advanced',{waitUntil:'domcontentloaded',timeout:30000});await p.getByRole('dialog').waitFor({timeout:15000}).catch(()=>{});await challenge(p);
 const controls=await p.locator('input,select,button[role="button"]').evaluateAll(ns=>ns.map(n=>({tag:n.tagName,type:n.getAttribute('type'),name:n.getAttribute('name'),aria_label:n.getAttribute('aria-label'),placeholder:n.getAttribute('placeholder'),value:n.tagName==='SELECT'?n.value:undefined,options:n.tagName==='SELECT'?[...n.options].map(o=>({text:o.text,value:o.value})):undefined})).filter(n=>n.type!=='password'));
 fs.writeFileSync(path.join(out,'x_advanced_form_controls.json'),JSON.stringify(controls,null,2));console.log(JSON.stringify({advanced_url:p.url(),advanced_controls:controls,primary_text:(await p.locator('[data-testid="primaryColumn"]').innerText().catch(()=>'' )).slice(0,1000),dialogs:await p.getByRole('dialog').count(),buttons:await p.locator('[data-testid="primaryColumn"] button').evaluateAll(ns=>ns.map(n=>({text:n.innerText,label:n.getAttribute('aria-label')})))}));
}finally{await c.close();}})().catch(e=>console.log(JSON.stringify({stopped:true,error_type:e.name,reason:e.message==='AccessChallenge'?'challenge/denial':e.message==='SearchStateMismatch'?'query state mismatch':'operation failed; details suppressed'})));
module.exports={collect,originals,ready,extract,challenge};
