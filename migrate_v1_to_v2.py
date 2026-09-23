"""
Migrates a v1 database (single login per team, password on the teams table)
into the v2 schema (up to 5 individual members per team) WITHOUT losing any
existing teams, scores, or submission history.

Strategy: for each v1 team, create the v2 team row with the same name/score,
then create one v2 member row (marked captain) reusing the team's old
password hash, so the captain can keep logging in with the same password
while up to 4 more teammates can now be added by an admin or by the team
re-registering additional members via a future /admin endpoint.

This script is idempotent: running it twice does not duplicate data.

Usage:
    python migrate_v1_to_v2.py /path/to/old_v1_toh.db
"""
import sys
import os
import sqlite3
import db as db_v2


def main():
    if len(sys.argv) != 2:
        print("Usage: python migrate_v1_to_v2.py /path/to/old_v1_toh.db")
        sys.exit(1)
    old_path = sys.argv[1]
    if not os.path.exists(old_path):
        print("Old database not found:", old_path)
        sys.exit(1)

    db_v2.init_db()  # ensure v2 schema exists
    new_conn = db_v2.get_conn()

    old_conn = sqlite3.connect(old_path)
    old_conn.row_factory = sqlite3.Row

    old_teams = old_conn.execute("SELECT * FROM teams").fetchall()
    migrated, skipped = 0, 0

    for t in old_teams:
        exists = new_conn.execute("SELECT id FROM teams WHERE name=?", (t["name"],)).fetchone()
        if exists:
            skipped += 1
            continue
        cur = new_conn.execute(
            "INSERT INTO teams (name, score, status) VALUES (?,?,?)",
            (t["name"], t["score"] if "score" in t.keys() else 0,
             t["status"] if "status" in t.keys() else "active"),
        )
        team_id = cur.lastrowid
        # Reuse old password hash for the captain login, username = old team name (sanitized)
        captain_username = t["name"].replace(" ", "_").lower() + "_captain"
        pw_hash = t["password_hash"] if "password_hash" in t.keys() else t["password"]
        new_conn.execute(
            "INSERT INTO members (team_id, username, password_hash, is_captain) VALUES (?,?,?,1)",
            (team_id, captain_username, pw_hash),
        )
        migrated += 1

    new_conn.commit()
    new_conn.close()
    old_conn.close()
    print(f"Migration complete: {migrated} teams migrated, {skipped} already present (skipped).")
    print("Captains can log in with username '<team_name>_captain' and their OLD v1 password.")
    print("Admins should add each captain's 4 teammates via the registration flow or a follow-up admin tool.")


if __name__ == "__main__":
    main()
