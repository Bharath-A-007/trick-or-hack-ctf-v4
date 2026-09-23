"""
init_db.py — production database initialization entrypoint.
Creates the schema (if not present) and seeds all 25 challenges, fully active.

Usage:
    python init_db.py
"""
import db
import seed_challenges

if __name__ == "__main__":
    db.init_db()
    seed_challenges.main()
