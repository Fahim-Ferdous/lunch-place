from typing import Generator, final

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
import schemas
from auth import create_access_token
from config import settings
from database import SessionLocal, get_db
from main import app
from models import Base, Roles


@pytest.fixture(scope="session")
def db() -> Generator:
    yield SessionLocal()


@pytest.fixture(scope="session")
def employee_auth_token() -> Generator:
    yield create_access_token("employee1", Roles.EMPLOYEE).access_token


@pytest.fixture(scope="session")
def restaurateur_auth_token() -> Generator:
    yield create_access_token("restaurateur", Roles.RESTAURATEUR).access_token


@pytest.fixture(scope="session")
def admin_auth_token() -> Generator:
    yield create_access_token(settings.ROOT_USERNAME, Roles.ADMIN).access_token


SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)


def create_dummy_data():
    test_db = TestingSessionLocal()
    try:
        for u in [
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
            ),
        ]:
            test_db.add(models.User(**u.model_dump()))
        test_db.commit()
    finally:
        test_db.close()


create_dummy_data()


def override_get_db():
    test_db = TestingSessionLocal()
    try:
        yield test_db
    finally:
        test_db.close()  # type: ignore [reportUnboundVariable]


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c
