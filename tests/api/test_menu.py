import sys

from fastapi import status
from fastapi.testclient import TestClient

by_name = lambda x: x["name"]


def test_get_menu_returns_all(client: TestClient, restaurateur_auth_token: str) -> None:
    items1 = [
        {"name": "ItemNoDay1", "price": 420},
        {"name": "ItemNoDay2", "price": 420},
        {"name": "ItemNoDay3", "price": 420},
    ]
    items2 = [
        {"name": "ItemWithDay4", "price": 420},
        {"name": "ItemWithDay5", "price": 420},
    ]
    assert (
        client.post(
            "/menu",
            json=items1,
            headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
        ).status_code
        == status.HTTP_201_CREATED
    )
    assert (
        client.post(
            "/menu?day=sunday",
            json=items2,
            headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
        ).status_code
        == status.HTTP_201_CREATED
    )
    r = client.get(
        "/menu?all=true",
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )

    assert r.status_code == status.HTTP_200_OK
    assert [i["name"] for i in items1 + items2] == [i["name"] for i in r.json()]


def test_add_menu(client: TestClient, restaurateur_auth_token: str) -> None:
    items = [
        {"name": "Item1", "price": 420},
        {"name": "Item2", "price": 420},
        {"name": "Item3", "price": 420},
    ]
    r = client.post(
        "/menu",
        json=items,
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )

    assert r.status_code == status.HTTP_201_CREATED

    r = client.get(
        "/menu",
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )

    assert r.status_code == status.HTTP_200_OK
    assert [i["name"] for i in items] == [i["name"] for i in r.json()]


def test_add_menu_with_day(client: TestClient, restaurateur_auth_token: str) -> None:
    items = [
        {"name": "Item4", "price": 420},
        {"name": "Item5", "price": 420},
    ]
    r = client.post(
        "/menu?day=sunday",
        json=items,
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )

    assert r.status_code == status.HTTP_201_CREATED

    r = client.get(
        "/menu?day=sunday",
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )

    assert r.status_code == status.HTTP_200_OK
    assert [i["name"] for i in items] == [i["name"] for i in r.json()]
