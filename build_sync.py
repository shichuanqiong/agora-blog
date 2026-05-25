# Run this to build sync_digests.py from parts
import sys;sys.stdout.reconfigure(encoding='utf-8')
import os; os.chdir(r'C:\elvar-agent\agora-blog')

# Read old script (has full main())
old = open('sync_digests_old.py', 'r', encoding='utf-8').read()
lines = old.split('\n')

# Read v2 base (has new fd())
v2 = open('sync_digests_v2.py', 'r', encoding='utf-8').read()

# Find fd() in old and v2
old_fd_start = next(i for i,l in enumerate(lines) if l.strip().startswith('def fd()'))
old_main_start = next(i for i,l in enumerate(lines) if l.strip().startswith('def main()'))

# Build: prefix (helpers) + v2_fd + v2_rp + old_main
prefix = '\n'.join(lines[:old_fd_start])  # imports + helpers

# Read rp() and main() from the generate script
# For now, just copy the whole thing
result = prefix + '\n' + v2 + '\n'

# Add main() from old, but modify it to call fd() with build_id
main_code = '\n'.join(lines[old_main_start:])
# Patch main() to pass build_id
main_code = main_code.replace(
    "digests=fd()",
    "digests=fd(bid, synced)"
)
# Patch main to get build_id first
main_code = main_code.replace(
    "print(f\"Already synced: {len(synced)}\")",
    "bid=gi()\n    print(f\"Already synced: {len(synced)}\")"
)

result += '\n' + main_code

with open('sync_digests_final.py', 'w', encoding='utf-8') as f:
    f.write(result)
print(f"Built: {len(result)} chars, {result.count(chr(10))} lines")
print("Check rp() exists:", "def rp(" in result)
