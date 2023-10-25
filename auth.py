from datetime import datetime, timedelta

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError

from config import get_settings
from models import Roles


class Token(BaseModel):
    access_token: str


class TokenData(BaseModel):
    user_id: int
    username: str
    role: Roles
    restaurant_id: int | None = None


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def encode_jwt(
    data: dict[str, datetime | str | int | None], expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, get_settings().JWT_SECRET_KEY, algorithm=get_settings().JWT_ALGORITHM
    )
    return encoded_jwt


def create_access_token(
    user_id: int, username: str, role: Roles, restaurant_id: int | None = None
) -> Token:
    access_token_expires = timedelta(seconds=get_settings().JWT_TTL_SECONDS)
    access_token = encode_jwt(
        data=TokenData(
            user_id=user_id, username=username, role=role, restaurant_id=restaurant_id
        ).model_dump(),
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token)


def unpack_jwt(token: str) -> TokenData:
    invalid_creds_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            get_settings().JWT_SECRET_KEY,
            algorithms=[get_settings().JWT_ALGORITHM],
        )
        token_data = TokenData(**payload)
        try:
            TokenData.model_validate(token_data)
        except ValidationError:
            raise invalid_creds_exc
    except JWTError:
        raise invalid_creds_exc

    return token_data
