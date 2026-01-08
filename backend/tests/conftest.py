import os
import tempfile
import pytest

from backend.app import create_app
from backend.init_db import init_db


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    os.environ["HMS_DB_PATH"] = db_path

    # IMPORTANT: init DB BEFORE app creation
    init_db()

    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client

    os.close(db_fd)
    os.unlink(db_path)

