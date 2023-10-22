from fastapi import status
from fastapi.testclient import TestClient


def test_non_admin_cant_create_restaurant(
    client: TestClient, restaurateur_auth_token: str
) -> None:
    r = client.post(
        f"/restaurants/",
        json={
            "name": "newrestaurant1",
            "description": "Description describing description.",
        },
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )
    assert r.status_code == status.HTTP_403_FORBIDDEN


def test_create_restaurant(client: TestClient, admin_auth_token: str) -> None:
    r = client.post(
        f"/restaurants/",
        json={
            "name": "newrestaurant1",
            "description": "Description describing description.",
        },
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert r.status_code == status.HTTP_201_CREATED
    assert "id" in r.json()
