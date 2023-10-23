from typing import Any

from fastapi import status
from fastapi.testclient import TestClient

by_name = lambda x: x["name"]


def test_get_items_returns_unassigned(
    client: TestClient, restaurateur_auth_token: str
) -> None:
    items1, _, _ = create_dummy_items(client, restaurateur_auth_token)
    r = client.get(
        "/menu",
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )

    assert r.status_code == status.HTTP_200_OK
    assert items1 == r.json()


def test_get_items_returns_specific_day(
    client: TestClient, restaurateur_auth_token: str
) -> None:
    _, items2, items3 = create_dummy_items(client, restaurateur_auth_token)
    r = client.get(
        "/menu?day=sunday",
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )

    assert r.status_code == status.HTTP_200_OK
    assert items2 == r.json()

    r = client.get(
        "/menu?day=monday",
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )

    assert r.status_code == status.HTTP_200_OK
    assert items3 == r.json()


def test_get_items_returns_all(
    client: TestClient, restaurateur_auth_token: str
) -> None:
    items1, items2, items3 = create_dummy_items(client, restaurateur_auth_token)
    r = client.get(
        "/menu?all=true",
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )

    assert r.status_code == status.HTTP_200_OK
    assert items1 + items2 + items3 == r.json()


def test_create_item(client: TestClient, restaurateur_auth_token: str) -> None:
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


def test_create_item_with_day(client: TestClient, restaurateur_auth_token: str) -> None:
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


dict_list = list[dict[str, Any]]


def create_dummy_items(
    client: TestClient, restaurateur_auth_token: str
) -> tuple[dict_list, dict_list, dict_list]:
    r1 = client.post(
        "/menu",
        json=[
            {"name": "ItemNoDay1", "price": 420},
            {"name": "ItemNoDay2", "price": 420},
            {"name": "ItemNoDay3", "price": 420},
        ],
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )
    assert r1.status_code == status.HTTP_201_CREATED

    r2 = client.post(
        "/menu?day=sunday",
        json=[
            {"name": "ItemSunday4", "price": 420},
            {"name": "ItemSunday5", "price": 420},
        ],
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )
    assert r2.status_code == status.HTTP_201_CREATED

    r3 = client.post(
        "/menu?day=monday",
        json=[
            {"name": "ItemMonday4", "price": 420},
            {"name": "ItemMonday5", "price": 420},
        ],
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )
    assert r3.status_code == status.HTTP_201_CREATED

    return (r1.json(), r2.json(), r3.json())


def test_delete_menu(client: TestClient, restaurateur_auth_token: str) -> None:
    items1, items2, items3 = create_dummy_items(client, restaurateur_auth_token)
    # Delete the items.
    r = client.patch(
        "/menu",
        json={"op": "delete", "ids": [items1[-1]["id"]]},
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )
    assert r.status_code == status.HTTP_200_OK
    del items1[-1]

    # Check if the items were deleted.
    r = client.get(
        "/menu?all=true",
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )

    assert r.status_code == status.HTTP_200_OK
    assert r.json() == items1 + items2 + items3


def test_delete_fails_with_day(
    client: TestClient, restaurateur_auth_token: str
) -> None:
    items1, items2, _ = create_dummy_items(client, restaurateur_auth_token)

    assert (
        client.patch(
            "/menu",
            json={"op": "delete", "day": "sunday", "ids": [items1[-1]["id"]]},
            headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
        ).status_code
        == status.HTTP_422_UNPROCESSABLE_ENTITY
    )
    assert (
        client.patch(
            "/menu",
            json={"op": "delete", "day": "sunday", "ids": [items2[-1]["id"]]},
            headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
        ).status_code
        == status.HTTP_422_UNPROCESSABLE_ENTITY
    )


def test_add_remove_items_to_menu_requires_day(
    client: TestClient, restaurateur_auth_token: str
) -> None:
    items1, items2, _ = create_dummy_items(client, restaurateur_auth_token)

    assert (
        client.patch(
            "/menu",
            json={"op": "add", "ids": [items1[-1]["id"]]},
            headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
        ).status_code
        == status.HTTP_422_UNPROCESSABLE_ENTITY
    )
    assert (
        client.patch(
            "/menu",
            json={"op": "remove", "ids": [items2[-1]["id"]]},
            headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
        ).status_code
        == status.HTTP_422_UNPROCESSABLE_ENTITY
    )


def test_add_to_menu(client: TestClient, restaurateur_auth_token: str) -> None:
    items1, items2, items3 = create_dummy_items(client, restaurateur_auth_token)

    assert (
        client.patch(
            "/menu",
            json={"op": "add", "day": "sunday", "ids": [items1[-1]["id"]]},
            headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
        ).status_code
        == status.HTTP_200_OK
    )
    items2.insert(0, items1[-1])
    items1 = items1[:-1]

    r = client.get(
        "/menu",
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )
    assert r.status_code == status.HTTP_200_OK
    assert items1 == r.json()

    r = client.get(
        "/menu?day=sunday",
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )
    assert r.status_code == status.HTTP_200_OK
    assert items2 == r.json()

    r = client.get(
        "/menu?day=monday",
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )
    assert r.status_code == status.HTTP_200_OK
    assert items3 == r.json()


def test_remove_from_menu(client: TestClient, restaurateur_auth_token: str) -> None:
    items1, items2, items3 = create_dummy_items(client, restaurateur_auth_token)

    # Test the patch.
    assert (
        client.patch(
            "/menu",
            json={"op": "remove", "day": "sunday", "ids": [items2[-1]["id"]]},
            headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
        ).status_code
        == status.HTTP_200_OK
    )
    items1.append(items2[-1])
    items2 = items2[:-1]

    r = client.get(
        "/menu",
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )
    assert r.status_code == status.HTTP_200_OK
    assert items1 == r.json()

    r = client.get(
        "/menu?day=sunday",
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )
    assert r.status_code == status.HTTP_200_OK
    assert items2 == r.json()

    r = client.get(
        "/menu?day=monday",
        headers={"Authorization": f"Bearer {restaurateur_auth_token}"},
    )
    assert r.status_code == status.HTTP_200_OK
    assert items3 == r.json()
