from datetime import datetime
from typing import Any
# sqlalchemy
from sqlalchemy import DateTime, String, event, func, orm
from sqlalchemy.orm import DeclarativeMeta, Mapped, Session, mapped_column
from sqlalchemy.sql.functions import current_timestamp
# app
from app.core.logger import get_logger
from app.core.utils import get_ulid

logger = get_logger(__name__)

class Base(DeclarativeMeta):
    pass

class ModelBaseMixin:
    """Model の基本クラスを定義する"""
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=get_ulid)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=current_timestamp(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=current_timestamp(),
        onupdate=func.utc_timestamp(),
    )
    deleted_at: Mapped[datetime] = mapped_column(DateTime)

class ModelBaseMixinWithoutDeletedAt:
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=get_ulid)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=current_timestamp(),
        onupdate=func.utc_timestamp(),
    )

# ORM実行時に自動的に呼び出されるコールバック関数
@event.listens_for(Session, "do_orm_execute")
def _add_filtering_deleted_at(execute_state: Any) -> None:
    """
    論理削除用のfilterを自動的に適用する
    以下例)論理削除済のデータも含めて取得可能
    select(...).filter(...).execution_options(include_deleted=True).
    """
    if (
        execute_state.is_select
        and not execute_state.is_column_load
        and not execute_state.is_relationship_load
        and not execute_state.execution_options.get("include_deleted", True)
    ):
        execute_state.statement = execute_state.statement.options(
            orm.with_loader_criteria(
                ModelBaseMixin,
                lambda cls: cls.deleted_at.is_(None),
                include_aliases=True
            )
        )