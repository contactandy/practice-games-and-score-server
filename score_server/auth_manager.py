"""Module for handling authentication."""
import hashlib
import logging
import secrets
import sqlite3

HASH_SECRET = hashlib.sha256(b"LEARNING PURPOSES ONLY").digest()

EXPIRE = 10  # seconds


def insert_token(conn, token):
    """Insert a token into the token table with an associated timestamp of now"""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tokens (token, created) VALUES (?, CURRENT_TIMESTAMP);", (token,)
    )


def init_auth(database):
    """
    Creates a paired server challenge and expected client response. The
    expected client response is stored in the token database and the server
    challenge is returned.
    """
    sc = secrets.base64.b64encode(secrets.token_bytes(32))
    cr = secrets.base64.b64encode(hashlib.sha256(sc + HASH_SECRET).digest())
    with sqlite3.connect(database) as conn:
        insert_token(conn, cr.decode())
    logging.debug(f"(sc, cr) = {(sc, cr)}")
    return sc.decode()


def query_token(conn, token):
    """
    Remove expired tokens, check for and return given token, and remove from
    database if found.
    """
    cursor = conn.cursor()
    # at query time, remove expired tokens
    cursor.execute(
        "DELETE FROM tokens "
        "WHERE "
        "CAST(strftime('%s', CURRENT_TIMESTAMP) as integer) "
        "- CAST(strftime('%s', created) as integer) > ?;",
        (EXPIRE,),
    )
    results = cursor.execute(
        "SELECT * FROM tokens WHERE token = ?;", (token,)
    ).fetchall()
    # tokens will be single use
    cursor.execute("DELETE FROM tokens WHERE token = ?;", (token,))
    return results


def check_basic_digest(nonce, actual_digest):
    """
    Check simplified basic digest authentication: actual_digest should be the
    sha256 hash of the nonce concatenated with the shared secret.
    """
    nonce = secrets.base64.b64decode(nonce)
    actual_digest = secrets.base64.b64decode(actual_digest)
    expected_digest = hashlib.sha256(nonce + HASH_SECRET).digest()
    return expected_digest == actual_digest


def check_single_use_challenge_response(database, cr):
    """
    Check if client has previously authenticated with single use challenge
    response method and obtained a token that is still current.
    """
    with sqlite3.connect(database) as scores:
        authed = query_token(scores, cr)
    return authed


def check_auth(database, request):
    """Returns the games for which the request is authorized to submit scores."""
    authed = []
    cr = request.cookies.get("_CR")
    nonce = request.cookies.get("NONCE")
    digest = request.cookies.get("DIGEST")
    if cr:
        if check_single_use_challenge_response(database, cr):
            authed.append("BUTTON")
    if nonce and digest:
        if check_basic_digest(nonce, digest):
            authed.append("TIMING")
    return authed
