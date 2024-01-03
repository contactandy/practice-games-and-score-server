"""Test score_server routines."""
from datetime import datetime, timezone

from score_server import score_server

# For checking timestamp creation in database.
DB_EVENT_MAX_TIME = 3


def datetime_fromdbutc(timestring):
    """
    Return datetime for provided time made explicitly utc. sqlite3 database
    DATETIME() function returns the UTC date and time as text in this formats:
    YYYY-MM-DD HH:MM:SS. This utility function reads this into a timezone-aware
    datetime object.
    """
    return datetime.fromisoformat(f"{timestring}+00:00")


def test_insert_token(score_db):
    """Test insert_token."""
    cursor = score_db.cursor()
    no_tokens_present = cursor.execute("SELECT * FROM tokens;").fetchall()
    assert no_tokens_present == []

    created = datetime.now(timezone.utc)
    token = "testingtesting123"
    score_server.insert_token(score_db, token)
    cursor = score_db.cursor()
    [token_entry] = cursor.execute("SELECT * FROM tokens;").fetchall()
    token_actual, created_actual = token_entry
    assert token_actual == token
    created_utc_actual = datetime.fromisoformat(f"{created_actual}+00:00")
    time_delta = created_utc_actual - created
    assert time_delta.total_seconds() < DB_EVENT_MAX_TIME
