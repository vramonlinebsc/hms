import sqlite3
import os
from flask import g

def get_db_path():
    return os.getenv("HMS_DB_PATH", "hms.db")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(get_db_path())
        g.db.row_factory = sqlite3.Row
    return g.db

def init_app(app):
    @app.teardown_appcontext
    def close_db(exception):
        db = g.pop("db", None)
        if db is not None:
            db.close()

