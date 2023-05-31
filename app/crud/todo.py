from sqlalchemy import or_
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, contains_eager
from sqlalchemy.sql import select
from app import crud, models, schemas
from .base import CRUDBase

class CRUDTodo(
    CRUDBase[
        models.Todo,
        schemas.TagResponse,
        schemas.TagCreate,
        schemas.TagUpdate,
        schemas.TagsPagedResponse,
    ],
):
    async def get_paged_list( # type: ignore[override]
        self,
        db: AsyncSession,
        paging_query_in: schemas.PagingQueryIn,
        q: str | None = None,
        sort_query_in: schemas.SortQueryIn | None = None,
        include_deleted: bool = False,
    ) -> schemas.TodosPagedResponse:
        """
        get_paged_list を オーバーライド.. where句を追加する
        """
        conditions = (
            [
                or_(
                    models.Todo.title.like(f"%{q}%"),
                    models.Todo.description.like(f"%{q}%")
                ),
            ]
            if q else []
        )

        data = await super().get_paged_list(
            db,
            paging_query_in,
            conditions,
            sort_query_in,
            include_deleted
        )

        return data

    def add_tags_to_todo(self, db:Session, todo: models.Todo, tags_in: list[schemas.TagCreate]) -> models.Todo:
        # Tags を upsert してデータを受け取り、整形してlist[dict]に格納する
        # TodoTag insert value を作成する
        tags   = crud.tag.upsert_tags(db, tag_in=tags_in)
        t_data = [{"todo_id": todo.id, "tag_id": tag.id} for tag in tags]

        # TodoTag を作成する by upsert
        stmt = insert(models.TodoTag).values(t_data)
        stmt = stmt.on_duplicate_key_update(tag_id=stmt.inserted.tag_id)
        db.execute(stmt)

        stmt = (
            select(models.Todo)
            .outerjoin(models.Todo.tags) # TodoTag　を経由して tags とリレーションを取得する
            .options(contains_eager(models.Todo.tags)) # eager load を指定する
            .where(models.Todo.id == todo.id)
        )
        todo = db.execute(stmt).scalars().unique().first() # 非重複でデータを取得する

        return todo

todo = CRUDTodo(
    models.Todo,
    response_schema_class=schemas.TodoResponse,
    list_response_class=schemas.TodosPagedResponse,
)