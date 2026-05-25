#!/usr/bin/env python3
"""Upgrade sync_digests.py to fetch full digest body from individual pages."""
import os

base = r"C:\elvar-agent\agora-blog"

with open(os.path.join(base, "sync_digests.py"), encoding="utf-8") as f:
    c = f.read()

# 1) Add fetch_digest_body() before def ls()
fetch_fn = """
def fetch_digest_body(url):
    \"\"\"Fetch a single digest page and extract body text.\"\"\"
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent":"AgoraBlog/1.0"})
        r.raise_for_status()
        txt = r.text
        text = re.sub(r\"<[^>]+>\", \" \", txt)
        text = re.sub(r\"\\s+\", \" \", text).strip()
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
        return \"\"
"""

insert_idx = c.find("def ls():")
c = c[:insert_idx] + fetch_fn + c[insert_idx:]

# 2) Replace fd() with body-fetching version
old_fd_start = c.find("def fd():")
old_fd_end = c.find("def gph(")

new_fd = """def fd():
    import json as j
    r=requests.get(AU,timeout=30,headers={"User-Agent":"AgoraBlog/1.0"})
    r.raise_for_status();t=r.text
    digests=[];seen=set()
    ld_match=re.search(r'<script type="application/ld\\\\+json">(.*?)</script>',t,re.DOTALL)
    if not ld_match: return digests
    try:
        ld=j.loads(ld_match.group(1))
        for item in ld.get("itemListElement",[])[:MX]:
            name=item.get("name","").strip()
            if not name or len(name)<10 or name in seen: continue
            seen.add(name)
            title=name.split("\\n")[0].strip()
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
"""

c = c[:old_fd_start] + new_fd + c[old_fd_end:]

# 3) Replace gph() with better HTML formatting
old_gph_start = c.find("def gph(")
old_gph_end = c.find("def ri(")
old_gph = c[old_gph_start:old_gph_end]

new_gph = """def gph(d):
    ti=he(d["title"]);de=he(d["body"][:150].replace("\\n"," "))
    ag=", ".join(d["agents"]) if d["agents"] else "AI agents"
    b = d["body"]
    b = re.sub(r"<[^>]+>", "", b)
    # Try to split into paragraphs by sentence or newline
    pars = [p.strip() for p in b.split(". ") if len(p.strip()) > 40]
    if not pars:
        pars = [p.strip() for p in b.split("\\n") if p.strip()]
    if not pars:
        pars = [b[:500]]
    html_pars = [f"<p>{he(p)}.</p>" for p in pars[:30]]
    b = "\\n".join(html_pars)
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
"""

c = c.replace(old_gph, new_gph)

# 4) Ensure main() calls ri(digests) not ri(nl)
old_main_call = """    existing=lpi()
    all_slugs=set(existing)
    nl=[]
    for d in digests:
        if d["slug"] not in all_slugs: all_slugs.add(d["slug"])
        desc=re.sub(r"<[^>]+>","",d["body"][:200]).replace("\\n"," ")[:150]
        nl.append({"slug":d["slug"],"title":d["title"],"desc":desc,"date":d["date"]})
    ri(nl)"""
new_main_call = """    ri(digests)"""

if old_main_call in c:
    c = c.replace(old_main_call, new_main_call)
else:
    # Try to find what's actually there
    idx = c.find("ri(nl)")
    if idx >= 0:
        print(f"Found ri(nl) at {idx}, context: {c[idx-100:idx+10]}")

# Verify
issues = []
if "def lpi():" in c:
    issues.append("lpi still present")
if "fetch_digest_body" not in c:
    issues.append("fetch_digest_body missing")
if "ri(digests)" not in c and "ri(nl)" in c:
    issues.append("ri(nl) not replaced")

if issues:
    print(f"ISSUES: {issues}")
else:
    with open(os.path.join(base, "sync_digests.py"), "w", encoding="utf-8") as f:
        f.write(c)
    print("UPGRADED OK")
    print(f"  fetch_digest_body: {'fetch_digest_body' in c}")
    print(f"  def lpi(): {'def lpi():' in c}")
    print(f"  ri(digests): {'ri(digests)' in c}")
