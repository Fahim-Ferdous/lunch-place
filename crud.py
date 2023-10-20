import secrets

from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import user

import auth
import models
import schemas
from config import settings
from database import Base, engine


def create_root_user(
    db: Session, username: str | None = None, password: str | None = None
) -> None:
    """
    Should run on startup. Check if there is at least one admin. If not, create one.
    """
    if db.query(models.User).filter(models.User.role == models.Roles.ADMIN).count() > 0:
        return

    Base.metadata.create_all(engine)

    if username is None:
        username = "root"
    if password is None:
        # TODO: Validate password.
        password = secrets.token_urlsafe(settings.PASSWORD_MAX_LENGTH)

    hashed_password = auth.pwd_context.hash(password)

    db.add(
        models.User(
            username=username, password=hashed_password, role=models.Roles.ADMIN
        )
    )
    db.commit()

    print(f"Admin credentials, {username}:{password}")


def is_email_username_registered(
    db: Session, email: str, username: str
) -> tuple[bool, bool]:
    l = (
        db.query(models.User)
        .filter(or_(models.User.username == username, models.User.email == email))
        .all()
    )

    u = False
    e = False
    for i in l:
        if i.username == username:
            u = True
        if i.email == email:
            e = True

    return (u, e)


def get_user(db: Session, username: str) -> models.User:
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    password = auth.pwd_context.hash(user.password)
    db_user = models.User(
        username=user.username, email=user.email, password=password, role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()
