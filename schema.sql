-- Trick or Hack CTF Platform — Schema v2
-- Supports: multi-member teams (max 5), per-member login, per-challenge lockouts,
-- full audit trail for admin actions.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    score INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',   -- active | suspended
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Each team has 1-5 members. Each member logs in individually from their own
-- machine with their own username+password, but all actions post to the shared
-- team row above, so points/solves sync instantly across all 5 systems.
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_captain INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    difficulty TEXT NOT NULL,           -- easy | medium | hard | insane
    points INTEGER NOT NULL,
    description TEXT NOT NULL,
    flag_hash TEXT NOT NULL,            -- sha256 of the true flag; never store plaintext
    hint1 TEXT,
    hint1_cost INTEGER DEFAULT 0,
    hint2 TEXT,
    hint2_cost INTEGER DEFAULT 0,
    attachment_path TEXT,
    is_active INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS solves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    challenge_id INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    member_id INTEGER NOT NULL REFERENCES members(id),
    points_awarded INTEGER NOT NULL,
    solved_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(team_id, challenge_id)
);

-- Every submission (right or wrong) is logged, from whichever member/IP made it.
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    member_id INTEGER NOT NULL REFERENCES members(id),
    challenge_id INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    submitted_flag TEXT NOT NULL,
    correct INTEGER NOT NULL,
    ip_address TEXT,
    submitted_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Per-team, per-challenge lockout state. Lockouts are scoped to ONE challenge
-- so a team locked out of Challenge A can still work on B, C, D... concurrently.
CREATE TABLE IF NOT EXISTS lockouts (
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    challenge_id INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    wrong_count INTEGER NOT NULL DEFAULT 0,
    locked_until TEXT,                  -- NULL = not locked
    PRIMARY KEY (team_id, challenge_id)
);

CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS score_adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    admin_username TEXT NOT NULL,
    delta INTEGER NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS team_status_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    admin_username TEXT NOT NULL,
    action TEXT NOT NULL,               -- suspended | reinstated
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_submissions_team_chall ON submissions(team_id, challenge_id);
CREATE INDEX IF NOT EXISTS idx_solves_team ON solves(team_id);
CREATE INDEX IF NOT EXISTS idx_members_team ON members(team_id);
