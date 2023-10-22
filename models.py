import enum

from sqlalchemy import (VARCHAR, Boolean, Column, Enum, ForeignKey, Integer,
                        String)
from sqlalchemy.orm import DeclarativeBase, relationship


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


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(VARCHAR(32), unique=True, nullable=False)
    description = Column(VARCHAR(255))

    items = relationship("Item")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(VARCHAR(32), unique=True, nullable=False)
    price = Column(Integer, nullable=False)
    description = Column(VARCHAR(255))

    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))


class RestaurantMenu(Base):
    __tablename__ = "restaurant_menus"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(VARCHAR(32))
    day = Column(Enum(Weekdays))


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(VARCHAR(32), unique=True, nullable=False)
    password = Column(VARCHAR(60))
    email = Column(String, unique=True, index=True)
    role = Column(Enum(Roles), nullable=False)

    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
