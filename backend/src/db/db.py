
from functools import lru_cache
from os import environ
import re
from urllib.parse import urlparse

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.engine.url import make_url
from sqlmodel import Session, create_engine, select

from src.models.master.apps import Apps, Urls

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
    if master == client:
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
    # 1. Validar la URL
    db_url = _validate_client_db_url(db_url)
    
    # 2. Usar make_url para desglosar la conexión de forma segura
    url_obj = make_url(db_url)
    
    # 3. Extraer las opciones del query string (?options=...)
    # url_obj.query es un diccionario con los parámetros de la URL
    extracted_options = url_obj.query.get("options")
    
    print(f"Creating new engine for client. Options found: {extracted_options}")

    # 4. Crear la URL "limpia" (sin los query params) para evitar duplicidad
    # Esto evita que el driver se confunda si pasamos la opción por dos lados
    clean_url = url_obj.set(query={})

    return create_engine(
        clean_url,
        # Aquí es donde realmente se pasan las opciones del search_path
        connect_args={"options": extracted_options} if extracted_options else {},
        echo=SQL_ECHO
    )

def _extract_tenant_host(request: Request) -> str:
    # Priority: explicit tenant header from SvelteKit actions, then forwarded/host fallback.
    raw_host = (
        request.headers.get("x-tenant-host")
        or request.headers.get("x-forwarded-host")
        or request.headers.get("host")
    )
    if not raw_host:
        raise ValueError("Tenant host header is required to determine client DB URL")
    return raw_host


_SCHEMA_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

def get_session_client(request: Request):
    """Return a dependency that yields tenant sessions resolved from master Apps by host."""
    client = get_client(request)
    engine_client = _get_client_engine(client.db_client)
    print(engine_client)

    with Session(engine_client) as session:
        #schema_name = get_schema_name_from_db_url(client.db_client)
        ## Scope all tenant queries in this session to the resolved schema.
        #session.exec(text(f'SET search_path TO "{schema_name}", public'))
        yield session


def get_client(request: Request) -> Apps:
    """Return the name of the client app based on the request host."""
    host = _extract_tenant_host(request)
    with Session(master_engine) as session:
        query = select(Apps, Urls.id_app).where(Urls.urls == host, Urls.id_app == Apps.id)
        result = session.exec(query).first()
        client = result[0] if result else None
        if client is None:
            raise LookupError("App not found in master DB for host: " + host)
        return client


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