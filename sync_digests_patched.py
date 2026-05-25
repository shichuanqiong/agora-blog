#!/usr/bin/env python3
# sync_digests.py 鈥?AgoraDigest -> GitHub Pages Blog Sync
import json,os,re,subprocess,sys,requests
from datetime import datetime,timezone
from pathlib import Path

R=Path(r"C:\elvar-agent\agora-blog")
SF=R/"digest_state.json"; PD=R/"posts"; IH=R/"index.html"
BH="/agora-blog/"; AU="https://agoradigest.com"; MX=30


def fetch_digest_body(url):
    """Fetch a single digest page and extract body text."""
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent":"AgoraBlog/1.0"})
        r.raise_for_status()
        txt = r.text
        text = re.sub(r"<[^>]+>", " ", txt)
        text = re.sub(r"\s+", " ", text).strip()
        # Find digest body
        markers = ["digest v", "high confidence", "synthesized from"]
        body_start = 0
        for m in markers:
            idx = text.lower().find(m)
            if idx >= 0:
                body_start = idx
                break
        # Cut at next major section
        end_markers = ["trust radar", "attempts", "live events"]
        body_end = body_start + 4000
        for m in end_markers:
            idx = text.lower().find(m, body_start + 100)
            if idx > body_start + 200 and idx < body_end:
                body_end = idx
                break
        return text[body_start:body_end].strip()
    except Exception as e:
        print(f"    FETCH ERROR {url}: {e}")
        return ""
def ls():
    if SF.exists():
        try: return json.loads(SF.read_text(encoding="utf-8"))
        except: pass
    return {"synced":[],"last":None}
def ss(s): SF.write_text(json.dumps(s,indent=2),encoding="utf-8")
def sl(t):
    s=t.lower().strip();s=re.sub(r"[^a-z0-9]+","-",s);return s.strip("-")[:80]
def he(t):
    return t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")
def g(*a):
    return subprocess.run(["git"]+list(a),capture_output=True,text=True,cwd=R)

def fd(bid,synced):
 r=requests.get(AU,timeout=30,headers={"User-Agent":"AgoraBlog/1.0"});r.raise_for_status()
 m=re.search(r'<script type="application/ld\+json">(.*?)</script>',r.text,re.DOTALL)
 if not m:return[]
 ld=json.loads(m.group(1));items=ld.get("itemListElement",[])[:30];result=[]
 for item in items:
  url=item.get("url","");name=item.get("name","").strip()
  if not url or not name or "/q/" not in url:continue
  qid=url.split("/q/")[1].split("/")[0].split("?")[0]
  if qid in synced:continue;td=name.split(chr(10))[0].strip()
  print(f"  Fetching: {td[:60]}...")
  dj_url=f"{AU}/_next/data/{bid}/q/{qid}.json"
  dr=requests.get(dj_url,timeout=30,headers={"User-Agent":"AgoraBlog/1.0"})
  if dr.status_code!=200:print(f"    SKIP ({dr.status_code})");continue
  dj=dr.json();init=dj.get("pageProps",{}).get("ssrInitialData",{})
  dig=init.get("digest",{});q=init.get("question",{})
  att=init.get("attempts",[]);aset=init.get("answerset",{});bi=init.get("bias",{})
  title=q.get("title",td)
  rendered=rp(title,dig.get("verdict",""),dig.get("confidence",""),
   dig.get("confidence_reason",""),dig.get("key_steps",[]),dig.get("conflicts",[]),
   dig.get("evidence_gaps",[]),dig.get("best_use_case",""),dig.get("canonical_solution",""),
   dig.get("digest_state","draft"),dig.get("version",1),q.get("tags",[]),att,bi,
   aset.get("stability",{}),qid)
  slug=sl(title);path=PD/f"{slug}.html"
  if path.exists():print(f"    EXISTS {slug}");synced.add(qid);continue
  path.write_text(rendered,encoding="utf-8");synced.add(qid)
  print(f"    OK {slug} ({len(rendered)} chars)")
  result.append({"slug":slug,"title":title,"qid":qid,"confidence":dig.get("confidence",""),
   "date":datetime.now(timezone.utc).strftime("%Y-%m-%d")})
 return result
def main():
    state=ls()
    synced=set(state["synced"])
    print(f"Already synced: {len(synced)}")
    digests=fd()
    print(f"Fetched {len(digests)} total")
    new_d=[d for d in digests if d["id"] not in synced]
    print(f"New: {len(new_d)}")
    if new_d:
        for d in new_d:
            path=PD/f"{d['slug']}.html"
            if path.exists(): print(f"  EXISTS {d['slug']}");continue
            html=gph(d)
            path.write_text(html,encoding="utf-8")
            synced.add(d["id"])
            print(f"  WROTE {path.name}")
        state["synced"]=list(synced)
        state["last"]=datetime.now(timezone.utc).isoformat()
        ss(state)
    else: print("Nothing new.")
    ri(digests)
    print("Git pull, commit, push...")
    g("pull","--rebase","origin","main")
    r1=g("add","-A");print(r1.stdout+r1.stderr[:200])
    r2=g("commit","-m",f"Auto-sync: {len(new_d)} new [{datetime.now().strftime('%Y-%m-%d %H:%M')}]")
    print(r2.stdout+r2.stderr[:200])
    if r2.returncode==0:
        r3=g("push","origin","main")
        print(r3.stdout+r3.stderr);print("PUSHED")
    else: print("Nothing to commit")
    print("DONE")

if __name__=="__main__": main()
