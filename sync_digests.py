#!/usr/bin/env python3
# sync_digests.py — AgoraDigest -> GitHub Pages Blog Sync
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

def fd():
    import json as j
    r=requests.get(AU,timeout=30,headers={"User-Agent":"AgoraBlog/1.0"})
    r.raise_for_status();t=r.text
    digests=[];seen=set()
    ld_match=re.search(r'<script type="application/ld\\+json">(.*?)</script>',t,re.DOTALL)
    if not ld_match: return digests
    try:
        ld=j.loads(ld_match.group(1))
        for item in ld.get("itemListElement",[])[:MX]:
            name=item.get("name","").strip()
            if not name or len(name)<10 or name in seen: continue
            seen.add(name)
            title=name.split("\n")[0].strip()
            url = item.get("url","")
            digest_id = url.split("/")[-1][:12]
            print(f"  Fetching body for: {title[:50]}...")
            body = fetch_digest_body(url) if url else name[:2000]
            if not body or len(body) < 100:
                body = name[:2000]
            digests.append({
                "id":digest_id,
                "title":title,"slug":sl(title),"vertical":"engineering",
                "body":body,"agents":["atlas","rhea","kairos"],
                "date":datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "url":url
            })
            print(f"  OK {title[:60]} ({len(body)} chars)")
    except Exception as e: print(f"JSON-LD error: {e}")
    return digests
def gph(d):
    ti=he(d["title"]);de=he(d["body"][:150].replace("\n"," "))
    ag=", ".join(d["agents"]) if d["agents"] else "AI agents"
    b = d["body"]
    b = re.sub(r"<[^>]+>", "", b)
    # Try to split into paragraphs by sentence or newline
    pars = [p.strip() for p in b.split(". ") if len(p.strip()) > 40]
    if not pars:
        pars = [p.strip() for p in b.split("\n") if p.strip()]
    if not pars:
        pars = [b[:500]]
    html_pars = [f"<p>{he(p)}.</p>" for p in pars[:30]]
    b = "\n".join(html_pars)
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{ti} | AgoraDigest</title><meta name="description" content="{de[:200]}">
<script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-white text-gray-900 font-sans">
<header class="border-b border-gray-200"><div class="max-w-3xl mx-auto px-6 py-6 flex items-center justify-between">
<a href="{BH}" class="text-xl font-bold">AgoraDigest Blog</a>
<nav class="space-x-6 text-sm text-gray-600"><a href="{BH}" class="hover:text-gray-900">Home</a>
<a href="https://agoradigest.com" class="hover:text-gray-900">Try AgoraDigest →</a></nav></div></header>
<main class="max-w-3xl mx-auto px-6 py-12"><article>
<time class="text-sm text-gray-500">{d["date"]}</time>
<h1 class="text-4xl font-bold mt-2 mb-6">{ti}</h1>
{b}
<p class="mt-8 text-sm text-gray-500">Digest by {ag} · <a href="{d["url"]}" class="text-blue-600 hover:underline">View original →</a></p>
</article></main>
<footer class="border-t border-gray-200 mt-12"><div class="max-w-3xl mx-auto px-6 py-8 text-sm text-gray-500 text-center">
<p>AgoraDigest Blog — Powered by multi-agent debate.</p></div></footer>
</body></html>'''
def ri(pl):
    """Rebuild index.html from ALL html files in posts/. not just JSON-LD data."""
    all_posts = []
    used_slugs = set()
    digest_by_slug = {d["slug"]: d for d in pl}
    html_files = sorted(PD.glob("*.html"), reverse=True)
    html_files = [f for f in html_files if f.name != "index.html"]
    for f in html_files:
        slug = f.stem
        if slug in used_slugs: continue
        used_slugs.add(slug)
        if slug in digest_by_slug:
            d = digest_by_slug[slug]
            desc = re.sub(r"<[^>]+>", "", d["body"][:200]).replace("\n", " ")[:150]
            all_posts.append({"slug": slug, "title": d["title"], "desc": desc, "date": d["date"]})
        else:
            txt = f.read_text(encoding="utf-8")
            tm = re.search(r"<h1[^>]*>(.*?)</h1>", txt, re.DOTALL)
            title = tm.group(1).strip() if tm else slug.replace("-", " ").title()
            dm = re.search(r'<meta name="description" content="([^"]*)"', txt)
            desc = dm.group(1)[:150] if dm else title[:150]
            dam = re.search(r"<time[^>]*>(.*?)</time>", txt)
            date = dam.group(1).strip() if dam else "2026-05-25"
            all_posts.append({"slug": slug, "title": title, "desc": desc, "date": date})
    items=[]
    for p in all_posts:
        t = p["title"].replace("\\", "\\\\").replace(chr(34), chr(92) + chr(34))
        d = p["desc"].replace("\\", "\\\\").replace(chr(34), chr(92) + chr(34))
        items.append('      {slug:\"' + p['slug'] + '\",title:\"' + t + '\",desc:\"' + d + '\",date:\"' + p['date'] + '\"}')
    its = "[\n" + ",\n".join(items) + "\n    ]"
    html = IH.read_text(encoding="utf-8")
    html = re.sub(r"const posts = \[.*?\];", "const posts = " + its + ";", html, flags=re.DOTALL)
    IH.write_text(html, encoding="utf-8")
    print(f"  index.html updated: {len(all_posts)} posts")

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
