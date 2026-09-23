import requests

BASE = "http://127.0.0.1:8000"
ok = 0
fail = 0

def check(name, cond):
    global ok, fail
    if cond:
        ok += 1
        print("PASS:", name)
    else:
        fail += 1
        print("FAIL:", name)

# 1. Register a 5-member team
s = requests.Session()
data = {
    "team_name": "The Headless Hackers",
    "username": ["cap1", "mem2", "mem3", "mem4", "mem5"],
    "password": ["password1", "password2", "password3", "password4", "password5"],
}
r = s.post(f"{BASE}/register", data=data, allow_redirects=True)
check("register 5-member team succeeds", r.status_code == 200 and "log in" in r.text.lower())

# 2. Try registering a 6th member -> should fail server-side even if client bypassed
data6 = dict(data)
data6["team_name"] = "Six Pack"
data6["username"] = ["a", "b", "c", "d", "e", "f"]
data6["password"] = ["password1"] * 6
r6 = requests.post(f"{BASE}/register", data=data6)
check("6-member team rejected", "between 1 and 5" in r6.text)

# 3. Member 1 logs in on "machine A"
sessA = requests.Session()
r = sessA.post(f"{BASE}/login", data={"username": "cap1", "password": "password1"})
check("member1 login", "Challenges" in r.text or r.status_code == 200)

# 4. Member 2 logs in independently on "machine B"
sessB = requests.Session()
r = sessB.post(f"{BASE}/login", data={"username": "mem2", "password": "password2"})
check("member2 independent login", r.status_code == 200)

# 5. Member A solves the easy web challenge
r = sessA.post(f"{BASE}/challenge/witchs-ledger", data={"flag": "TOH{c00k13s_l13_3v3ry_h4ll0w_3v3}"})
r2 = sessA.get(f"{BASE}/challenges")
check("member A solve reflected for A", "80 pts" in r2.text or "solved" in r2.text.lower())

# 6. Member B (different machine, same team) sees the score update instantly (DB-backed, no special sync needed)
r3 = sessB.get(f"{BASE}/challenges")
check("member B sees team's shared score instantly", "80" in r3.text)

# 7. Lockout: member B submits 3 wrong flags on crypto challenge
for i in range(3):
    r = sessB.post(f"{BASE}/challenge/covens-triple-curse", data={"flag": f"wrong{i}"})
locked_page = sessB.get(f"{BASE}/challenge/covens-triple-curse")
check("locked after 3 wrong attempts", "locked" in locked_page.text.lower())

# 8. During lockout, team can still work another challenge concurrently
other = sessA.get(f"{BASE}/challenge/cursed-jackolantern")
check("other challenge still accessible during lockout", other.status_code == 200)

# 9. Scoreboard shows the team
sb = requests.get(f"{BASE}/scoreboard")
check("scoreboard shows team", "Headless Hackers" in sb.text)

# 10. Credits page present
cr = requests.get(f"{BASE}/credits")
check("credits page has all 4 names", all(n in cr.text for n in
      ["Bharath A", "Chethan Kumar CS", "Vijay Kumar S", "Chinmayi B"]))

# 11. Multi-admin: two independent admin sessions
admA = requests.Session()
admA.post(f"{BASE}/admin/login", data={"username": "admin1", "password": "AdminPass123"})
admB = requests.Session()
admB.post(f"{BASE}/admin/login", data={"username": "admin2", "password": "AdminPass456"})
dashA = admA.get(f"{BASE}/admin/dashboard")
dashB = admB.get(f"{BASE}/admin/dashboard")
check("admin1 dashboard loads", "Admin Dashboard" in dashA.text)
check("admin2 dashboard loads independently", "Admin Dashboard" in dashB.text)

# 12. Admin sees team detail with member list + IP tracking
teams_page = admA.get(f"{BASE}/admin/teams")
check("admin teams list shows team", "Headless Hackers" in teams_page.text)

print(f"\n{ok} passed, {fail} failed")
