from collections.abc import AsyncGenerator, Callable, Generator
from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import (HTTPAuthorizationCredentials, HTTPBearer,
                              OAuth2PasswordRequestForm)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql.compiler import schema

import auth
import crud
import models
import schemas
from config import get_settings
from database import get_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """
    Creates root user on startup.
    """
    crud.create_root_user(next(get_db()))
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


def get_user_id(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> Generator[int, None, None]:
    yield auth.unpack_jwt(creds.credentials).user_id


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
        user.id, str(user.username), models.Roles(str(user.role)), user.restaurant_id
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
) -> models.Restaurant | None:
    try:
        return crud.create_restaurant(db, restaurant)
    except IntegrityError as e:
        if (
            e.orig is not None
            and isinstance(e.orig.args[0], str)
            and e.orig.args[0].lower().count("unique")
        ):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Restaurant with this name already exists."
            )
        raise e


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
def add_menu(
    items: list[schemas.ItemCreate],
    day: models.Weekdays | None = None,
    restaurant_id: int = Depends(get_restaurant_id),
    db: Session = Depends(get_db),
) -> models.DailyMenu | list[models.Item]:
    return crud.add_items(db, restaurant_id, day, items)


@app.patch(
    "/menu/",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(restaurateur_only)],
)
def patch_menu(
    patch: schemas.PatchMenu,
    restaurant_id: int = Depends(get_restaurant_id),
    db: Session = Depends(get_db),
) -> None:
    if patch.day is not None:
        if patch.op == schemas.PatchMenuOp.ADD:
            crud.add_item_to_daily_menu(db, restaurant_id, patch.day, patch.ids)
        elif patch.op == schemas.PatchMenuOp.REMOVE:
            crud.remove_item_from_daily_menu(db, restaurant_id, patch.day, patch.ids)
    else:  # We are sure this is delete, because of schemas.PatchMenu's validator.
        crud.delete_items(db, restaurant_id, patch.ids)


@app.get(
    "/vote",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(employee_only)],
)
def get_votes(
    employee_id: int = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> list[schemas.EmployeeVoteHistory]:
    return [
        schemas.EmployeeVoteHistory(restaurant=r[0], voted_at=r[1])
        for r in crud.get_voting_history_of_user(db, employee_id)
    ]


@app.get(
    "/vote/winners",
    status_code=status.HTTP_200_OK,
    response_model=list[schemas.VoteWinner],
    dependencies=[Depends(employee_only)],
)
def get_winners(
    of_day: date = datetime.today().date(),
    db: Session = Depends(get_db),
) -> list[schemas.VoteWinner]:
    return [
        schemas.VoteWinner(
            votes=i.votes, voting_date=i.voting_date, restaurant=i.restaurant.name
        )
        for i in crud.get_winners(db, of_day)
    ]


@app.post(
    "/vote/{restaurant_id}",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(employee_only)],
)
def vote(
    restaurant_id: int,
    employee_id: int = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> None:
    if (
        datetime.now()
        + get_settings().VOTING_END_TIME_MARGIN  # Stop voting a few seconds early
    ).time() > get_settings().VOTING_ENDS_AT:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Voting time has ended, try again tomorrow."
        )

    try:
        crud.vote(db, employee_id, restaurant_id)
    except IntegrityError as e:
        if e.orig is not None and isinstance(e.orig.args[0], str):
            err = e.orig.args[0].lower()
            if err.count("foreign key"):
                raise HTTPException(status.HTTP_404_NOT_FOUND, "No such restaurant.")
            elif err.count("unique"):
                raise HTTPException(
                    status.HTTP_409_CONFLICT, "You can vote only once per day."
                )
            else:
                raise e
