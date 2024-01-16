"""Test score_server/routes routines."""

from http import HTTPStatus

from bs4 import BeautifulSoup


def test_show_scores(client):
    """Test show_scores endpoint."""
    response = client.get("/scores")
    assert response.status_code == HTTPStatus.OK
    soup = BeautifulSoup(response.data, "html.parser")
    assert soup.title.string == "High Scores"
    for table in soup.find_all("table"):
        num_non_header_rows = len(table.find_all("tr")) - 1
        assert num_non_header_rows == 0


LEN_BASE64_ENCODED_32_BYTES = 44


def test_do_auth(client):
    """Test do_auth endpoint."""
    response = client.get("/auth")
    assert response.status_code == HTTPStatus.FOUND
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
