import datetime
from enum import Enum
from fastapi import Query
from app import schemas
from app.schemas.core import BaseSchema, PagingMeta
from app.schemas.tag import TagResponse

class TodoSortFieldEnum(Enum):
    created_at = "created_at"
    title      = "title"

class TodoBase(BaseSchema):
    """todo の基本スキーマを定義する"""
    title: str | None
    description: str | None
    completed_at: datetime.datetime | None

class TodoResponse(TodoBase):
    id: str
    tags: list[TagResponse] | None # Tagを保持する
    created_at: datetime.datetime | None
    updated_at: datetime.datetime | None

    class Config:
        orm_mode = True

class TodoCreate(TodoBase):
    title: str
    description: str | None

class TodoUpdate(TodoBase):
    pass

class TodosPagedResponse(BaseSchema):
    data: list[TodoResponse] | None
    meta: PagingMeta | None

class TodoSortQueryIn(schemas.SortQueryIn):
    """SortQueryIn を継承したクラス"""
    sort_field: TodoSortFieldEnum | None = Query(TodoSortFieldEnum.created_at)