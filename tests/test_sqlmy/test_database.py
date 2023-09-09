"""
database.pyのテスト
"""
from typing import Generator

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table
from sqlalchemy.exc import SQLAlchemyError

# import threading
from sqlmy.database import Database

# import psycopg2

metadata = MetaData()

# サンプルテーブルの定義
sample_table = Table(
    "sample_table",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String),
)

# テスト用のエンジンURL
DATABASE_NAME = "test_db"

TEST_ENGINE_URL = "sqlite:///:memory:"


# @pytest.fixture(scope="session", autouse=True)
# def create_and_drop_database():
#     # デフォルトのデータベース(通常は"postgres")に接続
#     conn = psycopg2.connect(dbname="postgres",
# user="your_username", password="your_password", host="localhost")
#     conn.autocommit = True  # このモードを使ってデータベースの作成と削除を行う

#     cursor = conn.cursor()

#     # テストの前: データベースを作成
#     cursor.execute(f"DROP DATABASE IF EXISTS {DATABASE_NAME};")
#     cursor.execute(f"CREATE DATABASE {DATABASE_NAME};")

#     cursor.close()
#     conn.close()

#     yield  # ここでテストが実行される

#     # テストの後: データベースを削除
#     conn = psycopg2.connect(dbname="postgres",
# user="your_username", password="your_password", host="localhost")
#     conn.autocommit = True

#     cursor = conn.cursor()
#     cursor.execute(f"DROP DATABASE {DATABASE_NAME};")

#     cursor.close()
#     conn.close()


# def insert_into_database(db_instance: Database, value: int):
#     db_instance.execute_query
# ("INSERT INTO sample_table (name) VALUES (:name)", name=value)


@pytest.fixture
def db_instance() -> Generator[Database, None, None]:
    """database.Databaseのインスタンスを作成する"""
    database = Database(metadata=metadata, engine_url=TEST_ENGINE_URL)
    yield database
    database.disconnect()


# pylint: disable=redefined-outer-name
class TestDatabase:
    """database.Databaseのテスト"""

    def test_connection(self, db_instance: Database):
        """connectionが確立されることを確認する"""
        db_instance.connect()
        assert db_instance.connection is not None

    def test_disconnection(self, db_instance: Database):
        """connectionが切断されることを確認する"""
        db_instance.connect()
        db_instance.disconnect()
        assert db_instance.connection is None

    def test_create_tables(self, db_instance: Database):
        """テーブルが作成されることを確認する"""
        db_instance.create_tables()
        assert db_instance.exists_table("sample_table")
        db_instance.drop_table("sample_table")

    def test_transaction(self, db_instance: Database):
        """トランザクションが開始されることを確認する"""
        db_instance.start_transaction()
        assert db_instance.trans != []
        db_instance.commit_transaction()
        assert db_instance.trans == []

    def test_transaction_rollback(self, db_instance: Database):
        """トランザクション内でロールバックを確認する"""
        db_instance.create_tables()
        db_instance.start_transaction()
        db_instance.execute_query(
            "INSERT INTO sample_table (name) VALUES (:name)", name="Test"
        )
        db_instance.rollback_transaction()
        result = db_instance.execute_query("SELECT * FROM sample_table")
        assert result == []

    def test_rollback_transaction(self, db_instance: Database):
        """トランザクションがロールバックされることを確認する"""
        db_instance.start_transaction()
        db_instance.rollback_transaction()
        assert db_instance.trans == []
        db_instance.drop_table("sample_table")

    def test_nested_transaction(self, db_instance: Database):
        """ネストされたトランザクションを確認する"""
        db_instance.create_tables()
        db_instance.start_transaction()  # 外部トランザクション
        db_instance.execute_query(
            "INSERT INTO sample_table (name) VALUES (:name)", name="Test1"
        )
        db_instance.start_nested_transaction()  # 内部トランザクション
        db_instance.execute_query(
            "INSERT INTO sample_table (name) VALUES (:name)", name="Test2"
        )
        db_instance.rollback_transaction()  # 内部トランザクションのロールバック
        db_instance.commit_transaction()  # 外部トランザクションのコミット
        result = db_instance.execute_query("SELECT * FROM sample_table")
        assert len(result) == 1  # Test2はロールバックされているので1つだけの結果
        assert result[0][1] == "Test1"
        db_instance.drop_table("sample_table")

    def test_transaction_error(self, db_instance: Database):
        """トランザクション内でのエラー処理を確認する"""
        db_instance.start_transaction()
        with pytest.raises(SQLAlchemyError):  # ここには予想される例外を入れてください
            db_instance.execute_query("INVALID SQL QUERY")
        assert db_instance.trans == []  # トランザクションは自動的に終了/ロールバックされていることを確認

    def test_execute_query_select(self, db_instance: Database):
        """select文が実行されることを確認する"""
        db_instance.create_tables()
        result = db_instance.execute_query("SELECT * FROM sample_table")
        assert result == []
        db_instance.drop_table("sample_table")

    def test_execute_query_insert(self, db_instance: Database):
        """insert文が実行されることを確認する"""
        db_instance.create_tables()
        row_id = db_instance.execute_query(
            "INSERT INTO sample_table (name) VALUES (:name)", name="Test"
        )
        assert row_id == 1
        db_instance.drop_table("sample_table")

    def test_visibility_before_commit(self, db_instance: Database):
        """insert文が実行されることを確認する"""
        db_instance.create_tables()
        db_instance.start_transaction()
        row_id = db_instance.execute_query(
            "INSERT INTO sample_table (name) VALUES (:name)", name="Test"
        )
        db_instance.disconnect()
        db_instance.connect()
        result = db_instance.execute_query(
            "SELECT * FROM sample_table WHERE id=:id", id=row_id
        )
        assert len(result) == 0
        db_instance.drop_table("sample_table")

    def test_execute_query_update(self, db_instance: Database):
        """update文が実行されることを確認する"""
        db_instance.create_tables()
        db_instance.execute_query(
            "INSERT INTO sample_table (name) VALUES (:name)", name="Test"
        )
        affected_rows = db_instance.execute_query(
            "UPDATE sample_table SET name=:new_name WHERE name=:old_name",
            new_name="Updated",
            old_name="Test",
        )
        assert affected_rows == 1
        db_instance.drop_table("sample_table")

    def test_exists_table(self, db_instance: Database):
        """テーブルが存在することを確認する"""
        db_instance.create_tables()
        assert db_instance.exists_table("sample_table") is True
        assert db_instance.exists_table("not_exists_table") is False
        db_instance.drop_table("sample_table")

    def test_drop_table(self, db_instance: Database):
        """テーブルが削除されることを確認する"""
        db_instance.create_tables()
        db_instance.drop_table("sample_table")
        assert db_instance.exists_table("sample_table") is False

    # def test_concurrent_insert_with_threading(self, db_instance: Database):
    #     db_instance.create_tables()

    #     # 並行してデータベースにデータを挿入
    #     threads = [threading.Thread
    # (target=insert_into_database, args=(db_instance, i)) for i in range(10)]
    #     for thread in threads:
    #         thread.start()

    #     # すべてのスレッドが終了するのを待つ
    #     for thread in threads:
    #         thread.join()

    #     # データベースのレコード数を確認
    #     result = db_instance.execute_query("SELECT COUNT(*)
    # FROM sample_table")
    #     # 10スレッドがそれぞれ1つのレコードを挿入しているので、合計10レコードが存在するはず
    #     assert result[0][0] == 10

    #     db_instance.drop_table("sample_table")
