#!/usr/bin/env python3
"""Minimal patch: replace fd+gph with SSR API in old sync_digests.py"""
import sys;sys.stdout.reconfigure(encoding='utf-8')
old=open('sync_digests_old.py','r',encoding='utf-8').read()
lines=old.split('\n')
# Replace lines 52-147 with new fd+rp+ri
# New fd = use SSR API
new_middle=[
"def fd(bid,synced):",
' r=requests.get(AU,timeout=30,headers={"User-Agent":"AgoraBlog/1.0"});r.raise_for_status()',
' m=re.search(r\'<script type="application/ld\\+json">(.*?)</script>\',r.text,re.DOTALL)',
' if not m:return[]',
' ld=json.loads(m.group(1));items=ld.get("itemListElement",[])[:30];result=[]',
' for item in items:',
'  url=item.get("url","");name=item.get("name","").strip()',
'  if not url or not name or "/q/" not in url:continue',
'  qid=url.split("/q/")[1].split("/")[0].split("?")[0]',
'  if qid in synced:continue;td=name.split(chr(10))[0].strip()',
'  print(f"  Fetching: {td[:60]}...")',
'  dj_url=f"{AU}/_next/data/{bid}/q/{qid}.json"',
'  dr=requests.get(dj_url,timeout=30,headers={"User-Agent":"AgoraBlog/1.0"})',
'  if dr.status_code!=200:print(f"    SKIP ({dr.status_code})");continue',
'  dj=dr.json();init=dj.get("pageProps",{}).get("ssrInitialData",{})',
'  dig=init.get("digest",{});q=init.get("question",{})',
'  att=init.get("attempts",[]);aset=init.get("answerset",{});bi=init.get("bias",{})',
'  title=q.get("title",td)',
'  rendered=rp(title,dig.get("verdict",""),dig.get("confidence",""),',
'   dig.get("confidence_reason",""),dig.get("key_steps",[]),dig.get("conflicts",[]),',
'   dig.get("evidence_gaps",[]),dig.get("best_use_case",""),dig.get("canonical_solution",""),',
'   dig.get("digest_state","draft"),dig.get("version",1),q.get("tags",[]),att,bi,',
'   aset.get("stability",{}),qid)',
'  slug=sl(title);path=PD/f"{slug}.html"',
'  if path.exists():print(f"    EXISTS {slug}");synced.add(qid);continue',
'  path.write_text(rendered,encoding="utf-8");synced.add(qid)',
'  print(f"    OK {slug} ({len(rendered)} chars)")',
'  result.append({"slug":slug,"title":title,"qid":qid,"confidence":dig.get("confidence",""),',
'   "date":datetime.now(timezone.utc).strftime("%Y-%m-%d")})',
' return result',
]
lines[52:148]=new_middle
result='\n'.join(lines)
with open('sync_digests_patched.py','w',encoding='utf-8') as f:f.write(result)
print(f"Patched: {len(result)} chars, {result.count(chr(10))} lines")
print("Has rp:", "def rp(" in result)
