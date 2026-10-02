import json,re
from pathlib import Path
P=Path(r'D:\School Work\FRE-GY 7871 NLP\Assignment 4');f=P/'data/processed/x_m2.jsonl';rows=[json.loads(l) for l in f.read_text(encoding='utf-8').splitlines() if l] if f.exists() else [];seen={r['post_id'] for r in rows}
for l in (P/'data/processed/x_browser_pilot.jsonl').read_text(encoding='utf-8').splitlines():
 if not l:continue
 r=json.loads(l)
 if r['post_id'] not in seen and r.get('matching_header') and not r.get('text_truncated') and re.search(r'\b(artificial intelligence|generative AI|AI|Anthropic|OpenAI|ChatGPT|Claude|Gemini|machine learning|LLMs?|large language models?)\b',r['text'],re.I):
  with f.open('a',encoding='utf-8') as out:out.write(json.dumps(r,ensure_ascii=False)+'\n')
  seen.add(r['post_id'])
helper=P/'src/x_debug.cjs';s=helper.read_text(encoding='utf-8');s=s.replace('promoted:/\\bPromoted\\b/.test(a.innerText),','promoted:/\\bPromoted\\b/.test(a.innerText),reposted:/\\breposted\\b/i.test(a.querySelector(\'[data-testid="socialContext"]\')?.innerText||\'\'),recommended:/recommended|because you follow|liked/i.test(a.querySelector(\'[data-testid="socialContext"]\')?.innerText||\'\'),');helper.write_text(s,encoding='utf-8')
print(json.dumps({'eligible_cached_pilot_reused':len(seen)}))
