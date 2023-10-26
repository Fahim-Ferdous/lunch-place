from collections.abc import Sequence
from datetime import date, datetime

from sqlalchemy import Row, desc, insert, or_, select, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql.functions import count

import auth
import models
import schemas
from config import get_settings
from database import SessionLocal, engine
from models import Base


def create_root_user(db: Session) -> None:
    """
    Should run on startup. Create all tables and check if there is at least one admin. If not, create one.
    """
    Base.metadata.create_all(engine)

    if db.query(models.User).filter(models.User.role == models.Roles.ADMIN).count() > 0:
        return

    hashed_password = auth.pwd_context.hash(get_settings().ROOT_PASSWORD)

    db.add(
        models.User(
            username=get_settings().ROOT_USERNAME,
            password=hashed_password,
            email=get_settings().ROOT_EMAIL,
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


def get_items(
    db: Session,
    restaurant_id: int,
    day: models.Weekdays | None,
    all: bool = False,
) -> list[models.Item]:
    qry = db.query(models.Item).where(models.Item.restaurant_id == restaurant_id)
    if not all:
        sieve = (
            db.query(models.AssocItemDailyMenu.item_id)
            .join(models.Item)
            .where(models.Item.restaurant_id == restaurant_id)
        )

        if day is not None:
            items_filter = models.Item.id.in_(
                sieve.join(models.DailyMenu).where(models.DailyMenu.day == day)
            )
        else:
            items_filter = models.Item.id.not_in(sieve)

        qry = qry.where(items_filter)
    items = qry.all()
    return items


def add_items(
    db: Session,
    restaurant_id: int,
    days: list[models.Weekdays] | None,
    items: list[schemas.ItemCreate],
) -> list[models.Item]:
    new_items = [
        models.Item(**(i.model_dump() | {"restaurant_id": restaurant_id}))
        for i in items
    ]
    db.bulk_save_objects(new_items, return_defaults=True)
    if days:
        db.execute(
            insert(models.AssocItemDailyMenu).values(
                [
                    {
                        "item_id": i.id,
                        "daily_menu_id": select(models.DailyMenu.id).where(
                            models.DailyMenu.restaurant_id == restaurant_id,
                            models.DailyMenu.day == day,
                        ),
                    }
                    for i in new_items
                    for day in days
                ]
            )
        )
    db.commit()
    return new_items


def delete_items(db: Session, restaurant_id: int, ids: list[int]) -> int:
    db.query(models.AssocItemDailyMenu).where(
        models.AssocItemDailyMenu.item_id.in_(ids)
    ).delete()
    return (
        db.query(models.Item)
        .where(models.Item.restaurant_id == restaurant_id, models.Item.id.in_(ids))
        .delete()
    )


def add_item_to_daily_menu(
    db: Session, restaurant_id: int, days: list[models.Weekdays], ids: list[int]
) -> int:
    return db.execute(
        insert(models.AssocItemDailyMenu).values(
            [
                {
                    "item_id": i,
                    "daily_menu_id": select(models.DailyMenu.id).where(
                        models.DailyMenu.restaurant_id == restaurant_id,
                        models.DailyMenu.day == day,
                    ),
                }
                for i in ids
                for day in days
            ]
        )
    ).rowcount


def remove_item_from_daily_menu(
    db: Session, restaurant_id: int, days: list[models.Weekdays], ids: list[int]
) -> int:
    return (
        db.query(models.AssocItemDailyMenu)
        .where(
            models.AssocItemDailyMenu.item_id.in_(
                db.query(models.AssocItemDailyMenu.item_id)
                .join(models.Item)
                .where(models.AssocItemDailyMenu.item_id.in_(ids))
                .where(models.Item.restaurant_id == restaurant_id)
            )
        )
        .where(
            models.AssocItemDailyMenu.daily_menu_id.in_(
                db.query(models.AssocItemDailyMenu.daily_menu_id)
                .join(models.DailyMenu)
                .where(models.DailyMenu.day.in_(days)),
            )
        )
        .delete()
    )


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    db_user = models.User(**user.model_dump())
    db_user.password = auth.get_password_hash(user.password)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_voting_history_of_user(
    db: Session, user_id: int
) -> Sequence[Row[tuple[str, datetime]]]:
    return db.execute(
        select(models.Restaurant.name, models.Vote.created_at)
        .join(models.Vote)
        .where(models.Vote.user_id == user_id)
    ).all()


def vote(db: Session, user_id: int, restaurant_id: int) -> models.Vote:
    r = models.Vote(user_id=user_id, restaurant_id=restaurant_id)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def _compute_winner(db: Session, of_date: date) -> list[tuple[int, int]]:
    votes_desc_cte = (
        db.query(
            models.Vote.restaurant_id.label("restaurant_id"),
            count(models.Vote.restaurant_id).label(  # type:ignore[no-untyped-call]
                "n"
            ),
        )
        .where(models.Vote.voting_date == of_date)
        .group_by(models.Vote.restaurant_id)
        .order_by(desc(text("n")))
        .cte("votes_desc")
    )
    winners = (
        db.query(votes_desc_cte)
        .where(votes_desc_cte.c["n"].in_(db.query(votes_desc_cte.c["n"]).limit(1)))
        .all()
    )
    db.bulk_save_objects(
        [
            models.VoteWinner(restaurant_id=restaurant_id, votes=count)
            for restaurant_id, count in winners
        ]
    )
    db.commit()
    return winners


def compute_winner(
    session: sessionmaker[Session] | Session = SessionLocal,
    of_date: date = datetime.now().date(),
) -> list[tuple[int, int]]:
    if isinstance(session, Session):
        return _compute_winner(session, of_date)
    with session() as db:
        return _compute_winner(db, of_date)


def get_winners(
    db: Session, voting_day: date = datetime.today().date()
) -> list[models.VoteWinner]:
    return (
        db.query(models.VoteWinner)
        .where(models.VoteWinner.voting_date == voting_day)
        .all()
    )
