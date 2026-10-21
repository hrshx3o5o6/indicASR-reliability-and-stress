import os
from huggingface_hub import snapshot_download
tok=os.environ["HF_TOKEN"]
for repo,rev,name in (("bodhan-ai/indic-transcribe-core","e083ab7dfeeddcb5c0b4a2d7df53f53e7b0f1537","core"),
                      ("bodhan-ai/indic-transcribe-flex","c0db6b2b05409fee7317f193fb207db332a0f14b","flex")):
    p=snapshot_download(repo,revision=rev,token=tok,local_dir=f"/tmp/claude-0/models/{name}",
        allow_patterns=["*.json","*.py","*.model","*.md","*.safetensors"])
    print("READY",name,p,flush=True)
