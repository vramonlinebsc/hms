import sqlite3
from flask import g

DB_PATH = "hms.db"

def get_db():
    if "db" not in g:
        conn = sqlite3.connect(
            DB_PATH,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row

        # --- HARDENING PRAGMAS ---
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA temp_store=MEMORY;")

        g.db = conn

    return g.db

def init_app(app):
    # DB is initialized lazily via get_db()
    # This hook exists only to satisfy app wiring
    pass

