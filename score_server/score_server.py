"""
Score server that includes an authentication process and a score submission
process.
"""
import argparse
import hashlib
import logging
import secrets
import sqlite3

from flask import Flask, make_response, redirect, render_template, request, url_for

app = Flask(__name__)


@app.route("/")
@app.route("/index")
def index():
    """Return main page"""
    return render_template("index.html")


def init_db(conn):
    """Create tables with the provided database connection."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT UNIQUE,
            created TIMESTAMP 
        );
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS button (
            username TEXT UNIQUE,
            score INTEGER DEFAULT 0, 
            date DATETIME
        );
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS timing ( 
            username TEXT UNIQUE, 
            score FLOAT NOT NULL, 
            date DATETIME 
        );
        """
    )
    conn.commit()


with sqlite3.connect("scores.db") as scores:
    init_db(scores)


SCORE_COMPARISONS_BY_GAME = {
    "BUTTON": {"select": max, "cast": int},
    "TIMING": {"select": min, "cast": float},
}


@app.route("/scores", methods=["GET"])
def show_scores():
    """Return page with score tables for each game"""
    game_data = dict()
    with sqlite3.connect("scores.db") as scores:
        cursor = scores.cursor()
        for game in SCORE_COMPARISONS_BY_GAME:
            cursor.execute(f"SELECT * FROM {game}")
            game_data[game] = cursor.fetchall()
            app.logger.debug(f"game `{game}` scores: {game_data[game]}")
    return render_template(
        "highscores.html", button=game_data["BUTTON"], timing=game_data["TIMING"]
    )


HASH_SECRET = hashlib.sha256(b"LEARNING PURPOSES ONLY").digest()

EXPIRE = 10  # seconds


def insert_token(conn, token):
    """Insert a token into the token table with an associated timestamp of now"""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tokens (token, created) VALUES (?, CURRENT_TIMESTAMP);", (token,)
    )


@app.route("/auth", methods=["GET"])
def do_auth():
    """
    Set up a single use challenge response token for a client to use when
    submitting a score.

    When a client visits this endpoint, a paired (sc, cr) value is created
    such that cr is the hash of sc with a secret key. Because this server is
    for exercises, the key is hardcoded into the app. The sc value is sent
    as a cookie in the response to the client. The cr value is stored in the
    tokens database for reference by the submit endpoint.
    """
    response = make_response(redirect(url_for("index")))
    good_ua = request.headers["user-agent"] == "basic-games"
    if request.method == "GET" and good_ua:
        app.logger.debug("Received request to initiate auth")
        sc = secrets.base64.b64encode(secrets.token_bytes(32))
        cr = secrets.base64.b64encode(hashlib.sha256(sc + HASH_SECRET).digest())
        with sqlite3.connect("scores.db") as scores:
            insert_token(scores, cr.decode())
        response.set_cookie("_SC", sc.decode())
        app.logger.debug(f"(sc, cr) = {(sc, cr)}")
    app.logger.debug(response)
    return response


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


def check_single_use_challenge_response(cr):
    """
    Check if client has previously authenticated with single use challenge
    response method and obtained a token that is still current.
    """
    with sqlite3.connect("scores.db") as scores:
        authed = query_token(scores, cr)
    return authed


def check_auth(request):
    """Returns the games for which the request is authorized to submit scores."""
    authed = []
    cr = request.cookies.get("_CR")
    nonce = request.cookies.get("NONCE")
    digest = request.cookies.get("DIGEST")
    if cr:
        if check_single_use_challenge_response(cr):
            authed.append("BUTTON")
    if nonce and digest:
        if check_basic_digest(nonce, digest):
            authed.append("TIMING")
    return authed


def insert_or_update_score(conn, score_entry):
    """
    Update the given database with the given score.

    If given score is 'better' than the one in the database, update the entry
    with the new score. Either way, update the time played. Determining if an
    entry is better requires a game-specific score selection function and a
    game-specific type function for scores that come in as strings.
    """
    app.logger.debug(f"score update info: {score_entry}")
    game = score_entry["game"].upper()
    select = SCORE_COMPARISONS_BY_GAME[game]["select"]
    cast = SCORE_COMPARISONS_BY_GAME[game]["cast"]
    username = score_entry["username"]
    score = score_entry["score"]

    cursor = conn.cursor()

    try:
        [old_score] = cursor.execute(
            f"SELECT score FROM {game} WHERE username = ?;", (username,)
        ).fetchone()
        app.logger.debug(f"found existing entry for username: {old_score}")
    except TypeError:
        # queries with no results return `None` instead of `[]`
        replace_score = score
    else:
        replace_score = select(cast(old_score), cast(score))

    insert_sql = f"""
        INSERT OR REPLACE INTO {game} 
        (username, score, date)
        VALUES (?, ?, datetime())
    """
    cursor.execute(insert_sql, (username, replace_score))


@app.route("/submissionOK")
def sub_ok():
    """Return page confirming submission succeeded"""
    return render_template("submissionOK.html")


@app.route("/submit", methods=["GET", "POST"])
def submit():
    """
    Provide form for submitting scores.

    GET returns the form. A POST of the form is checked for authentication
    and then the data is inserted into the database.
    """
    response = render_template("submit.html")
    # PRG pattern

    authed_for = check_auth(request)
    app.logger.info(f"request is authenticated for {authed_for}")

    sub_for = request.form.get("game") if request.method == "POST" else []
    if sub_for.upper() in authed_for:
        try:
            with sqlite3.connect("scores.db") as scores:
                insert_or_update_score(scores, request.form)
                scores.commit()
        except Exception as e:
            # leave default response
            app.logger.info(f"failed score update with {type(e)}: {e.args[0]}")
            pass
        else:
            # submission success
            response = redirect(url_for("sub_ok"), code=303)
            app.logger.info("successful score update")
    return response


def getLogLevels():
    """Return available log level names."""
    try:
        level_names = logging.getLevelNamesMapping().keys()
    except AttributeError:
        # getLevelNamesMapping only present in >= Python3.11
        level_names = list(
            logging.getLevelName(level)
            for level in range(logging.NOTSET, logging.CRITICAL + 1)
        )
        level_names = (level for level in level_names if not level.startswith("Level"))
    return list(level_names)


PARSER = argparse.ArgumentParser(description="Server for logging scores")
PARSER.add_argument("--port", help="Port to use. Defaults to 5000.")
PARSER.add_argument(
    "--log-level",
    choices=getLogLevels(),
    default="INFO",
    help="Set log level to one of the named levels.",
)


def main():
    """Main entrypoint for score server."""
    args = PARSER.parse_args()

    numeric_level = getattr(logging, args.log_level)
    logging.basicConfig(level=numeric_level)
    logging.info(f"Log level set to {args.log_level}[{numeric_level}]")

    app.run(port=args.port)


if __name__ == "__main__":
    main()
