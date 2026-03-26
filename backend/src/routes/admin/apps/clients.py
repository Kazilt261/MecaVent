from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel, select

from src.db import get_master_session
from src.models.master.apps import Apps, Urls
from src.routes.types import UserData
from src.utils.jwt_depends import get_jwt_username


router = APIRouter(prefix="/admin/apps/clients", tags=["Admin Apps Clients"])


class ClientCreate(SQLModel):
	name_client: str
	db_client: str
	redis_client: str = "default"


class ClientUpdate(SQLModel):
	name_client: str | None = None
	db_client: str | None = None
	redis_client: str | None = None


class ClientUrlCreate(SQLModel):
	urls: str


class ClientUrlUpdate(SQLModel):
	urls: str


def _serialize_client(client: Apps) -> dict[str, str | int]:
	return {
		"id": client.id,
		"name_client": client.name_client,
		"db_client": client.db_client,
		"redis_client": client.redis_client,
	}


def _serialize_client_url(url: Urls) -> dict[str, str | int]:
	return {
		"id": url.id,
		"id_app": url.id_app,
		"urls": url.urls,
	}


@router.get("")
def list_clients(
	search: str | None = Query(default=None, description="Search by name_client, db_client or redis_client"),
	sort_by: Literal["id", "name_client", "db_client", "redis_client"] = Query(default="name_client"),
	sort_order: Literal["asc", "desc"] = Query(default="asc"),
	limit: int = Query(default=50, ge=1, le=200),
	offset: int = Query(default=0, ge=0),
	session=Depends(get_master_session),
	_: UserData = Depends(get_jwt_username),
):
	statement = select(Apps)
	count_statement = select(func.count()).select_from(Apps)

	if search:
		search_value = f"%{search.strip()}%"
		search_filter = or_(
			Apps.name_client.ilike(search_value),
			Apps.db_client.ilike(search_value),
			Apps.redis_client.ilike(search_value),
		)
		statement = statement.where(search_filter)
		count_statement = count_statement.where(search_filter)

	sort_columns = {
		"id": Apps.id,
		"name_client": Apps.name_client,
		"db_client": Apps.db_client,
		"redis_client": Apps.redis_client,
	}
	sort_column = sort_columns[sort_by]
	order_by_clause = sort_column.desc() if sort_order == "desc" else sort_column.asc()

	statement = statement.order_by(order_by_clause).offset(offset).limit(limit)
	clients = session.exec(statement).all()
	total = session.exec(count_statement).one()
	return {
		"clients": [_serialize_client(client) for client in clients],
		"meta": {
			"search": search,
			"sort_by": sort_by,
			"sort_order": sort_order,
			"limit": limit,
			"offset": offset,
			"total": total,
		},
	}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_client(
	payload: ClientCreate,
	session=Depends(get_master_session),
	_: UserData = Depends(get_jwt_username),
):
	name_client = payload.name_client.strip()
	db_client = payload.db_client.strip()
	redis_client = payload.redis_client.strip()

	if not name_client:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name_client is required")
	if not db_client:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="db_client is required")
	if not redis_client:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="redis_client is required")

	client = Apps(name_client=name_client, db_client=db_client, redis_client=redis_client)
	try:
		session.add(client)
		session.commit()
		session.refresh(client)
	except IntegrityError as exc:
		session.rollback()
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail="Client with this name already exists",
		) from exc

	return {"message": "Client created", "client": _serialize_client(client)}


@router.put("/{client_id}")
def update_client(
	client_id: int,
	payload: ClientUpdate,
	session=Depends(get_master_session),
	_: UserData = Depends(get_jwt_username),
):
	client = session.get(Apps, client_id)
	if not client:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

	if payload.name_client is not None:
		name_client = payload.name_client.strip()
		if not name_client:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name_client cannot be empty")
		client.name_client = name_client

	if payload.db_client is not None:
		db_client = payload.db_client.strip()
		if not db_client:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="db_client cannot be empty")
		client.db_client = db_client

	if payload.redis_client is not None:
		redis_client = payload.redis_client.strip()
		if not redis_client:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="redis_client cannot be empty")
		client.redis_client = redis_client

	try:
		session.add(client)
		session.commit()
		session.refresh(client)
	except IntegrityError as exc:
		session.rollback()
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail="Client with this name already exists",
		) from exc

	return {"message": "Client updated", "client": _serialize_client(client)}


