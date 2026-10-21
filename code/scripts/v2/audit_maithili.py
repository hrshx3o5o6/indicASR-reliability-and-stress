import os, sys, json, collections
import pyarrow.parquet as pq
from huggingface_hub import HfFileSystem, HfApi
tok=os.environ["HF_TOKEN"]
fs=HfFileSystem(token=tok)
files=sorted(f for f in fs.ls("datasets/ai4bharat/IndicVoices/maithili", detail=False) if f.endswith(".parquet"))
print("shards",len(files), files[:2], files[-2:])
# schema from first shard
with fs.open(files[0],"rb") as fh:
    pf=pq.ParquetFile(fh); print("schema:", pf.schema_arrow.names, "rows/shard", pf.metadata.num_rows)
cols=["speaker_id","scenario","duration","lang","gender","age_group"]
want=[c for c in cols if c in pf.schema_arrow.names]
sp=collections.Counter(); sc=collections.Counter(); dur=collections.defaultdict(float); n=0
sample=[int(x) for x in sys.argv[1].split(",")] if len(sys.argv)>1 else range(len(files))
for i in sample:
    with fs.open(files[i],"rb") as fh:
        t=pq.read_table(fh, columns=want)
    d=t.to_pydict(); n+=t.num_rows
    for k in range(t.num_rows):
        sp[d["speaker_id"][k]]+=1; sc[d["scenario"][k]]+=1; dur[d["scenario"][k]]+=d["duration"][k]
    print("shard",i,"rows",t.num_rows,"cum speakers",len(sp),flush=True)
print("rows",n,"speakers",len(sp)); print("scenario",dict(sc)); print("hours by scenario",{k:round(v/3600,1) for k,v in dur.items()})
print("clips/speaker top",sp.most_common(5), "speakers>=5 clips", sum(1 for v in sp.values() if v>=5))
json.dump({"shards_scanned":list(sample),"rows":n,"speakers":len(sp),"scenario":sc,"clips_per_speaker":sp},open("/tmp/claude-0/audit/maithili_audit.json","w"),ensure_ascii=False)
