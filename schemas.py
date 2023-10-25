import enum
from datetime import date, datetime
from string import ascii_letters, digits

from pydantic import (BaseModel, ConfigDict, EmailStr, Field, field_validator,
                      model_validator)

from models import Roles, Weekdays

valid_username_chars = set(ascii_letters + digits + "-_")


class ItemCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(max_length=32)
    price: int = Field(gt=0, lt=10e5)
    description: str | None = Field(default=None, max_length=255)


class Item(ItemCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class PatchMenuOp(enum.StrEnum):
    ADD = enum.auto()  # Add the already existing items to some day's menu.
    REMOVE = enum.auto()  # Remove from some day's menu, but don't delete.
    DELETE = enum.auto()  # Delete the items entirely.


class PatchMenu(BaseModel):
    op: PatchMenuOp
    day: Weekdays | None = None
    ids: list[int]

    @model_validator(mode="after")
    def check_day(self) -> "PatchMenu":
        if self.op != PatchMenuOp.DELETE and self.day is None:
            raise ValueError("Must include day")
        elif self.op == PatchMenuOp.DELETE and self.day is not None:
            raise ValueError("day is redundant for delete")
        return self


class DailyMenuCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str | None = Field(default=None, max_length=32)
    day: Weekdays
    items: list[Item]


class DailyMenu(DailyMenuCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class RestaurantBase(BaseModel):
    name: str = Field(max_length=32)
    description: str | None = Field(default=None, max_length=255)


class Restaurant(RestaurantBase):
    id: int

    items: list[Item] = []
    daily_menus: list[DailyMenu] = []


class RestaurantCreate(RestaurantBase):
    pass


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str = Field(max_length=32, min_length=3)
    email: EmailStr
    role: Roles


class UserCreate(UserBase):
    model_config = ConfigDict(from_attributes=True)

    password: str
    restaurant_id: int | None = None

    @model_validator(mode="after")
    def check_restaurant_id(self) -> "UserCreate":
        if self.role == Roles.RESTAURATEUR and self.restaurant_id is None:
            raise ValueError("restaurant_id is required for creating restaurateurs")
        return self

    @field_validator("username")
    @classmethod
    def check_username(cls, v: str) -> str:
        assert not any(
            i for i in v if i not in valid_username_chars
        ), "Username can only contain alphanumeric characters, underscores, ands hyphens"
        return v


class EmployeeVoteHistory(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    voted_at: datetime
    restaurant: str
