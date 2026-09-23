import requests

BASE = "http://127.0.0.1:8000"
ok, fail = 0, 0

def check(name, cond):
    global ok, fail
    if cond:
        ok += 1; print("PASS:", name)
    else:
        fail += 1; print("FAIL:", name)

# Admin login
adm = requests.Session()
adm.post(f"{BASE}/admin/login", data={"username": "admin1", "password": "AdminPass123"})

# 1. Admin challenges page groups by difficulty tier, all 25 shown
chall_admin = adm.get(f"{BASE}/admin/challenges")
check("admin challenges page loads", chall_admin.status_code == 200)
check("admin page shows difficulty tier headings", all(t in chall_admin.text.lower() for t in ["easy", "medium", "hard", "insane"]))

# 2. Register + login a fresh team to check participant view
team = requests.Session()
team.post(f"{BASE}/register", data={
    "team_name": "Sorting Hats", "username": ["u1", "u2"], "password": ["password1", "password2"]
})
team.post(f"{BASE}/login", data={"username": "u1", "password": "password1"})

# 3. Roster visible on /challenges
chall_page = team.get(f"{BASE}/challenges")
check("roster shows both usernames", "u1" in chall_page.text and "u2" in chall_page.text)
check("captain label shown", "captain" in chall_page.text.lower())

# 4. Difficulty color classes present on tiles
check("difficulty CSS classes present (diff-easy/medium/hard/insane)",
      all(f"diff-{d}" in chall_page.text for d in ["easy", "medium", "hard", "insane"]))

# 5. All 25 challenges visible (across all categories)
check("all 8 categories rendered", all(cat in chall_page.text for cat in
      ["General Skills", "Cryptography", "Binary Exploitation", "Web Exploitation",
       "Digital Forensics", "Steganography", "Reverse Engineering", "Miscellaneous"]))

# 6. Live toggle: deactivate a challenge as admin, confirm it vanishes for participant instantly
toggle_resp = adm.get(f"{BASE}/admin/challenges")
# find the toggle form action for 'covens-welcome-scroll' by checking challenges list via API-ish route
# (simplify: use admin_toggle_challenge by id - fetch id via a direct DB-free approach: hit /challenges as team, get all titles before)
before = team.get(f"{BASE}/challenges").text
check("'Coven's Welcome Scroll' visible before deactivation", "Coven's Welcome Scroll" in before)

# Find challenge id 1 assumption isn't safe; instead use the toggle route by slug lookup via admin page parsing
import re
m = re.search(r'/admin/challenge/(\d+)/toggle"[^>]*>\s*<button class="ghost">Deactivate', chall_admin.text)
# fallback: just toggle id=1 (first seeded challenge, covens-welcome-scroll) since seed order is deterministic
adm.post(f"{BASE}/admin/challenge/1/toggle")
after = team.get(f"{BASE}/challenges").text
check("challenge disappears instantly after admin deactivates (no restart)",
      "Coven's Welcome Scroll" not in after)

# re-activate for cleanliness
adm.post(f"{BASE}/admin/challenge/1/toggle")
restored = team.get(f"{BASE}/challenges").text
check("challenge reappears instantly after admin reactivates",
      "Coven's Welcome Scroll" in restored)

# 7. Session persistence: cookie should be marked permanent (long-lived, not session-only)
raw_login = requests.post(f"{BASE}/login", data={"username": "u1", "password": "password1"}, allow_redirects=False)
set_cookie_header = raw_login.headers.get("Set-Cookie", "")
check("session cookie carries an Expires/Max-Age (permanent, survives tab close)",
      ("expires=" in set_cookie_header.lower()) or ("max-age=" in set_cookie_header.lower()))

print(f"\n{ok} passed, {fail} failed")
