#!/usr/bin/env python3
"""Rebuild index.html with ALL posts from posts/ directory."""
import re
from pathlib import Path

ROOT = Path(r"C:\elvar-agent\agora-blog")
POSTS_DIR = ROOT / "posts"
INDEX = ROOT / "index.html"

html_files = sorted(POSTS_DIR.glob("*.html"), reverse=True)

# Read existing index for reference (keeping header/footer)
idx = INDEX.read_text(encoding="utf-8")

# Find the posts array boundaries
start = idx.find("const posts = [")
end = idx.find("];", start)
if start < 0 or end < 0:
    print("ERROR: cannot find posts array in index.html")
    exit(1)

entries = []
for f in html_files:
    stem = f.stem
    if not stem:
        continue
    content = f.read_text(encoding="utf-8", errors="ignore")[:500]
    
    # Title from <title> tag
    tm = re.search(r"<title>(.*?)</title>", content)
    if tm:
        title = tm.group(1).replace(" | AgoraDigest", "").strip()
        title = title.replace("\\", "\\\\").replace('"', '\\"')
    else:
        title = stem.replace("-", " ").title()
    
    # Description from <meta> tag
    dm = re.search(r'<meta name="description"[^>]*content="([^"]*)"', content)
    if dm:
        desc = dm.group(1).replace("\\", "\\\\").replace('"', '\\"')
    else:
        desc = title[:120]
    
    # Date from existing index
    escaped_slug = re.escape(stem)
    em = re.search(r'slug:\s*"' + escaped_slug + r'"[^}]+date:\s*"([^"]+)"', idx)
    date = em.group(1) if em else "2026-05-25"
    
    entries.append('      {slug:"%s",title:"%s",desc:"%s",date:"%s"}' % (stem, title, desc, date))

entries_str = "[\n" + ",\n".join(entries) + "\n    ]"
new_posts_block = "const posts = " + entries_str + ";"

new_idx = idx[:start] + new_posts_block + idx[end+2:]
INDEX.write_text(new_idx, encoding="utf-8")

slugs_in_new = re.findall(r'slug:\s*"([^"]+)"', new_idx)
print(f"DONE: {len(slugs_in_new)} posts in index")
