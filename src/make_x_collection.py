from pathlib import Path
P=Path(r'D:\School Work\FRE-GY 7871 NLP\Assignment 4')
s=(P/'src/x_browser_pilot.cjs').read_text(encoding='utf-8')
s=s.replace("'x_browser_pilot.jsonl'","'x_m2.jsonl'").replace("'x_browser_pilot.csv'","'x_clean.csv'").replace("'x_browser_fixed_audit.json'","'x_m2_collection_audit.json'")
s=s.replace("['2026-09-08','2026-09-19','2026-09-30']","Array.from({length:23},(_,i)=>'2026-09-'+String(i+8).padStart(2,'0'))")
s=s.replace('accepted>=10','accepted>=20').replace('accepted<10','accepted<20').replace('scroll<=5','scroll<=10').replace('scroll<5','scroll<10').replace('visited.size<50','visited.size<100').replace('visited.size>=50','visited.size>=100').replace('2200','2500')
s=s.replace('const visited=new Set();const rejected={};let order=0;','const visited=new Set();const rejected={};let order=0,expansions=0;')
s=s.replace("else if(r.language!=='en')reason='English unverified';","else if(r.language!=='en')reason='English unverified';else if(r.reposted)reason='repost';else if(r.recommended)reason='recommended';else if(!/\\b(artificial intelligence|generative AI|AI|Anthropic|OpenAI|ChatGPT|Claude|Gemini|machine learning|LLMs?|large language models?)\\b/i.test(r.text))reason='no enclosing-text AI relevance';")
s=s.replace('if(!reason&&r.text_truncated){const original=',"if(!reason&&r.text_truncated&&expansions>=10)reason='original expansion effort limit';if(!reason&&r.text_truncated){expansions++;const original=")
# Incremental day audit survives a later access failure. All already successful sample checks are reused.
s=s.replace("console.log(JSON.stringify({date,qualified:accepted,unique_inspected:visited.size,rejected}));", "fs.writeFileSync(path.join(out,'x_m2_collection_audit.json'),JSON.stringify(audit,null,2));")
start=s.index(' // Verify three eligible original pages');end=s.index('}finally{',start)
s=s[:start]+s[end:]
(P/'src/x_collect_m2.cjs').write_text(s,encoding='utf-8')
