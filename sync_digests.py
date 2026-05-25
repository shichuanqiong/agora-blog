#!/usr/bin/env python3
"""sync_digests.py v2 — FULL digest via Next.js SSR API"""
import json,os,re,subprocess,sys,requests
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(r"C:\elvar-agent\agora-blog")
SF=ROOT/"digest_state.json";PD=ROOT/"posts";IH=ROOT/"index.html";BF=ROOT/".build_id"
BH="/agora-blog/";AU="https://agoradigest.com";MX=30

def h(t):
    if not t:return ""
    return t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")
def gi():
    if BF.exists():
        b=BF.read_text().strip()
        if b:return b
    r=requests.get(AU,timeout=30,headers={"User-Agent":"AgoraBlog/1.0"});r.raise_for_status()
    m=re.search(r'/_next/static/([^/]+)/_buildManifest\.js',r.text)
    if not m:raise RuntimeError("Build ID not found")
    b=m.group(1);BF.write_text(b);return b
def ls():
    if SF.exists():
        try:return json.loads(SF.read_text(encoding="utf-8"))
        except:pass
    return{"synced":[],"last":None}
def ss(s):SF.write_text(json.dumps(s,indent=2),encoding="utf-8")
def g(*a):
    return subprocess.run(["git"]+list(a),capture_output=True,text=True,cwd=ROOT)
def sl(t):
    s=t.lower().strip();s=re.sub(r"[^a-z0-9]+","-",s);return s.strip("-")[:80]
def fd(bid,synced):
    r=requests.get(AU,timeout=30,headers={"User-Agent":"AgoraBlog/1.0"});r.raise_for_status()
    m=re.search(r'<script type="application/ld\+json">(.*?)</script>',r.text,re.DOTALL)
    if not m:return[]
    ld=json.loads(m.group(1));items=ld.get("itemListElement",[])[:MX];result=[]
    for item in items:
        url=item.get("url","");name=item.get("name","").strip()
        if not url or not name or "/q/" not in url:continue
        qid=url.split("/q/")[1].split("/")[0].split("?")[0]
        if qid in synced:continue
        td=name.split("\n")[0].strip()
        print(f"  Fetching: {td[:60]}...")
        dj_url=f"{AU}/_next/data/{bid}/q/{qid}.json"
        dr=requests.get(dj_url,timeout=30,headers={"User-Agent":"AgoraBlog/1.0"})
        if dr.status_code!=200:print(f"    SKIP ({dr.status_code})");continue
        dj=dr.json();init=dj.get("pageProps",{}).get("ssrInitialData",{})
        dig=init.get("digest",{});q=init.get("question",{})
        att=init.get("attempts",[]);aset=init.get("answerset",{})
        bias=init.get("bias",{});title=q.get("title",td)
        body=q.get("body","")
        rendered=rp(title,dig.get("verdict",""),dig.get("confidence",""),
            dig.get("confidence_reason",""),dig.get("key_steps",[]),
            dig.get("conflicts",[]),dig.get("evidence_gaps",[]),
            dig.get("best_use_case",""),dig.get("canonical_solution",""),
            dig.get("digest_state","draft"),dig.get("version",1),
            q.get("tags",[]),att,bias,aset.get("stability",{}),qid)
        slug=sl(title);path=PD/f"{slug}.html"
        if path.exists():print(f"    EXISTS {slug}");synced.add(qid);continue
        path.write_text(rendered,encoding="utf-8");synced.add(qid)
        print(f"    OK {slug} ({len(rendered)} chars)")
        result.append({"slug":slug,"title":title,"qid":qid,"confidence":dig.get("confidence",""),"date":datetime.now(timezone.utc).strftime("%Y-%m-%d")})
    return result

# short rp
