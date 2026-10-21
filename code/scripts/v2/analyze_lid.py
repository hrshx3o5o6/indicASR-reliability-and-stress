import json,sys,math,collections
D="/tmp/claude-0/data/bho_lid"
vendor=sys.argv[1]
man={}
for l in open(f"{D}/manifest.jsonl"):
    r=json.loads(l); man[r["id"]]=r
res=[json.loads(l) for l in open(f"{D}/lid_{vendor}.jsonl")]
def wilson(k,n,z=1.96):
    if n==0: return (0,0)
    p=k/n; d=1+z*z/n; c=p+z*z/(2*n); a=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return ((c-a)/d,(c+a)/d)
groups=collections.defaultdict(list)
for r in res:
    m=man[r["id"]]
    if not r["topk"]: continue
    groups[(m["split"],m["lang"])].append((m,r["topk"][0][0],r["topk"]))
print(f"== {vendor}: LID top-1 on UNPADDED clips ==")
for (split,lang),v in sorted(groups.items()):
    n=len(v); k=sum(t==lang for _,t,_ in v); lo,hi=wilson(k,n)
    conf=collections.Counter(t for _,t,_ in v if t!=lang)
    spk=len({m["speaker_id"] for m,_,_ in v if m["speaker_id"]})
    print(f"{split:10s} {lang}: {k}/{n} = {100*k/n:5.1f}%  Wilson95 [{100*lo:.1f},{100*hi:.1f}]  speakers={spk}  wrong->{dict(conf.most_common(4))}")
for split in ("benchmark","train_real"):
    v=groups.get((split,"bho"),[])
    if v:
        c3=sum(any(l==m["lang"] for l,_ in tk[:3]) for m,_,tk in v); print(f"{split} bho truth in top-3: {c3}/{len(v)}")
for key in ("scenario","district"):
    c=collections.defaultdict(lambda:[0,0])
    for (split,lang),v in groups.items():
        if lang!="bho": continue
        for m,t,_ in v: c[(split,m[key])][0]+=(t=="bho"); c[(split,m[key])][1]+=1
    print(key,{k:f"{a}/{b}" for k,(a,b) in sorted(c.items(),key=str)})
w=[tk[0][1] for (s,l),v in groups.items() if l=="bho" for m,t,tk in v if t!="bho"]
if w: print("bho wrong: mean top1 prob %.3f, share >=0.9: %.2f"%(sum(w)/len(w),sum(x>=0.9 for x in w)/len(w)))
