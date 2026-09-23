import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "instance", "toh.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

MAX_MEMBERS_PER_TEAM = 5
MAX_WRONG_ATTEMPTS = 3
LOCKOUT_SECONDS = 5 * 60  # 5 minutes


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    # WAL mode: readers don't block writers, critical for 200+ concurrent users
    # hitting SQLite from many gunicorn workers at once.
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db():
    conn = get_conn()
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized at", DB_PATH)
