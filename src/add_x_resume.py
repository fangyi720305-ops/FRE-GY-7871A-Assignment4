from pathlib import Path
P=Path(r'D:\School Work\FRE-GY 7871 NLP\Assignment 4');f=P/'src/x_collect_m2.cjs';s=f.read_text(encoding='utf-8')
if 'checkpointPath' not in s:
 s=s.replace('const audit=[];',"const previousAudit=fs.existsSync(path.join(out,'x_m2_collection_audit.json'))?JSON.parse(fs.readFileSync(path.join(out,'x_m2_collection_audit.json'),'utf8')):[];const audit=[];const checkpointPath=path.join(out,'x_m2_resume_state.json');const checkpoint=fs.existsSync(checkpointPath)?JSON.parse(fs.readFileSync(checkpointPath,'utf8')):{};")
 s=s.replace(' let accepted='," const completed=previousAudit.find(a=>a.date===date);if(completed){audit.push(completed);continue;}\n let accepted=")
 s=s.replace('const visited=new Set();const rejected={};let order=0,expansions=0;',"const old=checkpoint[date]||{};const visited=new Set(old.visited||[]);const rejected=old.rejected||{};let order=old.order||0,expansions=old.expansions||0;const store=(scrolls)=>{checkpoint[date]={visited:[...visited],rejected,order,expansions,scrolls_completed:scrolls,updated_at:new Date().toISOString()};fs.writeFileSync(checkpointPath,JSON.stringify(checkpoint,null,2));};")
 s=s.replace('for(let scroll=0;scroll<=10','for(let scroll=old.scrolls_completed||0;scroll<=10')
 s=s.replace("if(reason){rejected[reason]=(rejected[reason]||0)+1;continue;}","if(reason){rejected[reason]=(rejected[reason]||0)+1;store(scroll);continue;}")
 s=s.replace('if(accepted>=20||visited.size>=100)break;','store(scroll);if(accepted>=20||visited.size>=100)break;')
 s=s.replace('await p.mouse.wheel(0,850);await p.waitForTimeout(2500);','await p.mouse.wheel(0,850);await p.waitForTimeout(2500);store(scroll+1);')
 f.write_text(s,encoding='utf-8')
print('Resume checkpoints added; completed effort-limited days are preserved.')
