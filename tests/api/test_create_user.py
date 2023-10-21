from fastapi import status
from fastapi.testclient import TestClient

from auth import Token


def test_create_user(client: TestClient, admin_auth_token: Token):
    r = client.post(
        "/users",
        json={
            "username": "jalal",
            "password": "hello123",
            "role": "employee",
            "email": "email@email.com",
        },
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    assert r.status_code == 201


def test_non_admin_cant_create_user(client: TestClient, employee_auth_token: Token):
    r = client.post(
        "/users",
        json={
            "username": "jalal",
            "password": "hello123",
            "role": "employee",
            "email": "email@email.com",
        },
        headers={"Authorization": f"Bearer {employee_auth_token}"},
    )

    assert r.status_code == status.HTTP_403_FORBIDDEN


def test_username_email_conflicts(client: TestClient, admin_auth_token: Token):
    for u, v in [
        (
            {
                "username": "employee1",
                "password": "hello123",
                "role": "employee",
                "email": "employee1@email.com",
            },
            "Username and Email already registered",
        ),
        (
            {
                "username": "employee1",
                "password": "hello123",
                "role": "employee",
                "email": "newemployee1@email.com",
            },
            "Username already registered",
        ),
        (
            {
                "username": "newemployee1",
                "password": "hello123",
                "role": "employee",
                "email": "employee1@email.com",
            },
            "Email already registered",
        ),
    ]:
        r = client.post(
            "/users",
            json=u,
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )

        err_msg = r.json()
        assert r.status_code == status.HTTP_409_CONFLICT
        assert "detail" in err_msg
        assert err_msg["detail"] == v
