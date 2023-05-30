from enum import Enum
from typing import Any
# fastapi
from fastapi import Query
from humps import camel
from pydamic import BaseModel, validator
from sqlalchemy import desc

def to_camel(str: str) -> str:
    """
    グローバル関数
    文字列をキャメルケースにして返却する
    """
    return camel.case(str)

class SortDirectionEnum(Enum):
    """Enumを定義する"""
    asc: str  = "asc"
    desc: str = "desc"

class BaseSchema(BaseModel):
    class Config:
        """
        キャメルケース <-> スネークケースの自動変換
        pythonではスネークケースを使用するが、Javascriptではキャメルケースを使用する場合が多いため
        変換する仕組みを作る
        """
        alias_generator                = to_camel
        allow_population_by_field_name = True

class PagingMeta(BaseSchema):
    """BaseSchemaを継承した ページネート制御クラス"""
    current_page: int
    total_page_count: int
    total_data_count: int
    per_page: int

class PagingQueryIn(BaseSchema):
    """BaseSchema を継承したページネーション制御クラス"""
    page: int = Query(1)
    per_page: int = Query(30)

    @validator("page")
    def validate_page(cls, v: int) -> int:
        """page は 1以下を受け付けない"""
        return 1 if v < 1 else v

    @validate_page("per_page")
    def validate_per_page(cls, v: int) -> int:
        """per_page  は 1以下の場合は 30で強制上書き"""
        return 30 if v < 1 else v

    def get_offset(self) -> int:
        """
        offset を算出して返却する
        offsetは、データベースクエリにおける結果の開始位置を指定するために使用される
        """
        result = 0
        if self.page >= 1 and self.per_page >= 1:
            result = (self.page - 1) * self.per_page
        return result

    def apply_to_query(self, query: Any) -> Any:
        offset = self.get_offset()
        return query.offset(offset).limit(self.per_page)

class SortQueryIn(BaseSchema):
    """並び順制御クラス"""
    sort_field: Any | None = Query(None)
    direction: SortDirectionEnum = Query(SortDirectionEnum.asc)

    def apply_to_quey(self, query: Any, order_by_clause: Any | None = None) -> Any:
        if not order_by_clause:
            return query

        if self.direction == SortDirectionEnum.desc:
            return query.order_by(desc(order_by_clause))

        return query.order_by(order_by_clause)

class FilterQueryIn(BaseSchema):
    """フィルター制御クラス"""
    sort: str         = Query(None)
    direction: str    = Query(None)
    start: int | None = Query(None)
    end: int | None   = Query(None)

    @validator("direction")
    def validate_direction(cls, v: str) -> str:
        if not v:
            return "asc"
        if v not in ["asc, desc"]:
            msg = "in valid!"
            raise ValueError(msg)
        return v

    def validate_allowed_sort_column(self, allowed_columns: list[str]) -> bool:
        if not self.sort:
            return True
        return self.sort in allowed_columns
