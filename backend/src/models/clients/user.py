import hashlib
from os import environ
from time import time
from typing import List, Optional

import jwt

from src.models.db_declarations import AppMetadata
from sqlmodel import JSON, Column, Field

class User(AppMetadata, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    admin: bool = False
    username: str = Field(index=True, unique=True)
    email: Optional[str] = Field(default=None, index=True, unique=True)
    hashed_password: str

    @staticmethod
    def hash_password(password: str):
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return User.hash_password(plain_password) == hashed_password
    
    @staticmethod
    def generate_jwt(username: str, hash_password:str) -> tuple[str, str]:
        secret_key = environ.get("JWT_SECRET_KEY", "your_secret_key")
        token_payload = {
            "username": username,
            "hash_password": hash_password,
            "token_type": "access",
            "exp": int(time()) + 3600,
        }
        token = jwt.encode(token_payload, secret_key, algorithm="HS256")

        reset_payload = {
            "username": username,
            "hash_password": hash_password,
            "token_type": "refresh",
            "exp": int(time()) + 3600 * 24,
        }
        reset_token = jwt.encode(reset_payload, secret_key, algorithm="HS256")
        return token, reset_token
    
    @staticmethod
    def validate_password(password: str) -> str|None:
        if not password:
            return "Password is required"
        if len(password) < 6:
            return "Password must be at least 6 characters long"
        if not any(char.isdigit() for char in password):
            return "Password must contain at least one digit"
        if not any(char.isalpha() for char in password):
            return "Password must contain at least one letter"
        return None
    
    def validate(self) -> str|None:
        if not self.username:
            return "Username is required"
        if len(self.username) < 6:
            return "Username must be at least 6 characters long"
        if not self.hashed_password:
            return "Password is required"
        if self.email:
            if "@" not in self.email or "." not in self.email:
                return "Invalid email format"
        return None
    
class Roles(AppMetadata, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, foreign_key="user.id")
    permisions: List[str] = Field(sa_column=Column(JSON))
