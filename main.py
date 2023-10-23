import logging
from collections.abc import AsyncGenerator, Callable, Generator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import (HTTPAuthorizationCredentials, HTTPBearer,
                              OAuth2PasswordRequestForm)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import auth
import crud
import models
import schemas
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Creates root user on startup, if not exists.
    We need to check if get_db has been overriden, since we will override it during tests.
    """
    dependency = get_db
    if get_db in app.dependency_overrides:
        dependency = app.dependency_overrides[get_db]

    logging.info("LIFESPAN")
    crud.create_root_user(next(dependency()))
    yield


app = FastAPI(lifespan=lifespan)
security = HTTPBearer()


def filter_by_role(role: models.Roles) -> Callable[..., None]:
    def role_only(
        creds: Annotated[HTTPAuthorizationCredentials, Depends(security)]
    ) -> None:
        d = auth.unpack_jwt(creds.credentials)
        if d.role != role:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail=f"Only an {role} can use this feature",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return role_only


admin_only = filter_by_role(models.Roles.ADMIN)
employee_only = filter_by_role(models.Roles.EMPLOYEE)
restaurateur_only = filter_by_role(models.Roles.RESTAURATEUR)


def get_role(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> Generator[models.Roles, None, None]:
    yield auth.unpack_jwt(creds.credentials).role


def get_restaurant_id(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> Generator[
    int | None, None, None
]:  # Here, ``None`` in yield type is unnecessary, as we will filter for resturateurs only.
    yield auth.unpack_jwt(creds.credentials).restaurant_id


# TODO: Logout (use a nonce in jwt?)
@app.post("/login", response_model=auth.Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> auth.Token:
    user = crud.get_user(db, username=form_data.username)
    if user is None or not auth.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    return auth.create_access_token(
        str(user.username), models.Roles(str(user.role)), user.restaurant_id
    )


@app.post(
    "/users/",
    response_model=schemas.UserBase,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(admin_only)],
)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)) -> models.User:
    u, e = crud.is_email_username_registered(
        db, username=user.username, email=user.email
    )
    d = []
    if u is True:
        d.append("Username")
    if e is True:
        d.append("Email")
    if u or e:
        raise HTTPException(
            status_code=409, detail=f"{' and '.join(d)} already registered"
        )
    try:
        new_user = crud.create_user(db=db, user=user)
        return new_user
    except IntegrityError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Restaurant does not exist.")


@app.post(
    "/restaurants/",
    response_model=schemas.Restaurant,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(admin_only)],
)
def create_restaurant(
    restaurant: schemas.RestaurantCreate, db: Session = Depends(get_db)
) -> models.Restaurant:
    return crud.create_restaurant(db, restaurant)


@app.get(
    "/menu/",
    response_model=list[schemas.Item],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(restaurateur_only)],
)
def get_menu(
    day: models.Weekdays | None = None,
    restaurant_id: int = Depends(get_restaurant_id),
    db: Session = Depends(get_db),
    all: bool = False,
) -> models.DailyMenu | list[models.Item]:
    return crud.get_items(db, restaurant_id, day, all)


@app.post(
    "/menu/",
    response_model=list[schemas.Item],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(restaurateur_only)],
)
def add_to_daily_menu(
    items: list[schemas.ItemCreate],
    day: models.Weekdays | None = None,
    restaurant_id: int = Depends(get_restaurant_id),
    db: Session = Depends(get_db),
) -> models.DailyMenu | list[models.Item]:
    return crud.add_items(
        db,
        restaurant_id,
        day,
        items,
    )
