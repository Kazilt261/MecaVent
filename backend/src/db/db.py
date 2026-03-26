
from functools import lru_cache
from os import environ

from sqlalchemy.engine.url import make_url
from sqlmodel import Session, create_engine, select

from src.models.master.apps import Apps

DATABASE_URL_MASTER = environ.get("URL_DB", "sqlite:///./test.db")
SQL_ECHO = environ.get("SQL_ECHO", "true").lower() == "true"

# Backward compatibility: existing imports expect `engine` to be available.
master_engine = create_engine(DATABASE_URL_MASTER, echo=SQL_ECHO, future=True)
engine = master_engine


def _validate_client_db_url(db_url: str) -> str:
    """Ensure client URL does not resolve to master DB."""
    if not db_url:
        raise ValueError("Client DB URL is required")

    if db_url == DATABASE_URL_MASTER:
        raise ValueError("Client DB URL cannot be the same as master DB URL")

    master = make_url(DATABASE_URL_MASTER)
    client = make_url(db_url)

    # Defensive check: same backend/host/port/database should never be used for tenant data.
    same_db = (
        master.get_backend_name() == client.get_backend_name()
        and master.host == client.host
        and master.port == client.port
        and master.database == client.database
    )
    if same_db:
        raise ValueError("Client DB resolves to master database; configure a different database")

    return db_url


def get_session():
    """Default session used by current routes (master DB)."""
    with Session(master_engine) as session:
        yield session


def get_master_session():
    with Session(master_engine) as session:
        yield session


@lru_cache(maxsize=128)
def _get_client_engine(db_url: str):
    db_url = _validate_client_db_url(db_url)
    return create_engine(db_url, echo=SQL_ECHO, future=True)


def get_session_client(db_name: str):
    """Return a dependency that yields sessions for the provided client DB URL."""
    db_name = _validate_client_db_url(db_name)

    def _get_session_client():
        engine_client = _get_client_engine(db_name)
        with Session(engine_client) as session:
            yield session

    return _get_session_client


def get_client_db_url(*, app_id: int | None = None, app_name: str | None = None) -> str:
    if app_id is None and app_name is None:
        raise ValueError("You must provide app_id or app_name")

    with Session(master_engine) as session:
        query = select(Apps)
        if app_id is not None:
            query = query.where(Apps.id == app_id)
        else:
            query = query.where(Apps.name_client == app_name)

        app = session.exec(query).first()
        if app is None:
            raise LookupError("App not found in master DB")
        if not app.db_client:
            raise ValueError("App has no DB URL configured")
        return _validate_client_db_url(app.db_client)


def get_session_client_by_app(*, app_id: int | None = None, app_name: str | None = None):
    """Return a dependency that resolves client DB URL from master Apps table."""
    db_url = get_client_db_url(app_id=app_id, app_name=app_name)
    return get_session_client(db_url)