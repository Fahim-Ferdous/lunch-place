from string import ascii_letters, digits

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from models import Roles

valid_username_chars = set(ascii_letters + digits + "-_")


class Item(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = Field(max_length=32)
    price: int = Field(gt=0, lt=10e5)
    description: str | None = Field(max_length=255)

    hide: bool = Field(False)


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str = Field(max_length=32, min_length=3)
    email: EmailStr
    role: Roles


class UserCreate(UserBase):
    model_config = ConfigDict(from_attributes=True)

    password: str

    @field_validator("username")
    @classmethod
    def check_username(cls, v: str):
        assert not any(
            i for i in v if i not in valid_username_chars
        ), "Username can only contain alphanumeric characters, underscores, ands hyphens"
        return v


class User(UserBase):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
