"""Submit information (scores) to (score) server."""
import hashlib
import logging
import secrets

import requests

RETRIES = 5

logging.basicConfig(level=logging.DEBUG)

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
        AUTH = self.location + AUTH_ENDPOINT
        self.session.get(AUTH)
        sc = self.session.cookies["_SC"].encode()
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
    for attempt in range(RETRIES):
        with AuthedSession(game_server, auth_method) as s:
            resp = s.post(
                game_server + SCORE_ENDPOINT, data=post_info, allow_redirects=False
            )
            logging.debug(
                f"Submit score attempt {attempt}: response {resp.status_code},"
                f"location {resp.headers.get('location')}"
            )
            redirected = resp.status_code == requests.codes.SEE_OTHER
            location_ok = resp.headers.get("location") == "/submissionOK"
            if redirected and location_ok:
                break
