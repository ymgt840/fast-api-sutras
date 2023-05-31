from fastapi.encoders import jsonable_encoder
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session
from sqlalchemy.sql import select
from app import models, schemas
from .base import CRUDBase

class CRUDTag(
    CRUDBase[
        models.Tag,
        schemas.TagResponse,
        schemas.TagCreate,
        schemas.TagUpdate,
        schemas.TagsPagedResponse,
    ],
):
    def upsert_tags(self, db: Session, tag_in: list[schemas.TagCreate]) -> list[models.Tag]:
        """ tag の upsert を実行して tags 一覧を返却する """
        tags_in_list = jsonable_encoder(tag_in)
        insert_stmt  = insert(models.Tag).values(tags_in_list)
        # upsertを設定
        insert_stmt  = insert_stmt.on_duplicated_key_update(name=insert_stmt.inserted.name)
        # insert を実行数
        db.execute(insert_stmt)

        tag_names = (x.name for x in tag_in)
        # in 句指定でtagを取得して返却する
        stmt      = select(models.Tag).where(models.Tag.name.in_(tag_names))
        tags      = db.execute(stmt).scalars().all()

        return tags

tag = CRUDTag(
    models.Tag,
    response_schema_class=schemas.TagResponse,
    list_response_class=schemas.TagsPagedResponse
)