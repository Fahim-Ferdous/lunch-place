from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import models
import schemas
from auth import create_access_token
from config import get_settings
from crud import create_root_user
from main import app
from models import Base, Roles, Weekdays


# This one is for the crud tests to use.
@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    create_dummy_data()
    with TestingSessionLocal() as session:
        yield session


@pytest.fixture(scope="session")
def admin_auth_token() -> Generator[str, None, None]:
    yield create_access_token(1, get_settings().ROOT_USERNAME, Roles.ADMIN).access_token


@pytest.fixture(scope="function")
def employee_auth_token() -> Generator[str, None, None]:
    yield create_access_token(2, "employee1", Roles.EMPLOYEE).access_token


@pytest.fixture(scope="session")
def restaurateur_auth_token() -> Generator[str, None, None]:
    yield create_access_token(3, "restaurateur", Roles.RESTAURATEUR, 1).access_token


@pytest.fixture(scope="function")
def employee_auth_token2() -> Generator[str, None, None]:
    yield create_access_token(4, "employee2", Roles.EMPLOYEE).access_token


engine = create_engine(
    get_settings().SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)


def create_dummy_data(
    sessionmaker: sessionmaker[Session] = TestingSessionLocal,
) -> None:
    with sessionmaker() as session:
        for t in reversed(Base.metadata.sorted_tables):
            session.execute(t.delete())
        session.commit()

    restaurants = [
        schemas.RestaurantCreate(name="restaurant1"),
        schemas.RestaurantCreate(name="restaurant2"),
    ]

    users = [
        schemas.UserCreate(
            username="employee1",
            role=Roles.EMPLOYEE,
            email="employee1@email.com",
            password="pass1",
        ),
        schemas.UserCreate(
            username="restaurateur1",
            role=Roles.RESTAURATEUR,
            email="restaurateur1@email.com",
            password="pass1",
            restaurant_id=1,
        ),
        schemas.UserCreate(
            username="employee2",
            role=Roles.EMPLOYEE,
            email="employee2@email.com",
            password="pass1",
        ),
    ]

    with sessionmaker() as session:
        create_root_user(session)

        for r in restaurants:
            empty_menus = [
                models.DailyMenu(
                    **(schemas.DailyMenuCreate(day=dm, items=[])).model_dump()
                )
                for dm in Weekdays
            ]

            session.add(
                models.Restaurant(**(r.model_dump() | {"daily_menus": empty_menus}))
            )

        for u in users:
            session.add(models.User(**u.model_dump()))

        session.commit()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    create_dummy_data()
    with TestClient(app) as c:
        yield c
