from string import ascii_letters, digits

from pydantic import BaseModel, EmailStr, Field, field_validator, validator

from models import Roles

valid_username_chars = set(ascii_letters + digits + "-_")


class Item(BaseModel):
    id: int
    name: str = Field(max_length=32)
    price: int = Field(gt=0, lt=10e5)
    description: str | None = Field(max_length=255)

    hide: bool = Field(False)

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    username: str = Field(max_length=32, min_length=3)
    email: EmailStr
    role: Roles


class UserCreate(UserBase):
    password: str

    @field_validator("username")
    @classmethod
    def check_username(cls, v: str):
        assert not any(
            i for i in v if i not in valid_username_chars
        ), "Username can only contain alphanumeric characters, underscores, ands hyphens"
        return v


class User(UserBase):
    id: int

    class Config:
        from_attributes = True
        use_enum_values = True
