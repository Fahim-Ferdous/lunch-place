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


# This one is for the crud tests to use.
@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    with TestingSessionLocal() as session:
        yield session
        for t in reversed(Base.metadata.sorted_tables):
            session.execute(t.delete())
        session.commit()
    create_dummy_data()


# And this one is for the backend to use, aka for api tests.
def override_get_db() -> Generator[Session, None, None]:
    with TestingSessionLocal() as session:
        yield session


@pytest.fixture(scope="session")
def employee_auth_token() -> Generator[str, None, None]:
    yield create_access_token("employee1", Roles.EMPLOYEE).access_token


@pytest.fixture(scope="session")
def restaurateur_auth_token() -> Generator[str, None, None]:
    yield create_access_token("restaurateur", Roles.RESTAURATEUR, 1).access_token


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

    with TestingSessionLocal() as session:
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


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestingSessionLocal() as session:
        for t in reversed(Base.metadata.sorted_tables):
            session.execute(t.delete())
        session.commit()
    create_dummy_data()
    with TestClient(app) as c:
        yield c
