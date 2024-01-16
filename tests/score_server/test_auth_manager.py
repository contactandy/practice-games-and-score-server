"""Test score_server/auth_manager routines."""

from datetime import datetime, timedelta, timezone

from score_server import auth_manager

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


def datetime_todbutc(datetime_val):
    """
    Return a string for provided time without UTC label. sqlite3 database
    DATETIME() function returns the UTC date and time as text in this formats:
    YYYY-MM-DD HH:MM:SS. This utility function converts the timezone-aware
    datetime object to such a string.
    """
    time_string, zone_info = str(datetime_val).split("+")
    return time_string


def test_insert_token(db):
    """Test insert_token."""
    cursor = db.cursor()
    no_tokens_present = cursor.execute("SELECT * FROM tokens;").fetchall()
    assert no_tokens_present == []

    created = datetime.now(timezone.utc)
    token = "testingtesting123"
    auth_manager.insert_token(db, token)
    cursor = db.cursor()
    [token_entry] = cursor.execute("SELECT * FROM tokens;").fetchall()
    token_actual, created_actual = token_entry
    assert token_actual == token
    created_utc_actual = datetime.fromisoformat(f"{created_actual}+00:00")
    time_delta = created_utc_actual - created
    assert time_delta.total_seconds() < DB_EVENT_MAX_TIME


def test_query_token(db):
    """Test query_token."""
    cursor = db.cursor()
    no_tokens_present = cursor.execute("SELECT * FROM tokens;").fetchall()
    assert no_tokens_present == []

    now = datetime.now(timezone.utc)
    created_expected = datetime_todbutc(now)
    created_unexpired = datetime_todbutc(
        now - timedelta(seconds=auth_manager.EXPIRE - 1)
    )
    created_expired = datetime_todbutc(now - timedelta(seconds=auth_manager.EXPIRE + 1))
    tokens = [
        ("querytoken", created_expected),
        ("remainingtoken", created_unexpired),
        ("expiredtoken", created_expired),
    ]
    cursor.executemany("INSERT INTO tokens VALUES (?, ?);", tokens)
    db.commit()

    token_expected, created_expected = tokens[0]
    [result] = auth_manager.query_token(db, token_expected)
    token_actual, created_actual = result
    assert token_actual == token_expected
    assert created_actual == created_expected

    [remaining] = cursor.execute("SELECT * FROM tokens;").fetchall()
    token_expected, created_expected = tokens[1]
    token_actual, created_actual = remaining
    assert token_actual == token_expected
    assert created_actual == created_expected
