from os import environ
from time import time
from typing import Annotated, Any
import json

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.models.master.users import UserMasterApp
from src.db import redis_master, engine
from src.routes.types import UserData

from sqlmodel import Session, select


bearer_scheme = HTTPBearer(auto_error=False)

def get_jwt_payload_from_header(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)] = None,
) -> dict[str, Any]:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Bearer token",
        )

    secret_key = environ.get("JWT_SECRET_KEY", "your_secret_key")

    try:
        payload = jwt.decode(credentials.credentials, secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT expired",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid JWT",
        ) from exc

    return payload


def get_jwt_username(
	payload: Annotated[dict[str, Any], Depends(get_jwt_payload_from_header)],
) -> UserData:
	username = payload.get("username")
	hash_password = payload.get("hash_password")
	exp = payload.get("exp")
	if not exp or exp < int(time()):
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="JWT expired",
		)

	if not isinstance(username, str) or not username:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid JWT: missing username",
		)

	user = redis_master.get(f"user:{username}")
	if user:
		cached = json.loads(user) if isinstance(user, str) else json.loads(user.decode("utf-8"))
		user_data = UserData.interface(cached)
		if user_data and user_data.hashed_password == hash_password:
			return user_data

	statement = select(UserMasterApp).where(UserMasterApp.username == username)
	with Session(engine) as session:
		user_db = session.exec(statement).first()

	if not user_db:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid JWT: user not found",
		)

	if user_db.hashed_password != hash_password:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid JWT: password mismatch",
		)

	user_data = UserData.interface(
		{
			"id": user_db.id,
			"username": user_db.username,
			"email": user_db.email,
			"hashed_password": user_db.hashed_password,
		}
	)
	redis_master.set(f"user:{username}", user_data.model_dump_json(), 3600)
	return user_data