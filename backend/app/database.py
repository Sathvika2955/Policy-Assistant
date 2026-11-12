"""SQLite setup. Plain SQL keeps things easy to follow."""
import sqlite3
from contextlib import closing

from app import config
from app.security import hash_password

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name     TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('admin', 'employee'))
);
CREATE TABLE IF NOT EXISTS conversations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    title      TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content         TEXT NOT NULL,
    sources         TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS leave_balances (
    user_id      INTEGER PRIMARY KEY REFERENCES users(id),
    annual_total INTEGER NOT NULL DEFAULT 24,
    annual_used  INTEGER NOT NULL DEFAULT 0,
    sick_total   INTEGER NOT NULL DEFAULT 10,
    sick_used    INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS expenses (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    description  TEXT NOT NULL,
    amount       REAL NOT NULL,
    status       TEXT NOT NULL,
    submitted_on TEXT NOT NULL
);
"""

# Demo accounts created on first run. Change these passwords before a real deployment.
# Demo expense claims for the "employee" account: (description, amount INR, status, date)
SEED_EXPENSES = [
    ("Client lunch - Hyderabad", 2400, "approved", "2026-10-02"),
    ("Flight to Bengaluru", 14500, "pending department head approval", "2026-10-20"),
    ("Hotel - 2 nights", 11000, "reimbursed", "2026-09-15"),
]

SEED_USERS = [
    ("admin", "admin123", "Admin User", "admin"),
    ("employee", "employee123", "Demo Employee", "employee"),
]


def connect() -> sqlite3.Connection:
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    """FastAPI dependency: one connection per request."""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with closing(connect()) as conn:
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            for username, password, full_name, role in SEED_USERS:
                conn.execute(
                    "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                    (username, hash_password(password), full_name, role),
                )

        # Every user gets a leave balance row (works for existing databases too)
        conn.execute(
            "INSERT INTO leave_balances (user_id) "
            "SELECT id FROM users WHERE id NOT IN (SELECT user_id FROM leave_balances)"
        )
        # Demo data for the demo employee, only the first time
        if conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0] == 0:
            demo = conn.execute("SELECT id FROM users WHERE username = 'employee'").fetchone()
            if demo:
                conn.executemany(
                    "INSERT INTO expenses (user_id, description, amount, status, submitted_on) "
                    "VALUES (?, ?, ?, ?, ?)",
                    [(demo["id"], *row) for row in SEED_EXPENSES],
                )
                conn.execute(
                    "UPDATE leave_balances SET annual_used = 9, sick_used = 2 WHERE user_id = ?",
                    (demo["id"],),
                )
        conn.commit()
