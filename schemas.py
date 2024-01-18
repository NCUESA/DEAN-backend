from pydantic import BaseModel


class RegisterSchema(BaseModel):
    username: str
    password: str


class LoginSchema(BaseModel):
    username: str
    password: str


class RefreshSchema(BaseModel):
    refresh_token: str


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str


class BaseSchema(BaseModel):
    id: int


class UserSchema(BaseSchema):
    username: str