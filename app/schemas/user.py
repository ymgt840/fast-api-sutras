from pydantic import EmailStr
from app.schemas.core import BaseSchema, PagingMeta

class UserBase(BaseSchema):
    full_name: str | None = None

class UserResponse(UserBase):
    id: str
    email: EmailStr
    email_verified: bool

    class Config:
        orm_mode = True

class UserCreate(UserBase):
    email : EmailStr
    password: str

class UserUpdate(UserBase):
    password: str | None = None

class UsersPagedResponse(BaseSchema):
    data: list[UserResponse] | None
    meta: PagingMeta | None