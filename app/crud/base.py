# 基本設定
import datetime
import math
from enum import Enum
from typing import Any, Generic, TypeVar
# fastapi
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.sql import func, select
# app
from app import schemas
from app.exceptions.core import APIException
from app.exceptions.error_message import ErrorMessage
from app.models.base import Base
from app.schemas.core import PagingQueryIn

#TypeVar を使用して以下の型を定義する
ModelType              = TypeVar("ModelType", bound=Base)
ResponseSchemaType     = TypeVar("ResponseSchemaType", bound=BaseModel)
CreateSchemaType       = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType       = TypeVar("UpdateSchemaType", bound=BaseModel)
ListResponseSchemaType = TypeVar("ListResponseSchemaType", bound=BaseModel)

class CRUDBase(
    Generic[
        ModelType,
        ResponseSchemaType,
        CreateSchemaType,
        UpdateSchemaType,
        ListResponseSchemaType,
    ],
):
    def __init__(
        self,
        model: type[ModelType],
        response_schema_class: type[ResponseSchemaType],
        list_response_class: type[ListResponseSchemaType]
    ) -> None:
        self.model                 = model
        self.response_schema_class = response_schema_class
        self.list_response_class   = list_response_class

    def _get_select_columns(self) -> list(ColumnProperty):
        """
        ResponseSchemaに含まれる fieldのみを
        sqlalchemyの select用のobject として返す
        """
        schema_columns = list(self.response_schema_class.__fields__.keys())
        mapper         = inspect(self.model) # マッパーを取得する
        select_columns = [
            # for文を実行し、条件文に合致するデータのみ, getattr を実行して listに代入する
            getattr(self.model, attr.key)
            for attr in mapper.attrs
            if (isinstance(attr, ColumnProperty)) and (attr.key in schema_columns)
        ]

        return select_columns

    def _filter_model_exists_fields(self, data_dict: dict[str, Any]) -> dict[str, Any]:
        """
        data_dict を基準に
        modelに存在する field のみを返却する
        """
        data_fields   = list(data_dict.keys())
        mapper        = inspect(self.model)
        exists_d_dict = {}
        for attr in mapper.attrs: # 条件に合致する field のみを返却する
            if isinstance(attr, ColumnProperty) and (attr.key in data_fields):
                exists_d_dict[attr.key] = data_dict[attr.key]

        return exists_d_dict

    def _get_order_by_clause(self, sort_field: Any | Enum) -> ColumnProperty | None:
        """
        引数 sort_field に合致する modelのfield を返却する
        """
        sort_field_value = sort_field.value if isinstance(sort_field, Enum) else sort_field
        mapper = inspect(self.model)

        order_by_clause = [
            attr
            for attr in mapper.attrs
            if isinstance(attr, ColumnProperty) and (attr.key == sort_field_value)
        ]

        return order_by_clause[0] if order_by_clause else None

    async def get_db_obj_by_id(
        self,
        db: AsyncSession,
        id: Any,
        include_deleted: bool = False,
    ) -> ModelType | None:
        """
        id から obj のデータを取得する
        """
        sql = select(self.model).where(self.model.id == id).execution_options(include_deleted=include_deleted)
        # scalars を使用してスカラー値のみ取得する
        return (await db.execute(sql)).scalars().first()

    async def get_db_obj_list(
        self,
        db: AsyncSession,
        where_clause: list[Any] | None = None,
        sort_query_in: schemas.SortQueryIn | None = None,
        include_deleted: bool = False,
    ) -> list[ModelType | None]:
        """
        一覧データを取得する
        """
        where_clause = where_clause if where_clause is not None else []
        stmt         = select(self.model).where(*where_clause) # where句をunpack

        if sort_query_in:
            order_by_clause = self._get_order_by_clause(sort_query_in.sort_field)
            stmt            = sort_query_in.apply_to_quey(stmt, order_by_clause=order_by_clause)

        db_obj_list = (await db.execute(stmt.execution_option(include_deleted=include_deleted))).all()
        return db_obj_list

    async def get_paged_list(
        self,
        db: AsyncSession,
        paging_query_in: PagingQueryIn,
        conditions: list[Any] | None = None,
        sort_query_in: schemas.SortQueryIn | None = None,
        include_deleted: bool = False,
    ) -> ListResponseSchemaType:
        """
        ページネーション付データを返却する
        """
        # ページネート使用データ取得
        conditions = conditions if conditions is not None else []
        stmt       = select(func.count(self.model.id)) \
                        .where(*conditions) \
                        .execution_options(include_deleted=include_deleted)
        total_cnt = (await db.execute(stmt)).scalar() # 取得行数を取得

        # データ取得
        selects = self._get_select_columns()
        stmt    = select(*selects).where(*conditions)
        if sort_query_in: # order がある場合取得して追加する
            order = self._get_order_by_clause(sort_query_in.sort_field)
            stmt  = sort_query_in.apply_to_quey(stmt, order_by_clause=order)

        stmt = stmt.execution_options(include_deleted=include_deleted)
        stmt = paging_query_in.apply_to_query(stmt)
        data = (await db.execute(stmt)).all()

        # meta データ生成
        meta = schemas.PagingMeta( # PagingMeta をインスタンス生成する
            total_data_count = total_cnt,
            current_page     = paging_query_in.page,
            total_page_count = int(math.ceil(total_cnt / paging_query_in.per_page)),
            per_page         = paging_query_in.per_page
        )
        # response 返却
        return self.list_response_class(data=data, meta=meta)

    async def create(
        self,
        db: AsyncSession,
        create_schema: CreateSchemaType,
    ) -> ModelType:
        """ データ新規作成 """
        create_dict = jsonable_encoder(create_schema, by_alias=False) # camelCase 採用を防ぐ
        exists_dict = self._filter_model_exists_fields(create_dict)

        db_obj = self.model(**exists_dict) # db_objを生成
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)

        return db_obj


    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        update_schema: UpdateSchemaType
    ) -> ModelType:
        """データ更新"""
        db_obj_dict = jsonable_encoder(db_obj)
        update_dict = update_schema.dict(exclude_unset=True) # 未指定カラムは更新しない

        for field in db_obj_dict: # attr をセットする
            if field in update_dict:
                # db_obj の field の値は update_dict[field]
                setattr(db_obj, field, update_dict[field])

        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def delete(
        self,
        db: AsyncSession,
        db_obj: ModelType
    ) -> ModelType:
        """soft delete 論理削除"""
        # バリデーション
        if not hasattr(db_obj, "deleted_at"): # deleted_at カラムが存在しない場合
            raise APIException(ErrorMessage.SOFT_DELETE_NOT_SUPPORTED)
        if db_obj.deleted_at:
            raise APIException(ErrorMessage.ALREADY_DELETED)

        db_obj.deleted_at = datetime.datetime.now(tz=datetime.timezone.utc) # moduleのdatetimeを取ってきている
        await db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def hard_delete(
        self,
        db: AsyncSession,
        db_obj: ModelType,
    ) -> None:
        """物理削除"""
        await db.delete(db_obj)
        await db.flush()

