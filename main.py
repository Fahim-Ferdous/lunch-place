from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import (HTTPAuthorizationCredentials, HTTPBearer,
                              OAuth2PasswordRequestForm)
from sqlalchemy.orm import Session

import auth
import crud
import models
import schemas
from config import settings
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # create root user.
    crud.create_root_user(db=next(get_db()))
    yield


app = FastAPI(lifespan=lifespan)
security = HTTPBearer()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def admin_only(creds: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    d = auth.unpack_jwt(creds.credentials)
    if d.role != models.Roles.ADMIN:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Only an admin can use this feature",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.post("/login", response_model=auth.Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    user = crud.get_user(db, username=form_data.username)
    if user is None or not auth.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token_expires = timedelta(seconds=settings.JWT_TTL_SECONDS)
    access_token = auth.create_access_token(
        data={"role": user.role, "sub": user.username},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token}


@app.post("/users/", response_model=schemas.User, dependencies=[Depends(admin_only)])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
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
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/items/", response_model=list[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items
