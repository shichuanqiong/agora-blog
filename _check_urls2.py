import requests, re

url = "https://agoradigest.com/q/0d08bc16-df3a-43f1-8d42-9d2c4004d75a"
r = requests.get(url, timeout=30, headers={'User-Agent':'AgoraBlog/1.0'})
print(f"Status: {r.status_code}")
print(f"Content length: {len(r.text)}")

# Check for digest body markers
text = re.sub(r'<[^>]+>', ' ', r.text)
text = re.sub(r'\s+', ' ', text).strip()
for m in ['digest v', 'high confidence', 'synthesized from', 'digest']:
    idx = text.lower().find(m)
    if idx >= 0:
        print(f"Found '{m}' at offset {idx}: ...{text[max(0,idx-20):idx+60]}...")
        
# Also check /q/{uuid}/v/1
url2 = url + "/v/1"
r2 = requests.get(url2, timeout=30, headers={'User-Agent':'AgoraBlog/1.0'})
print(f"\n/v/1 status: {r2.status_code}")
text2 = re.sub(r'<[^>]+>', ' ', r2.text)
text2 = re.sub(r'\s+', ' ', text2).strip()
for m in ['digest v', 'high confidence', 'synthesized from', 'digest']:
    idx = text2.lower().find(m)
    if idx >= 0:
        print(f"Found '{m}' at offset {idx}: ...{text2[max(0,idx-20):idx+60]}...")

# Check if the old /d/{slug} route still works - grab from current code's approach
print(f"\n---\nFirst 300 chars (question page):")
print(text[:300])
