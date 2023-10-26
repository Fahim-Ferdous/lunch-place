import enum
from datetime import date, datetime

from sqlalchemy import VARCHAR, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import current_date, now


class Base(DeclarativeBase):
    pass


class Weekdays(enum.StrEnum):
    SUNDAY = enum.auto()
    SATURDAY = enum.auto()
    MONDAY = enum.auto()
    TUESDAY = enum.auto()
    WEDNESDAY = enum.auto()
    THURSDAY = enum.auto()
    FRIDAY = enum.auto()


class Roles(enum.StrEnum):
    ADMIN = enum.auto()
    EMPLOYEE = enum.auto()
    RESTAURATEUR = enum.auto()


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        VARCHAR(32), unique=True, nullable=False
    )  # TODO: Uniqueness should be compunded with id.
    price: Mapped[int]
    description: Mapped[str | None] = mapped_column(VARCHAR(255))

    restaurant_id = mapped_column(ForeignKey("restaurants.id"))


class DailyMenu(Base):
    __tablename__ = "daily_menus"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str | None] = mapped_column(VARCHAR(32))
    day: Mapped[Weekdays]

    restaurant_id = mapped_column(ForeignKey("restaurants.id"))
    items: Mapped[list["AssocItemDailyMenu"]] = relationship()


class AssocItemDailyMenu(Base):
    __tablename__ = "items_daily_menus"

    item_id = mapped_column(ForeignKey("items.id"), primary_key=True)
    daily_menu_id = mapped_column(ForeignKey("daily_menus.id"), primary_key=True)


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(VARCHAR(32), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(VARCHAR(255))

    items = relationship(Item)
    daily_menus = relationship(DailyMenu)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(VARCHAR(32), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(VARCHAR(60))
    email: Mapped[str] = mapped_column(unique=True)
    role: Mapped[Roles]

    restaurant_id = mapped_column(ForeignKey("restaurants.id"))


class Vote(Base):
    __tablename__ = "votes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id = mapped_column(ForeignKey(User.id), nullable=False)
    restaurant_id = mapped_column(ForeignKey(Restaurant.id), nullable=False)

    voting_date: Mapped[date] = mapped_column(
        server_default=current_date(), index=True  # type: ignore[no-untyped-call]
    )
    created_at: Mapped[datetime] = mapped_column(server_default=now())  # type: ignore[no-untyped-call]

    __table_args__ = (UniqueConstraint("user_id", "voting_date"),)
    # TODO: No employee can vote twice.
    # TODO: After vote ends:
    # 1. compute winner
    # 2. archive to separate table
    # 3. select candidates for the next day (exclude candidate
    #    they won yesterday and the day before that).


class VoteWinner(Base):
    __tablename__ = "vote_winners"

    id: Mapped[int] = mapped_column(primary_key=True)
    votes: Mapped[int]
    restaurant_id = mapped_column(ForeignKey(Restaurant.id), nullable=False)
    restaurant = relationship(Restaurant)

    voting_date: Mapped[date] = mapped_column(
        server_default=current_date(), index=True  # type: ignore[no-untyped-call]
    )
    created_at: Mapped[datetime] = mapped_column(server_default=now())  # type: ignore[no-untyped-call]

    __table_args__ = (
        UniqueConstraint("restaurant_id", "voting_date"),
    )  # In case celery worker runs twice...
