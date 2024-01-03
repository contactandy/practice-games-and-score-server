import sqlite3

import pytest

from score_server import score_server


@pytest.fixture
def score_db():
    with sqlite3.connect(":memory:") as conn:
        score_server.init_db(conn)
        yield conn
