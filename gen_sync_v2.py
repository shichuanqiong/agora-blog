#!/usr/bin/env python3
"""Generate the new sync_digests.py with disk-scanning ri().
Solves the escaping hell by writing the file byte by byte."""

import os

base = r"C:\elvar-agent\agora-blog"

with open(os.path.join(base, "sync_digests.py"), encoding="utf-8") as f:
    content = f.read()

lpi_idx = content.find("def lpi():")
main_idx = content.find("def main():")

head = content[:lpi_idx]
tail = content[main_idx:]

# Fix main(): replace the old nl-building + ri(nl) with just ri(digests)
old_main_section = '''    existing=lpi()
    all_slugs=set(existing)
    nl=[]
    for d in digests:
        if d["slug"] not in all_slugs: all_slugs.add(d["slug"])
        desc=re.sub(r"<[^>]+>","",d["body"][:200]).replace("\\n"," ")[:150]
        nl.append({"slug":d["slug"],"title":d["title"],"desc":desc,"date":d["date"]})
    ri(nl)'''
new_main_section = '''    ri(digests)'''

# Fix tail
if old_main_section in tail:
    tail = tail.replace(old_main_section, new_main_section)
else:
    print("WARNING: old main section not found in tail")

# New ri() function as raw lines
ri_lines = []
ri_lines.append("def ri(pl):")
ri_lines.append('    """Rebuild index.html from ALL html files in posts/. not just JSON-LD data."""')
ri_lines.append("    all_posts = []")
ri_lines.append("    used_slugs = set()")
ri_lines.append('    digest_by_slug = {d["slug"]: d for d in pl}')
ri_lines.append('    html_files = sorted(PD.glob("*.html"), reverse=True)')
ri_lines.append('    html_files = [f for f in html_files if f.name != "index.html"]')
ri_lines.append("    for f in html_files:")
ri_lines.append("        slug = f.stem")
ri_lines.append("        if slug in used_slugs: continue")
ri_lines.append("        used_slugs.add(slug)")
ri_lines.append("        if slug in digest_by_slug:")
ri_lines.append("            d = digest_by_slug[slug]")
ri_lines.append('            desc = re.sub(r"<[^>]+>", "", d["body"][:200]).replace("\\n", " ")[:150]')
ri_lines.append('            all_posts.append({"slug": slug, "title": d["title"], "desc": desc, "date": d["date"]})')
ri_lines.append("        else:")
ri_lines.append('            txt = f.read_text(encoding="utf-8")')
ri_lines.append('            tm = re.search(r"<h1[^>]*>(.*?)</h1>", txt, re.DOTALL)')
ri_lines.append('            title = tm.group(1).strip() if tm else slug.replace("-", " ").title()')
ri_lines.append("            dm = re.search(r'<meta name=\"description\" content=\"([^\"]*)\"', txt)")
ri_lines.append("            desc = dm.group(1)[:150] if dm else title[:150]")
ri_lines.append('            dam = re.search(r"<time[^>]*>(.*?)</time>", txt)')
ri_lines.append('            date = dam.group(1).strip() if dam else "2026-05-25"')
ri_lines.append('            all_posts.append({"slug": slug, "title": title, "desc": desc, "date": date})')
ri_lines.append("    items=[]")
ri_lines.append("    for p in all_posts:")
ri_lines.append('        t = p["title"].replace("\\\\", "\\\\\\\\").replace(chr(34), chr(92) + chr(34))')
ri_lines.append('        d = p["desc"].replace("\\\\", "\\\\\\\\").replace(chr(34), chr(92) + chr(34))')
ri_lines.append("        items.append('      {slug:\\\"' + p['slug'] + '\\\",title:\\\"' + t + '\\\",desc:\\\"' + d + '\\\",date:\\\"' + p['date'] + '\\\"}')")
ri_lines.append('    its = "[\\n" + ",\\n".join(items) + "\\n    ]"')
ri_lines.append('    html = IH.read_text(encoding="utf-8")')
ri_lines.append('    html = re.sub(r"const posts = \\[.*?\\];", "const posts = " + its + ";", html, flags=re.DOTALL)')
ri_lines.append('    IH.write_text(html, encoding="utf-8")')
ri_lines.append('    print(f"  index.html updated: {len(all_posts)} posts")')
ri_lines.append("")

new_content = head + "\n".join(ri_lines) + "\n" + tail

# Verify
assert "def lpi()" not in new_content, "lpi still present"
assert "all_posts" in new_content, "all_posts missing"
assert "ri(digests)" in new_content, "ri(digests) missing"

with open(os.path.join(base, "sync_digests.py"), "w", encoding="utf-8") as f:
    f.write(new_content)

print("WRITTEN OK")
print("all_posts in file:", "all_posts" in new_content)
print("def lpi():", "def lpi():" in new_content)
