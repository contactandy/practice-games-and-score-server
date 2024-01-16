"""Submit information (scores) to (score) server."""
import hashlib
import logging
import secrets

import requests

RETRIES = 5

AUTH_ENDPOINT = "/auth"
SCORE_ENDPOINT = "/submit"

HASH_SECRET = hashlib.sha256(b"LEARNING PURPOSES ONLY").digest()


class AuthSetupFail(Exception):
    """Raise if unable to set up authentication to server."""

    pass


class AuthedSession:
    """
    Prepare a session to send information by first authenticating using a
    selected method.
    """

    def __init__(self, location, method):
        """Select an authentication method."""
        self.method = getattr(self, method)
        self.location = location

    def do_auth(self, method):
        """Authenticate with the selected method."""
        self.method()

    def __enter__(self):
        """Method to support context manager."""
        self.session = requests.Session()
        self.session.headers.update({"user-agent": "basic-games"})
        self.do_auth(self.method)
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Method to support context manager."""
        self.session.close()

    def single_use_challenge_response(self):
        """An authentication method for the game server."""
        AUTH = self.location + AUTH_ENDPOINT
        try:
            self.session.get(AUTH)
        except requests.exceptions.ConnectionError:
            raise AuthSetupFail("Unable to connect to /auth endpoint")
        try:
            sc = self.session.cookies["_SC"].encode()
        except KeyError:
            raise AuthSetupFail(
                "/auth endpoint did not provide server challenge cookie `_SC`"
            )
        cr = secrets.base64.b64encode(hashlib.sha256(sc + HASH_SECRET).digest())
        logging.debug(f"Auth: (sc, cr) = {(sc, cr)}")
        # self.session.headers.update({"_SR": secrets.base64.b64encode(cr)})
        # TODO ideally create cookie as cookie object
        self.session.cookies.set("_CR", cr.decode())

    def basic_digest(self):
        """An authentication method for the game server."""
        nonce = secrets.token_bytes(32)
        digest = hashlib.sha256(nonce + HASH_SECRET).digest()
        # TODO ideally create cookie as cookie object
        self.session.cookies.set("DIGEST", secrets.base64.b64encode(digest).decode())
        self.session.cookies.set("NONCE", secrets.base64.b64encode(nonce).decode())


def attempt_posts_with(dst_socket, auth_method, post_info):
    """
    Send info as data in a post to server after authenticating with the
    given method.
    """
    dst_addr, dst_port = dst_socket
    game_server = f"http://{dst_addr}:{dst_port}"
    success = False
    for attempt in range(RETRIES):
        try:
            with AuthedSession(game_server, auth_method) as s:
                try:
                    resp = s.post(
                        game_server + SCORE_ENDPOINT,
                        data=post_info,
                        allow_redirects=False,
                    )
                except requests.exceptions.ConnectionError:
                    logging.debug(
                        f"Failed attempt {attempt} to connect to score server"
                    )
                    continue
                redirected = resp.status_code == requests.codes.SEE_OTHER
                location_ok = resp.headers.get("location") == "/submissionOK"
                if success := redirected and location_ok:
                    break
                else:
                    logging.debug(
                        f"In attempt {attempt}, submission received response "
                        f"{resp.status_code}, to location "
                        f"{resp.headers.get('location')}"
                    )
        except AuthSetupFail as auth_fail:
            logging.debug(
                f"Failed attempt {attempt} to authenticate to score server: "
                f"{auth_fail.args[0]}"
            )
        except Exception:
            logging.debug(
                "Failed score server connection for unknown reason", exc_info=True
            )
    if success:
        logging.info("Submitted score to server")
    else:
        logging.info("Failed to submit score to server")
