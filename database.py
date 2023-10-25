from collections.abc import Generator
from sqlite3 import Connection as SqliteConnection

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry

from config import get_settings

engine = create_engine(
    get_settings().SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(
    dbapi_connection: DBAPIConnection, _: ConnectionPoolEntry
) -> None:
    if isinstance(dbapi_connection, SqliteConnection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Dependency function for db parameter to handler functions.
def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
        session.commit()
