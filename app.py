import os
import re
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory, abort
)
from werkzeug.security import generate_password_hash, check_password_hash

import db
from db import get_conn, MAX_MEMBERS_PER_TEAM, MAX_WRONG_ATTEMPTS, LOCKOUT_SECONDS

app = Flask(__name__)

SECRET_KEY_PATH = os.path.join(os.path.dirname(__file__), "instance", "secret_key")
os.makedirs(os.path.dirname(SECRET_KEY_PATH), exist_ok=True)
if not os.path.exists(SECRET_KEY_PATH):
    with open(SECRET_KEY_PATH, "w") as f:
        f.write(secrets.token_hex(32))
with open(SECRET_KEY_PATH) as f:
    app.secret_key = f.read().strip()

from datetime import timedelta as _timedelta

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    # Sessions persist across tabs/browser restarts until explicit logout —
    # without this, Flask's default is a non-permanent session that some
    # browsers drop on tab close, causing "random" admin/member logouts.
    PERMANENT_SESSION_LIFETIME=_timedelta(hours=12),
)


@app.before_request
def _make_session_permanent():
    # Every request refreshes the permanent flag so an active admin/member
    # session never silently expires mid-event; it only ends on /logout or
    # /admin/logout (explicit) or after 12h of total inactivity.
    session.permanent = True

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "attachments")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Canonical difficulty ordering used everywhere challenges are listed
# (participant view AND admin view), so both stay visually consistent.
DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2, "insane": 3}
DIFFICULTY_SQL_CASE = (
    "CASE difficulty "
    "WHEN 'easy' THEN 0 WHEN 'medium' THEN 1 WHEN 'hard' THEN 2 WHEN 'insane' THEN 3 ELSE 4 END"
)

CREDITS = {
    "department": "Students of CSE — Cybersecurity",
    "club": "CRYPTON Club",
    "team": [
        {"role": "Lead Challenge Developer", "name": "Bharath A"},
    ],
}


# ---------- helpers ----------

def hash_flag(flag: str) -> str:
    return hashlib.sha256(flag.strip().encode()).hexdigest()


def current_member():
    mid = session.get("member_id")
    if not mid:
        return None
    conn = get_conn()
    row = conn.execute(
        "SELECT m.*, t.name AS team_name, t.score AS team_score, t.status AS team_status "
        "FROM members m JOIN teams t ON t.id = m.team_id WHERE m.id = ?", (mid,)
    ).fetchone()
    conn.close()
    return row


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_member():
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_username"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper


def client_ip():
    fwd = request.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.remote_addr


# ---------- public / auth ----------

