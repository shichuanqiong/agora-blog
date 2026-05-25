#!/usr/bin/env python3
"""Generate the new sync_digests.py with disk-scanning ri()."""

import re

old = '''def lpi():
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
    print(f"  index.html updated: {len(pl)} posts")'''

new = '''def ri(pl):
    """Rebuild index.html from ALL html files in posts/, not just JSON-LD data."""
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
            desc = re.sub(r"<[^>]+>", "", d["body"][:200]).replace("\\n", " ")[:150]
            all_posts.append({"slug": slug, "title": d["title"], "desc": desc, "date": d["date"]})
        else:
            c = f.read_text(encoding="utf-8")
            tm = re.search(r"<h1[^>]*>(.*?)</h1>", c, re.DOTALL)
            title = tm.group(1).strip() if tm else slug.replace("-", " ").title()
            dm = re.search(r'<meta name="description" content="([^"]*)"', c)
            desc = dm.group(1)[:150] if dm else title[:150]
            dam = re.search(r"<time[^>]*>(.*?)</time>", c)
            date = dam.group(1).strip() if dam else "2026-05-25"
            all_posts.append({"slug": slug, "title": title, "desc": desc, "date": date})
    items=[]
    for p in all_posts:
        t=p["title"].replace("\\","\\\\").replace('"','\\"')
        d=p["desc"].replace("\\","\\\\").replace('"','\\"')
        items.append(f'      {{slug:"{p["slug"]}",title:"{t}",desc:"{d}",date:"{p["date"]}"}}')
    its="[\n"+",\n".join(items)+"\n    ]"
    html=IH.read_text(encoding="utf-8")
    html=re.sub(r"const posts = \[.*?\];",f"const posts = {its};",html,flags=re.DOTALL)
    IH.write_text(html,encoding="utf-8")
    print(f"  index.html updated: {len(all_posts)} posts")'''

old_main = '''    existing=lpi()
    all_slugs=set(existing)
    nl=[]
    for d in digests:
        if d["slug"] not in all_slugs: all_slugs.add(d["slug"])
        desc=re.sub(r"<[^>]+>","",d["body"][:200]).replace("\\n"," ")[:150]
        nl.append({"slug":d["slug"],"title":d["title"],"desc":desc,"date":d["date"]})
    ri(nl)'''

new_main = '''    ri(digests)'''

with open("sync_digests.py", encoding="utf-8") as f:
    content = f.read()

if old in content:
    content = content.replace(old, new)
    print("Replaced ri()")
else:
    print("WARNING: old ri() block not found")
    # Debug: print what's actually between lpi and main
    m = re.search(r"def lpi\(\):(.*?)def main\(\):", content, re.DOTALL)
    if m:
        print(repr(m.group(1)[:600]))

if old_main in content:
    content = content.replace(old_main, new_main)
    print("Replaced main() section")
else:
    print("WARNING: old main block not found")

with open("sync_digests.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Written.")
