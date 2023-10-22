import enum
from typing import Optional

from sqlalchemy import VARCHAR, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


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
    name: Mapped[str] = mapped_column(VARCHAR(32), unique=True, nullable=False)
    price: Mapped[int]
    description: Mapped[str | None] = mapped_column(VARCHAR(255))

    restaurant_id = mapped_column(ForeignKey("restaurants.id"))


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(VARCHAR(32), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(VARCHAR(255))

    items = relationship(Item)


class RestaurantMenu(Base):
    __tablename__ = "restaurant_menus"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str | None] = mapped_column(VARCHAR(32))
    day: Mapped[Weekdays]


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(VARCHAR(32), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(VARCHAR(60))
    email: Mapped[str] = mapped_column(unique=True)
    role: Mapped[Roles]

    restaurant_id = mapped_column(ForeignKey("restaurants.id"))
