TRICK OR HACK — CTF PLATFORM v2
CRYPTON Club — CSE Cybersecurity
================================

WHAT'S NEW IN v2
-----------------
1. Teams now support up to 5 individual members, each with their own
   username/password, logging in from their own machine. All actions
   (solves, points) write to the shared team row in SQLite, so every
   teammate sees the same live score instantly on refresh — no special
   sync code needed, it's just one shared source of truth.
2. Anti-cheat: 3 wrong flags on a SPECIFIC challenge locks the team out
   of only that challenge for 5 minutes. All other challenges stay open
   the entire time, so a lockout never stalls a team's whole run.
3. Hard and Insane hints are riddles/lore, not direct instructions — run
   `python hint_linter.py` any time to check hints against the banned
   tool/technique word list before the event.
4. Full Halloween theme (flying bats, glowing pumpkin hero, tombstone
   credits) across every page via static/spooky.css.
5. A dedicated /credits page honoring the dev team.


PART A — LOCAL TEST (do this first, on your own laptop)
---------------------------------------------------------
1. Extract the project and enter the folder.
2. python3 -m venv venv && source venv/bin/activate   (Windows: venv\Scripts\activate)
3. pip install -r requirements.txt
4. python seed_challenges.py          -> loads all 25 challenges (3 fully live, 22 placeholders)
5. python hint_linter.py              -> confirms no Hard/Insane hint leaks tool names
6. python create_admin.py admin1      -> repeat for each organizer who needs monitoring access
7. python app.py                      -> serves on http://127.0.0.1:8000
8. In another terminal: python test_integration.py
   This runs 13 automated checks: 5-member registration, cross-machine
   score sync, the 3-wrong-flags lockout, concurrent access to other
   challenges during a lockout, multi-admin dashboards, etc. All should PASS.
9. Optional: run the standalone Witch's Ledger challenge separately:
   cd standalone_challenges/witchs_ledger && python app.py   (port 5000)


PART B — FILLING IN YOUR REAL CHALLENGE CONTENT
--------------------------------------------------
Open seed_challenges.py. 3 challenges are fully built and tested (Witch's
Ledger, Coven's Triple Curse, Cursed Jack-o'-Lantern). The other 22 are
placeholders with is_active=0 and flags like TOH{PLACEHOLDER_n} — replace
description/flag/hints, set is_active=1, then re-run:
    python seed_challenges.py
For Hard/Insane hints, write riddles (no tool names, no command syntax),
then run `python hint_linter.py` to confirm the wording is clean.


PART C — DEPLOYING ON YOUR COLLEGE SERVER
--------------------------------------------
Assumes a Linux server on your college LAN, reachable by the 200+
participant machines, with Python 3.10+, nginx, and sudo access.

1. On the server:
     sudo mkdir -p /opt/trickorhack
     sudo chown $USER /opt/trickorhack
     cd /opt/trickorhack
     git clone <your-repo-url> platform
     cd platform

2. Set up the environment:
     python3 -m venv venv
     source venv/bin/activate
     pip install -r requirements.txt
     python seed_challenges.py
     python create_admin.py <organizer1-username>
     python create_admin.py <organizer2-username>
     (repeat for every admin who needs monitoring access)

3. If upgrading an EXISTING v1 deployment (don't lose old teams/scores):
     cp /opt/trickorhack/platform_v1/instance/toh.db instance/toh_v1_backup.db
     python migrate_v1_to_v2.py instance/toh_v1_backup.db
   This creates each old team's captain as a v2 member (same password),
   keeps their score/history, and is safe to re-run (won't duplicate).
   The other up-to-4 teammates per team can then be registered normally.

4. Create a dedicated system user (don't run the CTF as root):
     sudo useradd -r -s /usr/sbin/nologin ctf
     sudo chown -R ctf:ctf /opt/trickorhack

5. Install the systemd services (from deploy/):
     sudo cp deploy/toh.service /etc/systemd/system/
     sudo cp deploy/witchs_ledger.service /etc/systemd/system/
     sudo systemctl daemon-reload
     sudo systemctl enable --now toh
     sudo systemctl enable --now witchs_ledger

6. Install the nginx config:
     sudo cp deploy/nginx_trickorhack.conf /etc/nginx/sites-available/trickorhack
     sudo ln -s /etc/nginx/sites-available/trickorhack /etc/nginx/sites-enabled/
     sudo nginx -t && sudo systemctl reload nginx
   Edit server_name in that file to your LAN hostname or IP first.

7. Load-test before doors open (simulate ~250 connections):
     Use a tool like `hey` or `locust` against the scoreboard and login
     endpoints. The scoreboard auto-refreshes every 15s client-side —
     that's your biggest concurrent-read load; WAL mode handles it, but
     test it anyway.


PART D — MONITORING DURING THE EVENT (2+ ADMINS)
----------------------------------------------------
Each organizer logs in independently at /admin/login with their own
account (create_admin.py). Sessions are fully independent — two admins
can be logged in and acting at the same time without conflict.

- /admin/dashboard  : team count, solve count, active-lockout count,
                       top 10 leaderboard, rolling 40-item live activity
                       feed, auto-refreshes every 10s.
- /admin/teams      : every team, member count, score, status, and a
                       distinct-IP count — 3+ distinct IPs on one team
                       flags possible account sharing to investigate.
- /admin/team/<id>  : full member list, full submission history (every
                       flag tried, right or wrong, with IP + timestamp),
                       suspend/reinstate, and manual score adjustments
                       (every adjustment is logged with which admin and
                       why, so there's an audit trail after the event).
- /admin/challenges : activate/deactivate any challenge live, e.g. to
                       pull a challenge that turns out to be broken.


PART E — PUSHING UPDATES TO GITHUB SAFELY
----------------------------------------------
Run from your project folder:
     bash deploy/sync_to_github.sh "describe your change here"

This script:
  1. Writes/refreshes .gitignore so the live database, secret key, and
     uploaded attachments are NEVER committed (only code/templates are).
  2. Shows you `git status` and asks for confirmation before committing.
  3. Commits and pushes to your current branch.
  4. Prints the exact commands to run ON THE SERVER to pull the update
     without breaking the running deployment (git pull, reinstall deps
     if requirements.txt changed, re-run migration only if upgrading
     from v1, then restart the two systemd services).

Never run `git pull` directly into a live server folder without first
backing up instance/toh.db — copy it out, pull, then restart the service.


TROUBLESHOOTING
-----------------
"Port already in use"        -> another process is bound to 8000/5000;
                                  find and stop it, or change the port
                                  in app.py / the systemd unit.
"database is locked"         -> confirm WAL mode is active (db.py sets
                                  it automatically); avoid opening the
                                  .db file directly in another program
                                  while the server is running.
Hint linter fails             -> reword the flagged hint to remove the
                                  named tool/technique; re-run the linter.
Team says "6th member" needed -> intentional. Max 5 per team is enforced
                                  server-side even if the form is edited
                                  client-side; register a second team
                                  instead.


CREDITS
---------
Department: Students of CSE — Cybersecurity, CRYPTON Club
Lead Challenge Developer: Bharath A

Happy haunting, and good luck to every team. 🎃
