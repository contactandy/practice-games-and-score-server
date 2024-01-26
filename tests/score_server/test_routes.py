"""Test score_server/routes routines."""

import hashlib
import secrets

import pytest
import requests
from bs4 import BeautifulSoup

from score_server.auth_manager import HASH_SECRET


def test_show_scores(client):
    """Test show_scores endpoint."""
    response = client.get("/scores")
    assert response.status_code == requests.codes.OK
    soup = BeautifulSoup(response.data, "html.parser")
    assert soup.title.string == "High Scores"
    for table in soup.find_all("table"):
        num_non_header_rows = len(table.find_all("tr")) - 1
        assert num_non_header_rows == 0


LEN_BASE64_ENCODED_32_BYTES = 44


def test_do_auth(client):
    """Test do_auth endpoint."""
    response = client.get("/auth")
    assert response.status_code == requests.codes.FOUND
    print(response.headers)
    sc_cookie = client.get_cookie("_SC")
    assert sc_cookie is not None
    assert len(sc_cookie.value) == LEN_BASE64_ENCODED_32_BYTES
    client.delete_cookie("_SC")

    response = client.get("/auth")
    print(response.headers)
    new_sc_cookie = client.get_cookie("_SC")
    assert new_sc_cookie is not None
    assert new_sc_cookie.value != sc_cookie.value
    client.delete_cookie("_SC")

    headers = {
        "user-agent": "NOT basic-games",
    }
    response = client.get("/auth", headers=headers)
    print(response.headers)
    assert client.get_cookie("_SC") is None


def test_sub_ok(client):
    """Test sub_ok endpoint."""
    response = client.get("/submissionOK")
    assert response.status_code == requests.codes.OK


@pytest.fixture
def score_data():
    """Sample score submission data for use by a client."""
    return [
        {"game": "button", "username": "user", "score": "10"},
        {"game": "timing", "username": "user", "score": "15.976295709609985"},
        {"game": "FAKE", "username": "user", "score": "6"},
    ]


class TestSubmit:
    """Test submit endpoint."""

    def assert_submit_success(self, response):
        assert response.status_code == requests.codes.SEE_OTHER
        assert response.headers.get("location") == "/submissionOK"

    def assert_submit_failure(self, response):
        assert response.status_code == requests.codes.OK

    def test_get(self, client):
        """Test get to submit endpoint."""
        response = client.get("/submit")
        assert response.status_code == requests.codes.OK
        soup = BeautifulSoup(response.data, "html.parser")
        assert soup.title.string == "Score Submission"
        [form] = soup.find_all("form")
        assert form.get("method") == "POST"
        input_fields = [dict(input_elem.attrs) for input_elem in form.find_all("input")]
        assert len(input_fields) == len(["username", "score", "submit"])
        submits = [
            input_field
            for input_field in input_fields
            if input_field["type"] == "submit"
        ]
        assert len(submits) == 1

    def test_button_submit(self, client, score_data):
        """Test POST of button game scores."""
        button_entry, timing_entry, fail_entry = score_data

        client.get("/auth")
        sc = client.get_cookie("_SC").value.encode()
        cr = secrets.base64.b64encode(hashlib.sha256(sc + HASH_SECRET).digest())
        client.set_cookie("_CR", cr.decode())
        response = client.post("/submit", data=button_entry, follow_redirects=False)
        self.assert_submit_success(response)

        already_used_cr = cr
        client.set_cookie("_CR", already_used_cr.decode())
        response = client.post("/submit", data=button_entry, follow_redirects=False)
        self.assert_submit_failure(response)

        bad_cr = secrets.base64.b64encode(secrets.token_bytes(32))
        client.set_cookie("_CR", bad_cr.decode())
        response = client.post("/submit", data=button_entry, follow_redirects=False)
        self.assert_submit_failure(response)

        client.get("/auth")
        sc = client.get_cookie("_SC").value.encode()
        cr = secrets.base64.b64encode(hashlib.sha256(sc + HASH_SECRET).digest())
        client.set_cookie("_CR", cr.decode())
        response = client.post("/submit", data=fail_entry, follow_redirects=False)
        self.assert_submit_failure(response)

    def test_timing_submit(self, client, score_data):
        """Test POST of timing game scores."""
        button_entry, timing_entry, fail_entry = score_data

        nonce = secrets.token_bytes(32)
        digest = hashlib.sha256(nonce + HASH_SECRET).digest()
        client.set_cookie("DIGEST", secrets.base64.b64encode(digest).decode())
        client.set_cookie("NONCE", secrets.base64.b64encode(nonce).decode())
        response = client.post("/submit", data=timing_entry, follow_redirects=False)
        self.assert_submit_success(response)

        # For exercise purposes, this is designed to succeed.
        client.set_cookie("DIGEST", secrets.base64.b64encode(digest).decode())
        client.set_cookie("NONCE", secrets.base64.b64encode(nonce).decode())
        response = client.post("/submit", data=timing_entry, follow_redirects=False)
        self.assert_submit_success(response)

        nonce = secrets.token_bytes(32)
        bad_digest = secrets.base64.b64encode(secrets.token_bytes(32))
        client.set_cookie("DIGEST", secrets.base64.b64encode(bad_digest).decode())
        client.set_cookie("NONCE", secrets.base64.b64encode(nonce).decode())
        response = client.post("/submit", data=timing_entry, follow_redirects=False)
        self.assert_submit_failure(response)

        nonce = secrets.token_bytes(32)
        digest = hashlib.sha256(nonce + HASH_SECRET).digest()
        response = client.post("/submit", data=fail_entry, follow_redirects=False)
        self.assert_submit_failure(response)
