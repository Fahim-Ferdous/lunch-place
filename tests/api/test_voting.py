from fastapi import status
from fastapi.testclient import TestClient
from freezegun import freeze_time

import auth
import models


@freeze_time("2023-10-26 9:00:00")
def test_user_cannot_vote_twice(client: TestClient) -> None:
    # We need a new token because we froze time for this test, but not when pytest fixture generated the token.
    new_auth_token_for_employee = auth.create_access_token(
        2, "employee1", models.Roles.EMPLOYEE
    ).access_token
    assert (
        client.post(
            "/vote/1",
            headers={"Authorization": f"Bearer {new_auth_token_for_employee}"},
        ).status_code
        == status.HTTP_202_ACCEPTED
    )

    assert (
        client.post(
            "/vote/1",
            headers={"Authorization": f"Bearer {new_auth_token_for_employee}"},
        ).status_code
        == status.HTTP_409_CONFLICT
    )


@freeze_time("2023-10-26 9:00:00")
def test_vote_does_not_conflict_with_other_users(client: TestClient) -> None:
    new_auth_token_for_employee = auth.create_access_token(
        2, "employee1", models.Roles.EMPLOYEE
    ).access_token
    assert (
        client.post(
            "/vote/1",
            headers={"Authorization": f"Bearer {new_auth_token_for_employee}"},
        ).status_code
        == status.HTTP_202_ACCEPTED
    )

    new_auth_token_for_employee2 = auth.create_access_token(
        4, "employee2", models.Roles.EMPLOYEE
    ).access_token
    assert (
        client.post(
            "/vote/2",
            headers={"Authorization": f"Bearer {new_auth_token_for_employee2}"},
        ).status_code
        == status.HTTP_202_ACCEPTED
    )


@freeze_time("2023-10-26 14:00:00")
def test_vote_only_before_lunch(client: TestClient) -> None:
    new_auth_token_for_employee = auth.create_access_token(
        2, "employee1", models.Roles.EMPLOYEE
    ).access_token
    assert (
        client.post(
            "/vote/1",
            headers={"Authorization": f"Bearer {new_auth_token_for_employee}"},
        ).status_code
        == status.HTTP_403_FORBIDDEN
    )
