"""Re-measure auto-LID (identify) for Core/Flex on UNPADDED Rural_Women_Bhojpuri audio.
Usage: lid_v2.py stage | lid_v2.py run core|flex
"""
import os, sys, json, io, time
from pathlib import Path
OUT=Path("/tmp/claude-0/data/bho_lid"); OUT.mkdir(parents=True,exist_ok=True)
MAN=OUT/"manifest.jsonl"
def stage():
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download
    rows=[]
    for split in ("benchmark","train_real"):
        p=hf_hub_download("ai4bharat/Rural_Women_Bhojpuri",f"data/{split}-00000-of-00001.parquet",repo_type="dataset",token=os.environ["HF_TOKEN"])
        pf=pq.ParquetFile(p); i=0
        for batch in pf.iter_batches(batch_size=32):
            for r in batch.to_pylist():
                a=r["audio"]; lang=r.get("lang") or {"bhojpuri":"bho","hindi":"hi"}.get(r.get("language"),r.get("language"))
                if not a or not a.get("bytes"): continue
                sid=f"{split}-{i:04d}"; i+=1
                wav=OUT/"audio"/f"{sid}.wav"; wav.parent.mkdir(exist_ok=True); wav.write_bytes(a["bytes"])
                rows.append({"id":sid,"split":split,"lang":lang,"speaker_id":r.get("speaker_id"),"district":r.get("district"),"scenario":r.get("scenario"),"duration":r.get("duration"),"text":r.get("text"),"path":str(wav)})
    MAN.write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in rows)+"\n")
    import collections; print(len(rows),collections.Counter((x["split"],x["lang"]) for x in rows))
def run(vendor):
    sys.path.insert(0,f"/home/user/indicASR-reliability-and-stress/code/vendored/{vendor}")
    from indic_transcribe import IndicTranscribe
    asr=IndicTranscribe.from_pretrained(f"/tmp/claude-0/models/{vendor}",device="cpu")
    outp=OUT/f"lid_{vendor}.jsonl"; done=set()
    if outp.exists(): done={json.loads(l)["id"] for l in outp.open()}
    rows=[json.loads(l) for l in MAN.open()]; t0=time.time()
    with outp.open("a") as f:
        for n,r in enumerate(rows):
            if r["id"] in done: continue
            try: top=asr.identify(r["path"],topk=5); err=None
            except Exception as e: top=None; err=repr(e)
            f.write(json.dumps({"id":r["id"],"vendor":vendor,"topk":top,"err":err},ensure_ascii=False)+"\n"); f.flush()
            if n%50==0: print(vendor,n,len(rows),round(time.time()-t0),"s",flush=True)
if __name__=="__main__":
    stage() if sys.argv[1]=="stage" else run(sys.argv[2])
