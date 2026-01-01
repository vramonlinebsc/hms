import sqlite3
import os
from flask import g

# Single authoritative database path
DB_PATH = os.path.join(os.path.dirname(__file__), "hms.db")


def get_db():
    """
    Get a SQLite connection for the current request context.
    One connection per request.
    """
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exception=None):
    """
    Close the SQLite connection at the end of the request/app context.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    """
    Register DB teardown with Flask app.
    Must be called once during app creation.
    """
    app.teardown_appcontext(close_db)
