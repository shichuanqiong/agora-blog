with open('sync_digests.py', 'rb') as f:
    data = f.read()

# File has: ld\\+json  (bytes: 6c 64 5c 5c 2b 6a 73 6f 6e)
# Need:     ld\+json  (bytes: 6c 64 5c 2b 6a 73 6f 6e)
old = bytes([0x6c, 0x64, 0x5c, 0x5c, 0x2b, 0x6a, 0x73, 0x6f, 0x6e])
new = bytes([0x6c, 0x64, 0x5c, 0x2b, 0x6a, 0x73, 0x6f, 0x6e])

idx = data.find(old)
print(f"Old pattern found at: {idx}")
if idx >= 0:
    data = data[:idx] + new + data[idx+len(old):]
    with open('sync_digests.py', 'wb') as f:
        f.write(data)
    print(f"Written {len(data)} bytes")
    
    # Verify
    with open('sync_digests.py', 'rb') as f:
        v = f.read()
    print(f"Old still present: {old in v}")
    print(f"New in file: {new in v}")
    
    # Check the line
    line_start = v.rfind(b'\n', 0, idx) + 1
    line_end = v.find(b'\n', idx)
    print(f"Line: {v[line_start:line_end]}")
else:
    print("Old pattern NOT found!")
    # Debug: show all nearby bytes
    app_idx = data.find(b'application')
    print(f"'application' at {app_idx}: {data[app_idx:app_idx+30].hex()}")
