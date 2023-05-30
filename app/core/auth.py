from datetime import datetime, timedelta, timezone
from typing import Any
# fastapi
from fastapi import Depends, status
from fastapi, security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt
from jose.exceptions import JWTError
from passlib.context import CryptContext
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
# app
from app import crud_v2, models, schemas
from app.exceptions.core import APIException
from app.exceptions.error_message import ErrorMessage
# config系
from .config import settings
from .database import get_async_db
from .logger import get_logger

# 認証設定
pwd_context     = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM       = "HS256"
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_GATEWAY_STAGE_PATH}/auth/login",
    auto_error=False,
)

def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """jwtエンコードしたアクセストークンを生成する"""
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    if expires_delta:
        expire = datetime.now(tz=timezone.utc) + expires_delta

    to_encode   = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワードバリデーションを実行する"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """パスワードをハッシュ化して返却する"""
    return pwd_context.hash(password)

async def get_current_user(
        security_scopes: SecurityScopes,
        db: AsyncSession = Depens(get_async_db),
        token: str = Depends(reusable_oauth2),
) -> models.User:
    """現在のユーザーを取得する"""
    if not token:
        raise APIException(ErrorMessage.CouldNotValidateCredentials)

    # jwt をデコードしてデータを取得する
    try:
        payload    = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = schemas.TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise APIException(
            ErrorMessage.CouldNotValidateCredentials
        ) from None

    # ユーザーを取得する
    user = await crud_v2.user.get_db_obj_by_id(db, id=token_data.sub)
    if not user:
        raise APIException(ErrorMessage.NOT_FOUND("USER"))
    user_scope = user.scopes.split(",") if user.scopes else []
    # セキュリティ範囲外の場合は失敗
    for scope in security_scopes.scopes:
        if scope not in user_scope:
            raise APIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                error=ErrorMessage.PERMISSION_ERROR,
            )

    return user