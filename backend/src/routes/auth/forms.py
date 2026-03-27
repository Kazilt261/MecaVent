from pydantic import BaseModel

class LoginForm(BaseModel):
    username: str
    password: str

class RefreshTokenForm(BaseModel):
    refresh_token: str