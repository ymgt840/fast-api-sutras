from fastapi import APIRouter, Depends, Security
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, models, schemas
from app.core.auth import get_current_user
from app.core.database import get_async_db
from app.exceptions.core import APIException
from app.exceptions.error_message import ErrorMessage
router = APIRouter()

@router.get("/me")
async def get_user_me(current_user: models.User = Depends(get_current_user)) -> schemas.UserResponse:
    """ログインユーザを取得する"""
    return current_user

@router.get(
    "/{id}",
    dependencies=[Security(get_current_user, scopes=["admin"])],
)
async def get_user(id: str, db: AsyncSession = Depends(get_async_db)) -> schemas.UserResponse:
    """id からユーザを取得する"""
    user = await crud.user.get_db_obj_by_id(db, id=id)
    if not user:
        raise APIException(ErrorMessage.ID_NOT_FOUND)
    return user

@router.post("")
async def create_user(data_in: schemas.UserCreate, db: AsyncSession = Depends(get_async_db)) -> schemas.UserResponse:
    """user 新規登録"""
    user = await crud.user.get_by_mail(db, email=data_in.email)
    # メールアドレス重複登録はNGとする
    if user:
        raise APIException(ErrorMessage.ALREADY_REGISTERED_EMAIL)
    return await crud.user.create()

@router.put(
    "/{id}",
    dependencies=[Security(get_current_user, scopes=["admin"])]
)
async def update_user(
    id: str,
    data_in: schemas.UserUpdate,
    db: AsyncSession = Depends(get_async_db)
) -> schemas.UserResponse:
    user = await crud.user.get_db_obj_by_id(db, id=id)
    if not user:
        raise APIException(ErrorMessage.ID_NOT_FOUND)
    return await crud.user.update(db, db_obj=user, obj_in=data_in)