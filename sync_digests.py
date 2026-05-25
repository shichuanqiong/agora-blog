#!/usr/bin/env python3
# sync_digests.py — AgoraDigest -> GitHub Pages Blog Sync
import json,os,re,subprocess,sys,requests
from datetime import datetime,timezone
from pathlib import Path

R=Path(r"C:\elvar-agent\agora-blog")
SF=R/"digest_state.json"; PD=R/"posts"; IH=R/"index.html"
BH="/agora-blog/"; AU="https://agoradigest.com"; MX=30

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

def fd():
    import json as j
    r=requests.get(AU,timeout=30,headers={"User-Agent":"AgoraBlog/1.0"})
    r.raise_for_status();t=r.text
    digests=[];seen=set()
    ld_match=re.search(r'<script type="application/ld\+json">(.*?)</script>',t,re.DOTALL)
    if not ld_match: return digests
    try:
        ld=j.loads(ld_match.group(1))
        for item in ld.get("itemListElement",[])[:MX]:
            name=item.get("name","").strip()
            if not name or len(name)<10 or name in seen: continue
            seen.add(name)
            title=name.split("\n")[0].strip()
            digests.append({
                "id":item.get("url","").split("/")[-1][:12],
                "title":title,"slug":sl(title),"vertical":"engineering",
                "body":name[:2000],"agents":["atlas","rhea","kairos"],
                "date":datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "url":item.get("url","")
            })
            print(f"  OK {title[:60]}")
    except Exception as e: print(f"JSON-LD error: {e}")
    return digests

def gph(d):
    ti=he(d["title"]);de=he(d["body"][:150].replace("\n"," "))
    ag=", ".join(d["agents"]) if d["agents"] else "AI agents"
    b=re.sub(r"<[^>]+>","",d["body"])
    pars=[f"<p>{p.strip()}</p>" for p in b.split("\n") if p.strip()]
    b="\n".join(pars) if pars else f"<p>{b}</p>"
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{ti} | AgoraDigest</title><meta name="description" content="{de[:200]}">
<script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-white text-gray-900 font-sans">
<header class="border-b border-gray-200"><div class="max-w-3xl mx-auto px-6 py-6 flex items-center justify-between">
<a href="{BH}" class="text-xl font-bold">AgoraDigest Blog</a>
<nav class="space-x-6 text-sm text-gray-600"><a href="{BH}" class="hover:text-gray-900">Home</a>
<a href="https://agoradigest.com" class="hover:text-gray-900">Try AgoraDigest -{'>'}</a></nav></div></header>
<main class="max-w-3xl mx-auto px-6 py-12"><article>
<time class="text-sm text-gray-500">{d["date"]}</time>
<h1 class="text-4xl font-bold mt-2 mb-6">{ti}</h1>
{b}
<p class="mt-8 text-sm text-gray-500">Digest by {ag} . <a href="{d["url"]}" class="text-blue-600 hover:underline">View original -{'>'}</a></p>
</article></main>
<footer class="border-t border-gray-200 mt-12"><div class="max-w-3xl mx-auto px-6 py-8 text-sm text-gray-500 text-center">
<p>AgoraDigest Blog - Powered by multi-agent debate.</p></div></footer>
</body></html>'''

def lpi():
    if not IH.exists(): return []
    html=IH.read_text(encoding="utf-8")
    m=re.search(r"const posts = \[(.*?)\];",html,re.DOTALL)
    if not m: return []
    slugs=re.findall(r'slug:\s*"([^"]+)"',m.group(1))
    return slugs

def ri(pl):
    items=[]
    for p in pl:
        t=p["title"].replace("\\","\\\\").replace('"','\\"')
        d=p["desc"].replace("\\","\\\\").replace('"','\\"')
        items.append(f'      {{slug:"{p["slug"]}",title:"{t}",desc:"{d}",date:"{p["date"]}"}}')
    its="[\n"+",\n".join(items)+"\n    ]"
    html=IH.read_text(encoding="utf-8")
    html=re.sub(r"const posts = \[.*?\];",f"const posts = {its};",html,flags=re.DOTALL)
    IH.write_text(html,encoding="utf-8")
    print(f"  index.html updated: {len(pl)} posts")

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
    existing=lpi()
    all_slugs=set(existing)
    nl=[]
    for d in digests:
        if d["slug"] not in all_slugs: all_slugs.add(d["slug"])
        desc=re.sub(r"<[^>]+>","",d["body"][:200]).replace("\n"," ")[:150]
        nl.append({"slug":d["slug"],"title":d["title"],"desc":desc,"date":d["date"]})
    ri(nl)
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
