import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'outputs'
sample=json.loads((out/'validation_sample.json').read_text(encoding='utf-8'))
S='existential_safety'; E='economic_social'; B='benefits_opportunity'; I='investment_valuation'
# Codex judgments made from the fixed sample's actual primary texts, not market outcomes.
judgments=[
('negative',[S,E],'reports','negative','Hack/agent attack is adverse misuse; privacy implication is contextual. No body needed.'),
('negative',[B],'reports','mixed','Uneasy/shocked/boasting tone; solving a longstanding maths problem is implicit scientific benefit missed by phrases.'),
('negative',[],'uncertain','negative','Fear and concern dominate. Generic AI risks do not specify which risk category in this primary text.'),
('neutral',[],'not_applicable','uncertain','Political satire; waterslide quotation is not an identifiable AI attitude.'),
('negative',[E],'reports','negative','Denting job prospects and falling demand express economic harm; near-zero VADER misses it.'),
('negative',[S],'reports','negative','Rogue-agent incidents motivate inquiry; clinical wording does not make harm neutral.'),
('negative',[S,I],'reports','negative','Stock slide and reckless development are adverse; quoted dismissive sick conspiracy is attributed, not endorsed.'),
('negative',[S],'endorses','negative','Extinction threat and knowingly proceeding despite danger outweigh curiosity/profit; VADER positive is misleading.'),
('positive',[],'not_applicable','positive','Glamorous roles are positive tone; cultural reuse alone is not a specific listed benefit claim.'),
('negative',[S],'uncertain','mixed','Freaked out/doomsday concern plus uncertain policy; agree is not positive AI attitude.'),
('negative',[S,E],'reports','negative','Rogue activity and unauthorized image leaks explicitly implicate privacy and loss of control.'),
('negative',[E],'reports','negative','Environmental assessments and suspended planning convey environmental concern; no evidence of endorsed extinction risk.'),
('positive',[B],'not_applicable','positive','Optimistic educational opportunities are an explicit benefit framing.'),
('negative',[S,E],'endorses','negative','Bleak hack/security shortcomings; opportunity means remediation, not a benefit of AI. Strong protect/demand language inflates VADER.'),
('negative',[I],'endorses','negative','Bubble collapse/debt/worry are directly investment-risk framing.'),
('negative',[I,B],'reports','mixed','Bubble/inflation dominate; productivity benefits are discussed but explicitly not yet realized. Benefit flag is a mention, not endorsement.'),
('neutral',[S],'reports','mixed','Code of conduct and subordinate AI concern control/safety; service of people gives mild positive vocabulary, but primary is policy reporting.'),
('positive',[B],'not_applicable','positive','Claimed solution to a hard maths problem is scientific progress; stumped humans makes VADER falsely negative.'),
('negative',[S],'reports','negative','Fears of out-of-control agents; caution/slowdown contextual, not AI enthusiasm.'),
('negative',[],'not_applicable','negative','Accused/lobbying/alleged errors is adverse; no specific dictionary framing category established.'),
('negative',[S],'rejects','negative','Rejects doomer narrative while criticizing regulatory capture. Safety framing implicit in doomer; negative attitude is mainly toward Anthropic/regulation.'),
('negative',[],'not_applicable','negative','Sarcastic book destruction criticism, not a claim of human extinction. Copyright concern only implicit, so no forced category.'),
('negative',[S,B],'uncertain','mixed','Long hostile PR critique with threats to kill communities and explicit support for innovation; unrelated insults heavily affect VADER. Negation is not rejection of innovation.'),
('neutral',[],'not_applicable','negative','Typo/awkward double negation suggests opposition to Anthropic; weak generic emotional wording. AI attitude can differ from neutral tone.'),
('neutral',[],'not_applicable','uncertain','Question about blacklisting; no clear valence or categorized harm.'),
('negative',[],'not_applicable','uncertain','Alleged lawsuit/collusion is adverse; headline lacks specific listed risk type.'),
('positive',[],'not_applicable','positive','Tribute to mathematician/GPU naming; positive emotion and praise do not directly assert a listed AI benefit.'),
('negative',[],'not_applicable','uncertain','Not intelligent enough is criticism of state oversight; VADER mishandles multiword negation, not necessarily criticism of AI itself.'),
('negative',[S],'rejects','negative','Alignment theater/go rogue/grievances critique rejects moralized risk narrative. Reward functions should not turn skeptical tone positive.'),
('negative',[S],'reports','mixed','Reports disputed extinction estimates; alarming/scared language yields negative tone while risk endorsement is mixed.'),
('negative',[S,E],'uncertain','mixed','Extinction, control, deepfakes/fraud/misinformation explicitly discussed with qualifications. Climate-report correction is not rejection of all AI risks.'),
('negative',[E],'rejects','mixed','Explicitly rejects human replacement. Evil/defeated language is negative generic tone even though statement defends human agency.'),
('positive',[B],'uncertain','mixed','Useful tools praised with caveats; not perfect but useful is not rejection of usefulness. Double negatives and scope defeat simplistic stance.'),
('neutral',[],'not_applicable','uncertain','In a bubble means social/information isolation, not valuation excess; investment category false positive.'),
('positive',[B,I],'endorses','positive','Promotes orbital AI infrastructure advantages while explicitly listing investment/engineering execution risks. Capital expenditure alone is insufficient evidence; benefit claims are mostly paraphrases missed by rules.'),
('negative',[],'not_applicable','negative','Dangerous cult is company-directed insult. Does not specify extinction/misuse mechanism; no forced existential category.'),
('negative',[S,E],'uncertain','negative','Satirical attributed kill-you lines and Meta data collection raise safety/privacy themes; quotations are not literal company statements or author endorsements.'),
('positive',[B],'not_applicable','positive','Enthusiastic nursing adoption and patient/education benefits; experts word causes false attribution stance for a personal experience.'),
('neutral',[],'not_applicable','uncertain','Descriptive international open-source initiative. Lead/intelligence contribute positive VADER but no explicit praise.'),
('negative',[S,E],'reports','negative','Quoted unauthorized actions and made-up data imply loss of control and misinformation. A.I. safety variant missed initially; neutral/positive word safety masks adverse events.')
]
assert len(judgments)==len(sample)==40
reviews=[]
for r,(sentiment,frames,stance,attitude,notes) in zip(sample,judgments):
    reviews.append({'channel':r['channel'],'record_id':r['record_id'],'sentiment':sentiment,'framing':frames,'risk_stance':stance,'ai_attitude':attitude,'notes':notes,'reviewer_type':'Codex','independent_human_review':False,'body_context_used':False})
