"""
Score server that includes an authentication process and a score submission
process.
"""
import sqlite3

from flask import (
    Blueprint,
    current_app,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)

from score_server import auth_manager, score_manager

scoreboard = Blueprint("scoreboard", __name__)


@scoreboard.route("/")
@scoreboard.route("/index")
def index():
    """Return main page"""
    return render_template("index.html")


@scoreboard.route("/scores", methods=["GET"])
def show_scores():
    """Return page with score tables for each game."""
    game_data = dict()
    with sqlite3.connect(current_app.config["DB"]) as scores:
        cursor = scores.cursor()
        for game in score_manager.SCORE_COMPARISONS_BY_GAME:
            cursor.execute(f"SELECT * FROM {game}")
            game_data[game] = cursor.fetchall()
            current_app.logger.debug(f"game `{game}` scores: {game_data[game]}")
    return render_template(
        "highscores.html", button=game_data["BUTTON"], timing=game_data["TIMING"]
    )


@scoreboard.route("/auth", methods=["GET"])
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
    current_app.logger.debug("Received request to initiate auth")
    response = make_response(redirect(url_for("scoreboard.index")))
    good_ua = request.headers["user-agent"] == "basic-games"
    if request.method == "GET" and good_ua:
        sc = auth_manager.init_auth(current_app.config["DB"])
        response.set_cookie("_SC", sc)
    current_app.logger.debug(response)
    return response


@scoreboard.route("/submissionOK")
def sub_ok():
    """Return page confirming submission succeeded"""
    return render_template("submissionOK.html")


@scoreboard.route("/submit", methods=["GET", "POST"])
def submit():
    """
    Provide form for submitting scores.

    GET returns the form. A POST of the form is checked for authentication
    and then the data is inserted into the database.
    """
    response = render_template("submit.html")
    # PRG pattern

    authed_for = auth_manager.check_auth(current_app.config["DB"], request)
    current_app.logger.info(f"request is authenticated for {authed_for}")

    sub_for = request.form.get("game") if request.method == "POST" else []
    if sub_for.upper() in authed_for:
        try:
            with sqlite3.connect(current_app.config["DB"]) as scores:
                score_manager.insert_or_update_score(scores, request.form)
                scores.commit()
        except Exception as e:
            # leave default response
            current_app.logger.info(f"failed score update with {type(e)}: {e.args[0]}")
            pass
        else:
            # submission success
            response = redirect(url_for("scoreboard.sub_ok"), code=303)
            current_app.logger.info("successful score update")
    return response
