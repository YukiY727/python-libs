"""
databaseのtest用のfixtureを定義する
"""
from typing import Generator

import pytest
from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, Text

from libs.sqlmy.database import Database
from libs.utils.time_zone.time import current_japan_time

test_metadata = MetaData()

# サンプルテーブルの定義
sample_table = Table(
    "sample_table",
    test_metadata,
    Column("id", Integer),
    Column("name", String),
)

logs = Table(
    "logs",
    test_metadata,
    Column("id", Integer, primary_key=True),
    Column("timestamp", DateTime(timezone=True), default=current_japan_time()),
    Column("log_level", String(50)),
    Column("message", Text),
    Column("source", String(100), nullable=True),  # アプリケーションやソース名
    Column("thread_id", String(50), nullable=True),  # スレッドID
    Column("process_id", String(50), nullable=True),  # プロセスID
    Column("user_id", String(100), nullable=True),  # ユーザーID
    Column("session_id", String(100), nullable=True),  # セッションID
    Column("logger_name", String(100), nullable=True),  # ロガーの名前
    Column("stack_trace", Text, nullable=True),  # スタックトレース
    Column("ip_address", String(50), nullable=True),  # IPアドレス
    Column("user_agent", String(300), nullable=True),  # ユーザーエージェント
    Column("environment", String(50), nullable=True),  # 環境情報
    Column("tags", String(100), nullable=True),  # タグ
    Column("additional_data", Text, nullable=True),  # 任意の追加データ
)


TEST_ENGINE_URL = "postgresql://test_user:test_password@test_db:5432/test_db"


@pytest.fixture
def db_instance() -> Generator[Database, None, None]:
    """database.Databaseのインスタンスを作成する"""
    database = Database(metadata=test_metadata, engine_url=TEST_ENGINE_URL)

    database.create_database()
    database.create_tables()
    database.start_transaction()
    database.execute_query("DELETE FROM sample_table")
    database.commit_transaction()
    yield database
    database.disconnect()