(out/'validation_reviews.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2),encoding='utf-8')
rulespath=ROOT/'src'/'framing_rules.json'
rules=json.loads(rulespath.read_text(encoding='utf-8'))
if rules['version']=='ai-framing-boundaries-v1':
    (out/'framing_rules_initial.json').write_text(json.dumps(rules,ensure_ascii=False,indent=2),encoding='utf-8')
    rules['version']='ai-framing-boundaries-v1.1'
    p=rules['categories']['existential_safety'][0]['pattern']
    p=p.replace('loss of control|lose control|out of control','loss[- ]of[- ]control|lose control|out[- ]of[- ]control').replace('AI safety|AI alignment',r'A\.?I\.?[- ]safety|A\.?I\.?[- ]alignment')
    rules['categories']['existential_safety'][0]['pattern']=p
    rules['categories']['existential_safety'][1]['pattern']=rules['categories']['existential_safety'][1]['pattern'].replace('rogue AI',r'rogue (?:AI|agents?)')
    rules['correction']='One correction: recognize orthographic/entity variants of existing control/safety concepts (out-of-control, A.I. safety/alignment, rogue agents). No sentiment tuning; other contextual errors remain limitations.'
    rulespath.write_text(json.dumps(rules,ensure_ascii=False,indent=2),encoding='utf-8')
print('Saved 40 Codex judgments and one safety-phrase variant correction.')
