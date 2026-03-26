import json
from os import environ
from time import time
from typing_extensions import Annotated

from fastapi.params import Form, Query

from src.db.db import get_master_session
from src.utils.jwt_depends import get_jwt_username
from src.models.master.users import UserMasterApp
from .forms import LoginForm, RefreshTokenForm
from src.db import get_session, redis_client
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from src.routes.types import UserData
import jwt

router = APIRouter(prefix="/admin/auth", tags=["Admin Auth"])


@router.post("/login")
async def login(user: LoginForm, session=Depends(get_master_session)):
    cache_key = f"user:{user.username}"
    print(f"Attempting login for {user.username}")  # Debug log para verificar el intento de login
    cached_user = redis_client.get(cache_key)

    if cached_user:
        # 1. Evitamos eval() usando json.loads para seguridad
        user_data = json.loads(cached_user)
        db_result = UserData.interface(user_data)
        if not db_result or not UserMasterApp.verify_password(user.password, db_result.hashed_password):
            print(f"Login failed for {user.username}. Paswword")  # Debug log para intentos fallidos
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid username or password (from cache)"
            )
    else:
        # 2. Proyección limpia: solo pedimos lo necesario a la DB
        statement = select(UserMasterApp.id, UserMasterApp.username, UserMasterApp.hashed_password).where(UserMasterApp.username == user.username)
        db_result = UserData.interface(session.exec(statement).mappings().first())

        # 3. Validación: Si no existe el usuario o la clave falla
        if not db_result or not UserMasterApp.verify_password(user.password, db_result.hashed_password):
            print(f"Login failed for {user.username}. Paswword")  # Debug log para intentos fallidos
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid username or password"
            )

        # 5. Guardamos en Redis como JSON (más estándar que un string de objeto)
        redis_client.set(cache_key, db_result.model_dump_json(), 3600)

    jwt, reset_jwt = UserMasterApp.generate_jwt(db_result.username, db_result.hashed_password)
    redis_client.set(f"jwt:{db_result.username}", reset_jwt, 3600*24)  # Guardamos el JWT en Redis con expiración
    print(f"Generated JWT for {db_result.username}: {reset_jwt}")  # Debug log para verificar el JWT generado

    return {"message": "Login successful", "user_data": {
        "id": db_result.id,
        "username": db_result.username,
        "jwt": jwt,
        "reset_jwt": reset_jwt
    }}

@router.post("/change-password")
async def change_password(
    previous_password: Annotated[str, Form()],
    new_password: Annotated[str, Form()],
    session=Depends(get_master_session),
    user: UserData = Depends(get_jwt_username),
):
    validation_error = UserMasterApp.validate_password(new_password)
    if validation_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_error,
        )

    statement = select(UserMasterApp).where(UserMasterApp.username == user.username)
    user_db = session.exec(statement).first()
    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not UserMasterApp.verify_password(previous_password, user_db.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Previous password is incorrect",
        )

    user_db.hashed_password = UserMasterApp.hash_password(new_password)
    session.add(user_db)
    session.commit()
    session.refresh(user_db)

    new_jwt, new_reset_jwt = UserMasterApp.generate_jwt(user_db.username, user_db.hashed_password)
    user_data = UserData.interface(
        {
            "id": user_db.id,
            "username": user_db.username,
            "hashed_password": user_db.hashed_password,
        }
    )
    redis_client.set(f"user:{user_db.username}", user_data.model_dump_json(), 3600)
    redis_client.set(f"jwt:{user_db.username}", new_reset_jwt, 3600 * 24)

    return {
        "message": "Password changed successfully",
        "user_data": {
            "id": user_db.id,
            "username": user_db.username,
            "jwt": new_jwt,
            "reset_jwt": new_reset_jwt
        },
    }

@router.post("/logout")
async def logout(user: UserData = Depends(get_jwt_username)):
    redis_client.delete(f"jwt:{user.username}")
    return {"message": "Logout successful"}

@router.get("")
def get_user(user: UserData = Depends(get_jwt_username)):
    """
    Endpoint that return the user data from the database, if the user exist, otherwise return a 404 error.
    """
    return {"id": user.id, "username": user.username, "email": user.email}



@router.post("/refresh")
def refresh_token(data: RefreshTokenForm, session=Depends(get_master_session)):
    """
    Endpoint that return a new JWT token for the user, if the user exist, otherwise return a 404 error.
    """
    refresh_token = data.refresh_token
    secret_key = environ.get("JWT_SECRET_KEY", "your_secret_key")
    print("Received refresh token:", refresh_token)  # Debug log para verificar el token recibido

    try:
        payload = jwt.decode(refresh_token, secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from exc

    if payload.get("token_type") not in (None, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type for refresh",
        )

    username = payload.get("username")
    hash_password = payload.get("hash_password")
    if not isinstance(username, str) or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload",
        )

    stored_refresh = redis_client.get(f"jwt:{username}")
    if not stored_refresh:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is not active",
        )

    stored_refresh_str = (
        stored_refresh.decode("utf-8")
        if isinstance(stored_refresh, (bytes, bytearray))
        else str(stored_refresh)
    )
    print("Stored refresh token:", stored_refresh_str)  # Debug log para verificar el token almacenado
    if stored_refresh_str != refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token mismatch",
        )
    user_data = redis_client.get(f"user:{username}")
    if not user_data:
        statement = select(UserMasterApp.id, UserMasterApp.username, UserMasterApp.hashed_password).where(UserMasterApp.username == username)
        user_data = UserData.interface(session.exec(statement).mappings().first())
    else:
        user_data = json.loads(user_data) if isinstance(user_data, str) else json.loads(user_data.decode("utf-8"))
        user_data = UserData.interface(user_data)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user_data.hashed_password != hash_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is no longer valid",
        )

    new_jwt, new_reset_jwt = UserMasterApp.generate_jwt(user_data.username, user_data.hashed_password)
    redis_client.set(f"jwt:{user_data.username}", new_reset_jwt, 3600 * 24)
    redis_client.set(f"user:{user_data.username}", user_data.model_dump_json(), 3600)

    return {
        "message": "Token refreshed",
        "user_data": {
            "id": user_data.id,
            "username": user_data.username,
            "jwt": new_jwt,
            "reset_jwt": new_reset_jwt,
        },
    }

