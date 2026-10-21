"""Flex native + mixed decodes on Bhojpuri benchmark clips whose reference has spoken numbers."""
import sys, json, time
from pathlib import Path
sys.path.insert(0,"/home/user/indicASR-reliability-and-stress/code")
sys.path.insert(0,"/home/user/indicASR-reliability-and-stress/code/vendored/flex")
from guard.devanagari_numbers import number_runs, has_currency_word
from indic_transcribe import IndicTranscribe
D=Path("/tmp/claude-0/data/bho_lid")
rows=[json.loads(l) for l in (D/"manifest.jsonl").open() if l.strip()]
sel=[r for r in rows if r["split"]=="benchmark" and (number_runs(r["text"]) or has_currency_word(r["text"]))]
print("selected",len(sel),flush=True)
asr=IndicTranscribe.from_pretrained("/tmp/claude-0/models/flex",device="cpu")
out=D/"guard_flex.jsonl"; done=set()
if out.exists(): done={json.loads(l)["id"] for l in out.open()}
t0=time.time()
with out.open("a") as f:
    for n,r in enumerate(sel):
        if r["id"] in done: continue
        rec={"id":r["id"],"reference":r["text"],"district":r["district"],"duration":r["duration"]}
        try:
            for m in ("native","mixed"):
                rec[m]=asr.transcribe(r["path"],lang="bho",mode=m,max_new_tokens=256)
        except Exception as e: rec["err"]=repr(e)
        f.write(json.dumps(rec,ensure_ascii=False)+"\n"); f.flush()
        if n%20==0: print(n,len(sel),round(time.time()-t0),"s",flush=True)
