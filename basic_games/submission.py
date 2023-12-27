"""Submit information (scores) to (score) server."""
import hashlib
import logging
import secrets

import requests

RETRIES = 5

logging.basicConfig(level=logging.DEBUG)

GAME_SERVER = "http://127.0.0.1:5000"
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

    def __init__(self, method):
        """Select an authentication method."""
        self.method = getattr(self, method)

    def do_auth(self, method):
        """Authenticate with the selected method."""
        self.method()

    def __enter__(self):
        """Method to support context manager."""
        self.session = requests.Session()
        self.session.headers.update({"user-agent": "basic-games"})
        try:
            self.do_auth(self.method)
        except Exception:
            raise AuthSetupFail("failed to authenticate to server")
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Method to support context manager."""
        self.session.close()

    def single_use_challenge_response(self):
        """An authentication method for the game server."""
        AUTH = GAME_SERVER + AUTH_ENDPOINT
        self.session.get(AUTH)
        sc = self.session.cookies["_SC"].encode()
        sr = secrets.base64.b64encode(hashlib.sha256(sc + HASH_SECRET).digest())
        logging.debug(f"Auth: (sc, sr) = {(sc, sr)}")
        # self.session.headers.update({"_SR": secrets.base64.b64encode(sr)})
        # TODO ideally create cookie as cookie object
        self.session.cookies.set("_SR", sr.decode())


def attempt_posts_with(auth_method, post_info):
    """
    Send info as data in a post to server after authenticating with the
    given method.
    """
    for attempt in range(RETRIES):
        with AuthedSession(auth_method) as s:
            resp = s.post(
                GAME_SERVER + SCORE_ENDPOINT, data=post_info, allow_redirects=False
            )
            logging.debug(
                f"Submit score attempt {attempt}: response {resp.status_code},"
                f"location {resp.headers.get('location')}"
            )
            redirected = resp.status_code == requests.codes.SEE_OTHER
            location_ok = resp.headers.get("location") == "/submissionOK"
            if redirected and location_ok:
                break
