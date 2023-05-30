from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, ModelBaseMixinWithoutDeletedAt

class TodoTag(ModelBaseMixinWithoutDeletedAt, Base):
    __tablename__  = "todos_tags"
    mysql_charset  = ("utf8mb4",)
    mysql_collate  = "utf8mb4_unicode_ci"
    __table_args__ = (
        UniqueConstraint("todo_id", "tag_id", name="ix_todos_tags_todo_id_tag_id")
    )

    name: Mapped[str]   = Column(String(100), unique=True, index=True)
    todos: Mapped[list] = relationship(
        "Todo",
        secondary="todos_tags",
        back_populates="tags",
        lazy="joined",
    )