@router.delete("/{client_id}")
def delete_client(
	client_id: int,
	session=Depends(get_master_session),
	_: UserData = Depends(get_jwt_username),
):
	client = session.get(Apps, client_id)
	if not client:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

	session.delete(client)
	session.commit()
	return {"message": "Client deleted", "id": client_id}


@router.get("/{client_id}/urls")
def list_client_urls(
	client_id: int,
	search: str | None = Query(default=None, description="Search by url value"),
	sort_by: Literal["id", "urls"] = Query(default="id"),
	sort_order: Literal["asc", "desc"] = Query(default="asc"),
	limit: int = Query(default=50, ge=1, le=200),
	offset: int = Query(default=0, ge=0),
	session=Depends(get_master_session),
	_: UserData = Depends(get_jwt_username),
):
	client = session.get(Apps, client_id)
	if not client:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

	statement = select(Urls).where(Urls.id_app == client_id)
	count_statement = select(func.count()).select_from(Urls).where(Urls.id_app == client_id)

	if search:
		search_value = f"%{search.strip()}%"
		search_filter = Urls.urls.ilike(search_value)
		statement = statement.where(search_filter)
		count_statement = count_statement.where(search_filter)

	sort_columns = {
		"id": Urls.id,
		"urls": Urls.urls,
	}
	sort_column = sort_columns[sort_by]
	order_by_clause = sort_column.desc() if sort_order == "desc" else sort_column.asc()

	statement = statement.order_by(order_by_clause).offset(offset).limit(limit)
	client_urls = session.exec(statement).all()
	total = session.exec(count_statement).one()
	return {
		"client": _serialize_client(client),
		"urls": [_serialize_client_url(url) for url in client_urls],
		"meta": {
			"search": search,
			"sort_by": sort_by,
			"sort_order": sort_order,
			"limit": limit,
			"offset": offset,
			"total": total,
		},
	}


@router.post("/{client_id}/urls", status_code=status.HTTP_201_CREATED)
def create_client_url(
	client_id: int,
	payload: ClientUrlCreate,
	session=Depends(get_master_session),
	_: UserData = Depends(get_jwt_username),
):
	client = session.get(Apps, client_id)
	if not client:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

	url_value = payload.urls.strip()
	if not url_value:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="urls is required")

	new_url = Urls(id_app=client_id, urls=url_value)
	session.add(new_url)
	session.commit()
	session.refresh(new_url)

	return {
		"message": "Client URL created",
		"client": _serialize_client(client),
		"url": _serialize_client_url(new_url),
	}


@router.put("/{client_id}/urls/{url_id}")
def update_client_url(
	client_id: int,
	url_id: int,
	payload: ClientUrlUpdate,
	session=Depends(get_master_session),
	_: UserData = Depends(get_jwt_username),
):
	client = session.get(Apps, client_id)
	if not client:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

	client_url = session.get(Urls, url_id)
	if not client_url or client_url.id_app != client_id:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client URL not found")

	url_value = payload.urls.strip()
	if not url_value:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="urls is required")

	client_url.urls = url_value
	session.add(client_url)
	session.commit()
	session.refresh(client_url)

	return {
		"message": "Client URL updated",
		"client": _serialize_client(client),
		"url": _serialize_client_url(client_url),
	}


@router.delete("/{client_id}/urls/{url_id}")
def delete_client_url(
	client_id: int,
	url_id: int,
	session=Depends(get_master_session),
	_: UserData = Depends(get_jwt_username),
):
	client = session.get(Apps, client_id)
	if not client:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

	client_url = session.get(Urls, url_id)
	if not client_url or client_url.id_app != client_id:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client URL not found")

	session.delete(client_url)
	session.commit()
	return {"message": "Client URL deleted", "id": url_id, "client_id": client_id}
