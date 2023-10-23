from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import models
import schemas
from auth import create_access_token
from config import settings
from database import get_db
from main import app
from models import Base, Roles, Weekdays


@pytest.fixture(scope="session")
def db() -> Generator[Session, None, None]:
    yield TestingSessionLocal()


@pytest.fixture(scope="session")
def employee_auth_token() -> Generator[str, None, None]:
    yield create_access_token("employee1", Roles.EMPLOYEE).access_token


@pytest.fixture(scope="session")
def restaurateur_auth_token() -> Generator[str, None, None]:
    yield create_access_token("restaurateur", Roles.RESTAURATEUR).access_token


@pytest.fixture(scope="session")
def admin_auth_token() -> Generator[str, None, None]:
    yield create_access_token(settings.ROOT_USERNAME, Roles.ADMIN).access_token


TEST_SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)


def create_dummy_data() -> None:
    restaurants = [schemas.RestaurantCreate(name="restaurant1")]

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
    ]

    test_db = TestingSessionLocal()
    try:
        for r in restaurants:
            empty_menus = [
                models.DailyMenu(
                    **(schemas.DailyMenuCreate(day=dm, items=[])).model_dump()
                )
                for dm in Weekdays
            ]

            test_db.add(
                models.Restaurant(**(r.model_dump() | {"daily_menus": empty_menus}))
            )

        for u in users:
            test_db.add(models.User(**u.model_dump()))

        test_db.commit()
    finally:
        test_db.close()


def override_get_db() -> Generator[Session, None, None]:
    test_db = TestingSessionLocal()
    try:
        yield test_db
    finally:
        test_db.close()


app.dependency_overrides[get_db] = override_get_db
create_dummy_data()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c
