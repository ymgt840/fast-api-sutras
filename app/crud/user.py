from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select
from app import models, schemas
from app.core.auth import get_password_hash, verify_password
from app.crud.base import CRUDBase

class CRUDUser(
    CRUDBase[
        models.User,
        schemas.UserResponse,
        schemas.UserCreate,
        schemas.UserUpdate,
        schemas.UsersPagedResponse,
    ]
):
    async def get_by_mail(self, db: AsyncSession, *, email: str) -> models.User | None:
        """メールアドレスからユーザを取得する"""
        stmt = select(models.User).where(models.User.email == email)
        return (await db.execute(stmt)).scalars().first()

    async def create(self, db: AsyncSession, obj_in: schemas.UserCreate) -> models.User:
        """User 新規作成 (なぜbaseを使わないのか不明)"""
        db_obj = models.User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name
        )
        db.add(db_obj)
        await db.flush() # 更新実行
        await db.refresh(db_obj)
        return db_obj # 作成インスタンスを返却する

    async def update(self, db: AsyncSession, *, db_obj: models.User, obj_in: schemas.UserUpdate) -> models.User:
        """ユーザ情報更新"""
        if obj_in.password:
            db_obj.hashed_password = get_password_hash(obj_in.password)

        user = await super().update(db, db_obj=db_obj, update_schema=obj_in)
        return user

    async def authenticate(self, db: AsyncSession, *, email: str, password: str) -> models.User | None:
        """認証済ユーザか確認する. 認証済の場合インスタンスを返却する"""
        user = await self.get_by_mail(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

user = CRUDUser(
    models.User,
    response_schema_class=schemas.UserResponse,
    list_response_class=schemas.UsersPagedResponse
)