import re,json,time
# Existing JSON failures are not repeated; ordinary original HTML pages are a distinct route.
from urllib.request import Request,urlopen
from pathlib import Path
P=Path(r'D:\School Work\FRE-GY 7871 NLP\Assignment 4'); audit=[]
urls=[('start','https://www.reddit.com/r/singularity/comments/1wayu26/openai_putting_safety_first/'),('middle','https://www.reddit.com/r/techsupport/comments/1wkbnae/firefox_deletes_chatgpt_cookies_despite_cookie/'),('end','https://www.reddit.com/r/singularity/comments/1wtnm5v/i_think_something_might_be_happening/')]
for name,url in urls:
 try:
  with urlopen(Request(url,headers={'User-Agent':'Assignment4HistoricalPilot/1.0'}),timeout=20) as r:raw=r.read().decode('utf-8'); status=r.status
  (P/'data/raw'/('reddit_html_'+name+'.html')).write_text(raw,encoding='utf-8')
  print(name,status,'bytes',len(raw),'times',re.findall(r'datetime="([^"]+)"',raw)[:4])
  audit.append({'route':'Reddit original HTML '+name,'url':url,'status':status,'bytes':len(raw)})
 except Exception as e:
  status='HTTP '+str(e.code) if hasattr(e,'code') else type(e).__name__; print(name,status);audit.append({'route':'Reddit original HTML '+name,'url':url,'status':status})
 time.sleep(1)
(P/'outputs/reddit_html_routes.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
