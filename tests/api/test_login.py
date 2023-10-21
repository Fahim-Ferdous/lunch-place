from fastapi import status
from fastapi.testclient import TestClient

from config import settings


def test_get_access_token(client: TestClient) -> None:
    login_data = {
        "username": settings.ROOT_USERNAME,
        "password": settings.ROOT_PASSWORD,
    }
    r = client.post(f"/login", data=login_data)
    tokens = r.json()
    assert r.status_code == status.HTTP_200_OK
    assert "access_token" in tokens
    assert tokens["access_token"] != ""


def test_incorrect_password(client: TestClient) -> None:
    login_data = {
        "username": settings.ROOT_USERNAME,
        "password": settings.ROOT_PASSWORD + "garbage",
    }
    r = client.post(f"/login", data=login_data)
    err_msg = r.json()
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
    assert "access_token" not in err_msg
    assert "detail" in err_msg
    assert err_msg["detail"] == "Incorrect username or password"
