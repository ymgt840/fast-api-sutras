from collections.abc import AsyncGenerator, Generator
# sql
from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import text
# setting, log
from app.core.config import settings
from app.core.logger import get_logger
# log 生成
logger = get_logger(__name__)

# DB接続設定を定義
try: # 通常エンジンを定義する
    engine = create_engine(
        settings.get_database_url(),
        connect_args={"auth_plugin": "mysql_native_password"},
        pool_pre_ping=True,
        echo=False,
        future=True,
    )
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
except Exception as e:
    logger.error(f"DB connection error. detail={e}")

try: # 非同期エンジンを定義する
    async_engine = create_async_engine(
        settings.get_database_url(),
        connect_args={"auth_plugin": "mysql_native_password"},
        pool_pre_ping=True,
        echo=False,
        future=True,
    )
    async_session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=async_engine,
        class_=AsyncSession,
    )
except Exception as e:
    logger.error(f"DB connection error. detail={e}")


def get_db() -> Generator[Session, None, None]:
    """
    通常DBセッションを生成し動作させる
    endpointからアクセス時に、Dependで呼び出しdbセッションを生成する
    エラーがなければ、commitする
    エラー時はrollbackし、いずれの場合も最終的にcloseする.
    """
    db = None
    try:
        db = session_factory()
        yield db
        db.commit()
    except Exception:
        if db:
            db.rollback()
    finally:
        if db:
            db.close()

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """非同期DBセッションを生成し動作させる"""
    async with async_session_factory() as db:
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
        finally:
            await db.close()

def drop_all_tables() -> None:
    """全てのテーブルおよび型、Roleなどを削除して、初期状態に戻す(開発環境専用)"""
    logger.info("start: drop_all_tables")
    if settings.ENV != "local":
        # ローカル環境以外は非動作
        logger.info("drop_all_table() is ENV local only.")
        return

    metadata = MetaData()
    metadata.reflect(bind=engine) # 通常エンジンと紐づける

    with engine.connect() as connect:
        # 外部キー制約を無効にして、データを無制限に削除できるようにする
        connect.execute("SET FOREIGN_KEY_CHECKS = 0")
         # 全テーブル削除
        for table in metadata.tables:
            connect.execute(text(f"DROP TABLE {table} CASCADE"))
        # 外部キー制約を有効化
        connect.execute("SET FOREIGN_KEY_CHECKS = 1")
    logger.info("end: drop_all_tables")
