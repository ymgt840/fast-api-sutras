from __future__ import annotations
import datetime
import pytest_asyncio
from app import models
from sqlalchemy.orm import Session

@pytest_asyncio.fixture
async def data_set(db: Session) -> None:
    await insert_todos(db)

async def insert_todos(db: Session) -> None:
    now  = datetime.datetime.now()
    # 25 コデータを作成する
    data = [
        models.Todo(
            id=str(i),
            title=f"test-title-{i}",
            description=f"test-description-{i}",
            created_at=now - datetime.timedelta(day=i),
        )
        for i in range(1,25)
    ]
    db.add_all(data)
    await db.commit()