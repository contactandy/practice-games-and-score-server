"""
Score server that includes an authentication process and a score submission
process.
"""
import hashlib
import secrets
import sqlite3

from flask import Flask, make_response, redirect, render_template, request, url_for

app = Flask(__name__)


@app.route("/")
@app.route("/index")
def index():
    """Return main page"""
    return render_template("index.html")


with sqlite3.connect("scores.db") as scores:
    scores.execute(
        """
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT UNIQUE,
            created TIMESTAMP 
        );
        """
    )
    scores.execute(
        """
        CREATE TABLE IF NOT EXISTS button (
            username TEXT UNIQUE,
            score INTEGER DEFAULT 0, 
            date DATETIME
        );
        """
    )
    scores.execute(
        """
        CREATE TABLE IF NOT EXISTS timing ( 
            username TEXT UNIQUE, 
            score FLOAT NOT NULL, 
            date DATETIME 
        );
        """
    )
    scores.commit()

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

EXPIRE = 10


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

    When a client visits this endpoint, a paired (sc, sr) value is created
    such that sr is the hash of sc with a secret key. Because this server is
    for exercises, the key is hardcoded into the app. The sc value is sent
    as a cookie in the response to the client. The sr value is stored in the
    tokens database for reference by the submit endpoint.
    """
    response = make_response(redirect(url_for("index")))
    good_ua = request.headers["user-agent"] == "basic-games"
    if request.method == "GET" and good_ua:
        app.logger.debug("Received request to initiate auth")
        sc = secrets.base64.b64encode(secrets.token_bytes(32))
        sr = secrets.base64.b64encode(hashlib.sha256(sc + HASH_SECRET).digest())
        with sqlite3.connect("scores.db") as scores:
            insert_token(scores, sr.decode())
        response.set_cookie("_SC", sc.decode())
        app.logger.debug(f"(sc, sr) = {(sc, sr)}")
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
        "DELETE FROM tokens WHERE created < CURRENT_TIMESTAMP - ?;", (EXPIRE,)
    )
    results = cursor.execute(
        "SELECT * FROM tokens WHERE token = ?;", (token,)
    ).fetchall()
    # tokens will be single use
    cursor.execute("DELETE FROM tokens WHERE token = ?;", (token,))
    return results


def check_auth(request):
    """Check that request has a single use token stored in the tokens database"""
    authed = False
    sr = request.cookies.get("_SR")
    app.logger.debug(f"Found sr cookie: {sr}")
    if sr:
        with sqlite3.connect("scores.db") as scores:
            authed = query_token(scores, sr)
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
    if request.method == "POST" and check_auth(request):
        app.logger.info("POST is authenticated")
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


def main():
    """Main entrypoint for score server"""
    app.run(debug=True)


if __name__ == "__main__":
    main()
