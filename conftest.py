import os
import tempfile
import pytest

from backend.app import create_app
from backend.init_db import init_db


@pytest.fixture
def client():
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()

    # Point HMS to this DB
    os.environ["HMS_DB_PATH"] = db_path

    # Initialize schema AFTER env var is set
    init_db()

    # Create app + test client
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)

