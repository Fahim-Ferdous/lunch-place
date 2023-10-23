from sqlalchemy import or_
from sqlalchemy.orm import Session

import auth
import models
import schemas
from config import settings
from database import engine
from models import Base


def create_root_user(db: Session) -> None:
    """
    Should run on startup. Check if there is at least one admin. If not, create one.
    """
    if db.query(models.User).filter(models.User.role == models.Roles.ADMIN).count() > 0:
        return

    Base.metadata.create_all(engine)

    hashed_password = auth.pwd_context.hash(settings.ROOT_PASSWORD)

    db.add(
        models.User(
            username=settings.ROOT_USERNAME,
            password=hashed_password,
            email=settings.ROOT_EMAIL,
            role=models.Roles.ADMIN,
        )
    )
    db.commit()


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


def get_user(db: Session, username: str) -> models.User | None:
    return db.query(models.User).filter(models.User.username == username).first()


def create_restaurant(
    db: Session, restaurant: schemas.RestaurantCreate
) -> models.Restaurant:
    empty_menus = [
        models.DailyMenu(**(schemas.DailyMenuCreate(day=dm, items=[])).model_dump())
        for dm in models.Weekdays
    ]

    r = models.Restaurant(**(restaurant.model_dump() | {"daily_menus": empty_menus}))
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    db_user = models.User(**user.model_dump())
    db_user.password = auth.get_password_hash(user.password)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
