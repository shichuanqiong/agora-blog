import requests, json, re

r = requests.get('https://agoradigest.com', timeout=30, headers={'User-Agent':'AgoraBlog/1.0'})
ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', r.text, re.DOTALL)
data = json.loads(ld.group(1))

print("=== JSON-LD entries (first 5) ===")
for i, item in enumerate(data.get('itemListElement',[])[:5]):
    name = item.get('name','')[:60]
    url = item.get('url','')
    print(f"\n[{i}] name: {name}")
    print(f"    url:  {url}")

print("\n=== Checking permalink format ===")
# If url = /d/xxx... check if /q/xxx/v/1 also works
first_url = data['itemListElement'][0].get('url','')
print(f"First URL: {first_url}")