@app.route("/")
def index():
    return render_template("index.html", credits=CREDITS)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        team_name = request.form.get("team_name", "").strip()
        usernames = [u.strip() for u in request.form.getlist("username") if u.strip()]
        passwords = request.form.getlist("password")

        if not team_name or not (1 <= len(usernames) <= MAX_MEMBERS_PER_TEAM):
            flash(f"A team needs a name and between 1 and {MAX_MEMBERS_PER_TEAM} members.", "error")
            return redirect(url_for("register"))
        if len(usernames) != len(passwords) or any(len(p) < 6 for p in passwords):
            flash("Each member needs a username and a password of at least 6 characters.", "error")
            return redirect(url_for("register"))
        if len(set(usernames)) != len(usernames):
            flash("Member usernames must be unique within the team.", "error")
            return redirect(url_for("register"))
        if not re.match(r"^[A-Za-z0-9 _'\-]{3,40}$", team_name):
            flash("Team name must be 3-40 chars (letters, numbers, spaces, - and ' only).", "error")
            return redirect(url_for("register"))

        conn = get_conn()
        try:
            cur = conn.execute("INSERT INTO teams (name) VALUES (?)", (team_name,))
            team_id = cur.lastrowid
            for i, (u, p) in enumerate(zip(usernames, passwords)):
                conn.execute(
                    "INSERT INTO members (team_id, username, password_hash, is_captain) VALUES (?,?,?,?)",
                    (team_id, u, generate_password_hash(p), 1 if i == 0 else 0),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            flash("Team name or a username is already taken.", "error")
            return redirect(url_for("register"))
        finally:
            conn.close()

        flash("Team registered! Each member can now log in from their own machine.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", max_members=MAX_MEMBERS_PER_TEAM)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        conn = get_conn()
        member = conn.execute("SELECT * FROM members WHERE username = ?", (username,)).fetchone()
        conn.close()
        if not member or not check_password_hash(member["password_hash"], password):
            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))
        session.clear()
        session["member_id"] = member["id"]
        session.permanent = True  # stays logged in until explicit logout
        return redirect(url_for("challenges"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ---------- challenges ----------

@app.route("/challenges")
@login_required
def challenges():
    conn = get_conn()
    m = current_member()
    # Live feature flags: only is_active=1 challenges are ever returned here,
    # so an admin deactivating a challenge makes it disappear immediately —
    # no server restart, no caching, every page load re-queries the DB.
    rows = conn.execute(
        f"SELECT * FROM challenges WHERE is_active = 1 "
        f"ORDER BY {DIFFICULTY_SQL_CASE}, points"
    ).fetchall()
    solved_ids = {
        r["challenge_id"] for r in conn.execute(
            "SELECT challenge_id FROM solves WHERE team_id = ?", (m["team_id"],)
        ).fetchall()
    }
    roster = conn.execute(
        "SELECT username, is_captain FROM members WHERE team_id = ? ORDER BY is_captain DESC, username",
        (m["team_id"],)
    ).fetchall()
    conn.close()
    by_category = {}
    for r in rows:
        by_category.setdefault(r["category"], []).append(dict(r, solved=r["id"] in solved_ids))
    return render_template("challenges.html", by_category=by_category, member=m, roster=roster)


def get_lockout(conn, team_id, challenge_id):
    return conn.execute(
        "SELECT * FROM lockouts WHERE team_id=? AND challenge_id=?", (team_id, challenge_id)
    ).fetchone()


@app.route("/challenge/<slug>", methods=["GET", "POST"])
@login_required
def challenge_detail(slug):
    m = current_member()
    conn = get_conn()
    chall = conn.execute("SELECT * FROM challenges WHERE slug=? AND is_active=1", (slug,)).fetchone()
    if not chall:
        conn.close()
        abort(404)

    already_solved = conn.execute(
        "SELECT 1 FROM solves WHERE team_id=? AND challenge_id=?", (m["team_id"], chall["id"])
    ).fetchone() is not None

    lock = get_lockout(conn, m["team_id"], chall["id"])
    locked_until = None
    if lock and lock["locked_until"]:
        lu = datetime.fromisoformat(lock["locked_until"])
        if lu > datetime.utcnow():
            locked_until = lu

    if request.method == "POST" and not already_solved:
        if locked_until:
            flash("This challenge is temporarily locked for your team. Try another one meanwhile!", "error")
            return redirect(url_for("challenge_detail", slug=slug))

        submitted = request.form.get("flag", "").strip()
        correct = hash_flag(submitted) == chall["flag_hash"]

        conn.execute(
            "INSERT INTO submissions (team_id, member_id, challenge_id, submitted_flag, correct, ip_address) "
            "VALUES (?,?,?,?,?,?)",
            (m["team_id"], m["id"], chall["id"], submitted, int(correct), client_ip()),
        )

        if correct:
            conn.execute(
                "INSERT OR IGNORE INTO solves (team_id, challenge_id, member_id, points_awarded) VALUES (?,?,?,?)",
                (m["team_id"], chall["id"], m["id"], chall["points"]),
            )
            conn.execute("UPDATE teams SET score = score + ? WHERE id=?", (chall["points"], m["team_id"]))
            # clear any lockout state on success
            conn.execute("DELETE FROM lockouts WHERE team_id=? AND challenge_id=?", (m["team_id"], chall["id"]))
            conn.commit()
            conn.close()
            flash(f"Correct! +{chall['points']} points. The spirits are pleased. 🎃", "success")
            return redirect(url_for("challenges"))
        else:
            if lock:
                wrong = lock["wrong_count"] + 1
            else:
                wrong = 1
                conn.execute(
                    "INSERT INTO lockouts (team_id, challenge_id, wrong_count) VALUES (?,?,0)",
                    (m["team_id"], chall["id"]),
                )
            new_locked_until = None
            if wrong >= MAX_WRONG_ATTEMPTS:
                new_locked_until = (datetime.utcnow() + timedelta(seconds=LOCKOUT_SECONDS)).isoformat()
                wrong = 0  # reset counter once the cooldown is applied
            conn.execute(
                "UPDATE lockouts SET wrong_count=?, locked_until=? WHERE team_id=? AND challenge_id=?",
                (wrong, new_locked_until, m["team_id"], chall["id"]),
            )
            conn.commit()
            conn.close()
            if new_locked_until:
                flash("3 wrong flags — this challenge is locked for your team for 5 minutes. "
                      "Other challenges remain open, so keep hunting elsewhere! 👻", "error")
            else:
                flash("Incorrect flag. The pumpkin does not glow... yet.", "error")
            return redirect(url_for("challenge_detail", slug=slug))

    conn.close()
    return render_template(
        "challenge_detail.html", chall=chall, already_solved=already_solved,
        locked_until=locked_until.isoformat() + "Z" if locked_until else None,
    )


@app.route("/attachments/<path:filename>")
@login_required
def attachments(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)


@app.route("/scoreboard")
def scoreboard():
    conn = get_conn()
    rows = conn.execute(
        "SELECT t.name, t.score, COUNT(s.id) AS solves "
        "FROM teams t LEFT JOIN solves s ON s.team_id = t.id "
        "WHERE t.status='active' GROUP BY t.id ORDER BY t.score DESC, MAX(s.solved_at) ASC"
    ).fetchall()
    conn.close()
    return render_template("scoreboard.html", rows=rows)


@app.route("/credits")
def credits_page():
    return render_template("credits.html", credits=CREDITS)


# ---------- admin ----------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "")
        conn = get_conn()
        row = conn.execute("SELECT * FROM admins WHERE username=?", (u,)).fetchone()
        conn.close()
        if row and check_password_hash(row["password_hash"], p):
            session.clear()
            session["admin_username"] = u
            session.permanent = True  # stays logged in across tabs until explicit logout
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials.", "error")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    conn = get_conn()
    team_count = conn.execute("SELECT COUNT(*) c FROM teams").fetchone()["c"]
    solve_count = conn.execute("SELECT COUNT(*) c FROM solves").fetchone()["c"]
    active_locks = conn.execute(
        "SELECT COUNT(*) c FROM lockouts WHERE locked_until IS NOT NULL AND locked_until > ?",
        (datetime.utcnow().isoformat(),)
    ).fetchone()["c"]
    feed = conn.execute(
        "SELECT sub.submitted_at, t.name AS team, mem.username AS member, c.title, sub.correct "
        "FROM submissions sub "
        "JOIN teams t ON t.id = sub.team_id "
        "JOIN members mem ON mem.id = sub.member_id "
        "JOIN challenges c ON c.id = sub.challenge_id "
        "ORDER BY sub.submitted_at DESC LIMIT 40"
    ).fetchall()
    top = conn.execute("SELECT name, score FROM teams ORDER BY score DESC LIMIT 10").fetchall()
    conn.close()
    return render_template("admin_dashboard.html", team_count=team_count, solve_count=solve_count,
                            active_locks=active_locks, feed=feed, top=top)


@app.route("/admin/teams")
@admin_required
def admin_teams():
    conn = get_conn()
    teams = conn.execute(
        "SELECT t.*, (SELECT COUNT(*) FROM members m WHERE m.team_id=t.id) AS member_count, "
        "(SELECT COUNT(DISTINCT ip_address) FROM submissions s WHERE s.team_id=t.id) AS ip_count "
        "FROM teams t ORDER BY t.score DESC"
    ).fetchall()
    conn.close()
    return render_template("admin_teams.html", teams=teams)


@app.route("/admin/team/<int:team_id>")
@admin_required
def admin_team_detail(team_id):
    conn = get_conn()
    team = conn.execute("SELECT * FROM teams WHERE id=?", (team_id,)).fetchone()
    if not team:
        conn.close()
        abort(404)
    members = conn.execute("SELECT * FROM members WHERE team_id=?", (team_id,)).fetchall()
    subs = conn.execute(
        "SELECT sub.*, mem.username, c.title FROM submissions sub "
        "JOIN members mem ON mem.id = sub.member_id "
        "JOIN challenges c ON c.id = sub.challenge_id "
        "WHERE sub.team_id=? ORDER BY sub.submitted_at DESC", (team_id,)
    ).fetchall()
    adjustments = conn.execute("SELECT * FROM score_adjustments WHERE team_id=? ORDER BY created_at DESC", (team_id,)).fetchall()
    conn.close()
    return render_template("admin_team_detail.html", team=team, members=members, subs=subs, adjustments=adjustments)


@app.route("/admin/team/<int:team_id>/suspend", methods=["POST"])
@admin_required
def admin_suspend(team_id):
    conn = get_conn()
    conn.execute("UPDATE teams SET status='suspended' WHERE id=?", (team_id,))
    conn.execute("INSERT INTO team_status_log (team_id, admin_username, action) VALUES (?,?,'suspended')",
                 (team_id, session["admin_username"]))
    conn.commit()
    conn.close()
    flash("Team suspended.", "success")
    return redirect(url_for("admin_team_detail", team_id=team_id))


@app.route("/admin/team/<int:team_id>/reinstate", methods=["POST"])
@admin_required
def admin_reinstate(team_id):
    conn = get_conn()
    conn.execute("UPDATE teams SET status='active' WHERE id=?", (team_id,))
    conn.execute("INSERT INTO team_status_log (team_id, admin_username, action) VALUES (?,?,'reinstated')",
                 (team_id, session["admin_username"]))
    conn.commit()
    conn.close()
    flash("Team reinstated.", "success")
    return redirect(url_for("admin_team_detail", team_id=team_id))


@app.route("/admin/team/<int:team_id>/adjust", methods=["POST"])
@admin_required
def admin_adjust(team_id):
    delta = int(request.form.get("delta", 0))
    reason = request.form.get("reason", "").strip() or "No reason given"
    conn = get_conn()
    conn.execute("UPDATE teams SET score = score + ? WHERE id=?", (delta, team_id))
    conn.execute("INSERT INTO score_adjustments (team_id, admin_username, delta, reason) VALUES (?,?,?,?)",
                 (team_id, session["admin_username"], delta, reason))
    conn.commit()
    conn.close()
    flash(f"Score adjusted by {delta:+d}.", "success")
    return redirect(url_for("admin_team_detail", team_id=team_id))


@app.route("/admin/challenges")
@admin_required
def admin_challenges():
    conn = get_conn()
    rows = conn.execute(
        f"SELECT * FROM challenges ORDER BY {DIFFICULTY_SQL_CASE}, category, points"
    ).fetchall()
    conn.close()
    # Group by difficulty tier (Easy -> Medium -> Hard -> Insane) for the admin view,
    # matching the same tier ordering and color coding shown to participants.
    by_difficulty = {"easy": [], "medium": [], "hard": [], "insane": []}
    for r in rows:
        by_difficulty.setdefault(r["difficulty"], []).append(r)
    return render_template("admin_challenges.html", by_difficulty=by_difficulty)


@app.route("/admin/challenge/<int:cid>/toggle", methods=["POST"])
@admin_required
def admin_toggle_challenge(cid):
    conn = get_conn()
    row = conn.execute("SELECT is_active FROM challenges WHERE id=?", (cid,)).fetchone()
    conn.execute("UPDATE challenges SET is_active=? WHERE id=?", (0 if row["is_active"] else 1, cid))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_challenges"))


if __name__ == "__main__":
    db.init_db()
    app.run(host="0.0.0.0", port=8000, debug=False)