@router.post("/generate-token-reset-password")
async def generate_token_reset_password(username: Annotated[str, Form()], session=Depends(get_master_session)):
    """
    Endpoint that generate a token that you can use to reset the password of the user, if the user exist, otherwise return a 404 error.
    """
    statement = select(UserMasterApp.id, UserMasterApp.username, UserMasterApp.hashed_password).where(UserMasterApp.username == username)
    user_data = UserData.interface(session.exec(statement).mappings().first())

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    secret_key = environ.get("JWT_SECRET_KEY", "your_secret_key")
    token_payload = {
        "username": user_data.username,
        "hash_password": user_data.hashed_password,
        "token_type": "reset_password",
        "exp": int(time()) + 900,
    }
    token = jwt.encode(token_payload, secret_key, algorithm="HS256")
    redis_client.set(f"reset-password:{user_data.username}", token, 900)

    return {
        "message": "Password reset token generated",
        "username": user_data.username,
        "token": token,
        "expires_in_seconds": 900,
    }

@router.post("/reset-password")
async def reset_password(token: Annotated[str, Form()], new_password: Annotated[str, Form()], session=Depends(get_master_session)):
    """
    Endpoint that reset the password of the user, if the token is valid, otherwise return a 401 error.
    """
    secret_key = environ.get("JWT_SECRET_KEY", "your_secret_key")

    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Reset token expired",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid reset token",
        ) from exc

    if payload.get("token_type") not in (None, "reset_password"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type for password reset",
        )

    username = payload.get("username")
    old_hash_password = payload.get("hash_password")
    if not isinstance(username, str) or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid reset token payload",
        )

    stored_token = redis_client.get(f"reset-password:{username}")
    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Reset token is not active",
        )

    stored_token_str = (
        stored_token.decode("utf-8")
        if isinstance(stored_token, (bytes, bytearray))
        else str(stored_token)
    )
    if stored_token_str != token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Reset token mismatch",
        )

    statement = select(UserMasterApp).where(UserMasterApp.username == username)
    user_db = session.exec(statement).first()
    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user_db.hashed_password != old_hash_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Reset token is no longer valid",
        )

    user_db.hashed_password = UserMasterApp.hash_password(new_password)
    session.add(user_db)
    session.commit()
    session.refresh(user_db)

    new_jwt, new_reset_jwt = UserMasterApp.generate_jwt(user_db.username, user_db.hashed_password)
    user_data = UserData.interface(
        {
            "id": user_db.id,
            "username": user_db.username,
            "hashed_password": user_db.hashed_password,
        }
    )
    redis_client.set(f"user:{user_db.username}", user_data.model_dump_json(), 3600)
    redis_client.set(f"jwt:{user_db.username}", new_reset_jwt, 3600 * 24)
    redis_client.delete(f"reset-password:{user_db.username}")

    return {
        "message": "Password reset successful",
        "user_data": {
            "id": user_db.id,
            "username": user_db.username,
            "jwt": new_jwt,
            "reset_jwt": new_reset_jwt,
        },
    }

@router.get("/reset-password")
async def verify_token_reset_password(token: Annotated[str, Query(...)], session=Depends(get_master_session)):
    """
    Endpoint that verify if the token is valid, if the token is valid return the user data, otherwise return a 401 error.
    """
    secret_key = environ.get("JWT_SECRET_KEY", "your_secret_key")

    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Reset token expired",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid reset token",
        ) from exc

    if payload.get("token_type") not in (None, "reset_password"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type for password reset",
        )

    username = payload.get("username")
    hash_password = payload.get("hash_password")
    if not isinstance(username, str) or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid reset token payload",
        )

    stored_token = redis_client.get(f"reset-password:{username}")
    stored_token_str = (
        stored_token.decode("utf-8")
        if isinstance(stored_token, (bytes, bytearray))
        else str(stored_token)
    ) if stored_token else None
    is_active = stored_token_str == token

    statement = select(UserMasterApp.id, UserMasterApp.username, UserMasterApp.hashed_password).where(UserMasterApp.username == username)
    user_data = UserData.interface(session.exec(statement).mappings().first())
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user_data.hashed_password != hash_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Reset token is no longer valid",
        )

    return {
        "message": "Reset token is valid",
        "is_active": is_active,
        "user_data": {
            "id": user_data.id,
            "username": user_data.username,
        },
    }
