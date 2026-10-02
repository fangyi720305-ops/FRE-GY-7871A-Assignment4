const {chromium}=require('C:/Users/fangyi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path');const root=path.resolve(__dirname,'..');
(async()=>{const c=await chromium.launchPersistentContext(path.join(root,'.browser-profile/x-pilot'),{headless:false,channel:'chrome'});
try{const p=c.pages()[0]||await c.newPage();const records=[];
for(const date of ['2026-09-08','2026-09-19','2026-09-30']){
 const end=new Date(Date.parse(date+'T00:00:00Z')+86400000).toISOString().slice(0,10);
 const q='("artificial intelligence" OR "generative AI" OR Anthropic) lang:en since:'+date+' until:'+end+' -filter:retweets';
 await p.goto('https://x.com/search?'+new URLSearchParams({q,f:'live',src:'typed_query'}),{waitUntil:'domcontentloaded'});await p.waitForTimeout(4000);
 const body=await p.locator('body').innerText();if(/captcha|verify you are human|authenticate your account|access denied|rate limit exceeded|too many requests/i.test(body)){console.log('Stopped on challenge');break;}
 const latest=p.getByRole('tab',{name:'Latest',exact:true});if(!(await latest.count())||await latest.getAttribute('aria-selected')!=='true'){console.log('Latest unavailable');break;}
 const samples=await p.locator('article[data-testid="tweet"]').evaluateAll(as=>as.slice(0,3).map(a=>{
 const quote=[...a.querySelectorAll('[role="link"]')].filter(n=>n.querySelector('[data-testid="tweetText"]'));
 const own=n=>!quote.some(q=>q.contains(n));const t=[...a.querySelectorAll('time[datetime]')].find(own);const link=t?.closest('a');const text=[...a.querySelectorAll('[data-testid="tweetText"]')].find(own);
 return {original_url:link?.href||null,publication_timestamp:t?.getAttribute('datetime')||null,text:text?.innerText||'',language:text?.getAttribute('lang')||null,text_truncated:!!a.querySelector('[data-testid="tweet-text-show-more-link"]')};}));
 for(const r of samples)records.push({...r,platform:'X',requested_date:date,query:q,retrieved_at:new Date().toISOString(),retrieval_method:'visible Latest result; boundary diagnostic only',eligible_for_analysis:false});
 console.log(JSON.stringify({requested_date:date,observed_timestamps:samples.map(r=>r.publication_timestamp)}));await p.waitForTimeout(3000);
}
fs.writeFileSync(path.join(root,'data/processed/x_boundary_examples.jsonl'),records.map(r=>JSON.stringify(r)).join('\n')+'\n');
}finally{await c.close();}})().catch(e=>console.log('Diagnostic error type: '+e.name));
