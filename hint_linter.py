"""
Hint Policy Linter — run this any time after editing hints in seed_challenges.py
(or directly against the live DB) to make sure Hard/Insane hints stay abstract.

Usage:
    python hint_linter.py            # checks the live database
    python hint_linter.py --source   # checks CHALLENGES list in seed_challenges.py directly

Policy: for difficulty in {hard, insane}, a hint may NOT contain:
  - named tools/commands (gdb, ghidra, burp, nmap, sqlmap, radare2, wireshark, exiftool, binwalk, python, curl, nc...)
  - direct exploit/algorithm terms (buffer overflow, sql injection, ret2libc, format string, base64, rot13,
    xor, aes, rsa, sha256, jwt, use-after-free, race condition, ssrf, deserialization...)
  - shell/code syntax markers: backticks, "$", "sudo", "import ", "def ", flag-looking `--` flags
A hint should read like a riddle a human has to think laterally about, not a recipe.
"""
import re
import sys

BANNED_TERMS = [
    "gdb", "ghidra", "burp", "burpsuite", "nmap", "sqlmap", "radare2", "wireshark",
    "exiftool", "binwalk", "python", "curl", "netcat", " nc ", "objdump", "strace",
    "ltrace", "ida pro", "pwntools", "metasploit", "john the ripper", "hashcat",
    "buffer overflow", "sql injection", "ret2libc", "format string", "base64",
    "rot13", "vigenere", "vigenère", "xor cipher", "aes", "rsa", "sha256", "sha-256",
    "jwt", "use-after-free", "use after free", "race condition", "ssrf",
    "deserialization", "get_flag", "strings command", "unzip", "7-zip", "7zip",
]
SYNTAX_MARKERS = ["`", "$ ", "sudo ", "import ", "def ", "curl ", "wget "]


def check_hint(text, tier, label):
    if not text:
        return []
    lowered = text.lower()
    issues = []
    for term in BANNED_TERMS:
        if term in lowered:
            issues.append(f"[{tier}] {label}: contains banned direct term '{term.strip()}'")
    for marker in SYNTAX_MARKERS:
        if marker in text:
            issues.append(f"[{tier}] {label}: contains code/shell syntax marker '{marker.strip()}'")
    return issues


def lint_from_source():
    import seed_challenges
    problems = []
    for c in seed_challenges.CHALLENGES:
        if c["difficulty"] in ("hard", "insane"):
            problems += check_hint(c["hint1"], c["difficulty"], f'{c["slug"]} hint1')
            problems += check_hint(c["hint2"], c["difficulty"], f'{c["slug"]} hint2')
    return problems


def lint_from_db():
    from db import get_conn
    conn = get_conn()
    rows = conn.execute(
        "SELECT slug, difficulty, hint1, hint2 FROM challenges WHERE difficulty IN ('hard','insane')"
    ).fetchall()
    conn.close()
    problems = []
    for r in rows:
        problems += check_hint(r["hint1"], r["difficulty"], f'{r["slug"]} hint1')
        problems += check_hint(r["hint2"], r["difficulty"], f'{r["slug"]} hint2')
    return problems


if __name__ == "__main__":
    problems = lint_from_source() if "--source" in sys.argv else lint_from_db()
    if problems:
        print(f"❌ {len(problems)} hint policy violation(s) found:\n")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    else:
        print("✅ All Hard/Insane hints pass the abstraction policy (no direct tool/technique leakage).")
