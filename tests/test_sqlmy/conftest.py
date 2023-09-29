"""
databaseのtest用のfixtureを定義する
"""
from typing import Generator

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table

from sqlmy.database import Database

metadata = MetaData()

# サンプルテーブルの定義
sample_table = Table(
    "sample_table",
    metadata,
    Column("id", Integer),
    Column("name", String),
)

# テスト用のエンジンURL
DATABASE_NAME = "test_db"

TEST_ENGINE_URL = (
    f"postgresql://test_user:test_password@test_db:5432/{DATABASE_NAME}"
)


@pytest.fixture
def db_instance() -> Generator[Database, None, None]:
    """database.Databaseのインスタンスを作成する"""
    database = Database(metadata=metadata, engine_url=TEST_ENGINE_URL)

    database.create_database()
    database.create_tables()
    database.start_transaction()
    database.execute_query("DELETE FROM sample_table")
    database.commit_transaction()
    yield database
    database.disconnect()
