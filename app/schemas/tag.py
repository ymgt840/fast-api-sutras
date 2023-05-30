import datetime
from app.schemas.core import BaseSchema, PagingMeta

class TagBase(BaseSchema):
    """Tag の 基本スキーマ を定義するクラス"""
    name: str | None

class TagResponse(TagBase):
    """ Tag のレスポンススキーマを定義するクラス """
    id: str
    created_at: datetime.datetime | None
    updated_at: datetime.datetime | None
    deleted_at: datetime.datetime | None

    class Config: # BaseSchema Configのオーバーライド
        orm_mode = True

class TagCreate(TagBase):
    """Tag の 作成スキーマ を定義するクラス"""
    name: str | None

class TagUpdate(TagBase):
    """Tag の 更新スキーマ 定義するクラス"""
    pass

class TagsPagedResponse(BaseSchema):
    """Tag の ページングレスポンススキーマを 定義するクラス"""
    data: list[TagResponse] | None
    meta: PagingMeta | None