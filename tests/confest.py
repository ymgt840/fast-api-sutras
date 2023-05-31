import logging
import os
from collections.abc import AsyncGenerator
from typing import Any
import alembic.command # マイグレーションを制御する
import alembic.config
import pytest
import pytest_asyncio
from app import schemas
from app.core.config import Settings
from app.core.database import get_async_db
from app.main import app
from fastapi import status
from httpx import AsyncClient
from pytest_mysql import factories
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
# 初期設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.info("root-conftest")
pytest.USER_ID = ""

class TestSettings(Settings):
    """テスト実施時に使用する設定を定義する"""
    TEST_USER_EMAIL: str    = "test-user1@example.com"
    TEST_USER_PASSWORD: str = "test-user"
    class Config:
        env_file = ".env.test"
settings = TestSettings()

# db 設定
logger.debug("start:mysql_proc")
db_proc = factories.mysql_noproc( # proc = プロシージャ
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    user=settings.DB_USER_NAME,
)
mysql = factories.mysql("db_proc")
logger.debug("end:mysql_proc")

# schema設定
TEST_USER_CREATE_SCHEMA = schemas.UserCreate(
    email=settings.TEST_USER_EMAIL,
    password=settings.TEST_USER_PASSWORD,
    full_name="test_user"
)

def migrate(
    versions_path: str,
    migrate_path: str,
    uri: str,
    alembic_ini_path: str,
    connection: Any = None,
    revision: str = "head",
) -> None:
    """migration を実行する？"""
    # config 設定
    config = alembic.config.Config(alembic_ini_path)
    config.set_main_option("version_locations", versions_path)
    config.set_main_option("script_location", migrate_path)
    config.set_main_option("sqlalchemy.url", uri)

    if connection is not None:
        config.attribute["connection"] = connection
    # upgrade = migrate?
    alembic.command.upgrade(config, revision)

@pytest_asyncio.fixture
async def engine(mysql: Any) -> AsyncEngine:
    """fixture: db-engine の作成 および migrate を実行し engine を返却する"""
    logger.debug("fixture:engine")
    uri    = settings.get_database_url(is_async=True)
    # migrate(alembic)はasyncに未対応なため、sync-engineを使用する
    sync_uri = settings.get_database_url()
    print(sync_uri)
    sync_engine = create_engine(sync_uri, echo=False, poolclass=NullPool)
    with sync_engine.begin() as conn:
        migrate(
            versions_path=os.path.join(settings.MIGRATIONS_DIR_PATH, "versions"),
            migrate_path=settings.MIGRATIONS_DIR_PATH,
            uri=sync_uri,
            alembic_ini_path=os.path.join(settings.ROOT_DIR_PATH, "alembic.ini"),
            connection=conn,
        )
    logger.debug("migration end")

    engine = create_async_engine(uri, echo=False, poolclass=NullPool)
    return engine

@pytest_asyncio.fixture
async def db(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """fixture: db-session の作成"""
    test_session_factory = sessionmaker(
        autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
    )

    async with test_session_factory() as session:
        yield session
        await session.commit()

@pytest_asyncio.fixture
async def client(engine: AsyncEngine) -> AsyncClient:
    """fixture: HTTP-Clientの作成"""
    test_session_factory = sessionmaker(
        autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
    )
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        """内部関数 Test用のDBを指定する"""
        async with test_session_factory() as session:
            yield session
            await session.commit()
    # get_dbをTest用のDBを使用するようにoverrideする
    app.dependency_overrides[get_async_db] = override_get_db
    app.debug = False
    return AsyncClient(app=app, base_url="http://test")

@pytest_asyncio.fixture
async def user_login(client: AsyncClient) -> AsyncClient:
    """fixture: ログインを通し、認証ユーザを生成する"""
    # テストユーザを作成
    res = await client.post(
        "/users",
        json=TEST_USER_CREATE_SCHEMA.dict(),
    )
    assert res.status_code == status.HTTP_200_OK

    # ログイン実行
    res = await client.post(
        "/auth/login",
        data={
            "username": settings.TEST_USER_EMAIL,
            "password": settings.TEST_USER_PASSWORD,
        },
    )
    assert res.status_code == status.HTTP_200_OK
    # token を取得する
    access_token = res.json().get("access_token")
    client.headers = {"authorization": f"Bearer {access_token}"}

    res = await client.get("users/me")
    assert res.json().get("id") is not None
    pytest.USER_ID = res.json().get("id")  # テスト全体で使用するので、グローバル変数とする

    return client