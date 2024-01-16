import sqlite3

import pytest

import score_server

TEST_DB = "test_scores.db"


@pytest.fixture
def db():
    """
    Sample in-memory database. Disappears once the connection closes.
    """
    with sqlite3.connect(":memory:") as conn:
        score_server.init_db(conn)
        yield conn


@pytest.fixture
def db_entries():
    """Sample entries for each table in the database."""
    date = "2024-01-12 12:46:45"
    token = ("1vppX8i17HcMTkAjTColXbCxaBStyknHeKpqRI3O9hc=", date)
    button_score = ("user", "10", date)
    timing_score = ("user", "15.976295709609985", date)
    return {
        "tokens": token,
        "button": button_score,
        "timing": timing_score,
    }


@pytest.fixture
def app():
    """Sample app for flask testing."""
    yield score_server.init_app(TEST_DB)
    with sqlite3.connect(TEST_DB) as conn:
        score_server.clear_db(conn)


@pytest.fixture
def client(app):
    """Sample client for flask testing."""
    with app.test_client() as client:
        client.environ_base["HTTP_USER_AGENT"] = "basic-games"
        yield client
