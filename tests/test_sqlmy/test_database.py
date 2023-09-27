"""
database.pyのテスト
"""
import threading
from typing import Generator

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table
from sqlalchemy.exc import SQLAlchemyError

from sqlmy.database import Database

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

TEST_ENGINE_URL = (
    f"postgresql://test_user:test_password@test_db:5432/{DATABASE_NAME}"
)


# @pytest.fixture(scope="session", autouse=True)
# def create_and_drop_database():
#     # デフォルトのデータベース(通常は"postgres")に接続
#     conn = psycopg2.connect(dbname="test_database",
# user="test_user", password="test_password", host="test_db", port="5432")
#     conn.autocommit = True  # このモードを使ってデータベースの作成と削除を行う

#     cursor = conn.cursor()

#     # テストの前: データベースを作成
#     cursor.execute(f"DROP DATABASE IF EXISTS {DATABASE_NAME};")
#     cursor.execute(f"CREATE DATABASE {DATABASE_NAME};")


#     yield  # ここでテストが実行される

#     # テストの後: データベースを削除
#     cursor.execute(f"SELECT pg_terminate_backend(pg_stat_activity.pid)
# FROM pg_stat_activity WHERE pg_stat_activity.datname = '{DATABASE_NAME}'
# AND pid <> pg_backend_pid();")
#     cursor.execute(f"DROP DATABASE {DATABASE_NAME};")

#     cursor.close()
#     conn.close()


# @pytest.fixture(scope="session")
# def create_tables_fixture(db_instance: Database):
#     # テストの前: テーブルを作成
#     db_instance.create_tables()

#     yield  # ここでテストが実行される

#     # テストの後: テーブルを削除
#     db_instance.drop_table("sample_table")


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
        assert db_instance.exists_table("sample_table")

    def test_transaction(self, db_instance: Database):
        """トランザクションが開始されることを確認する"""
        db_instance.start_transaction()
        assert db_instance.trans != []
        db_instance.commit_transaction()
        assert db_instance.trans == []

    def test_transaction_rollback(self, db_instance: Database):
        """トランザクション内でロールバックを確認する"""
        db_instance.start_transaction()
        db_instance.execute_query(
            "INSERT INTO sample_table (name) VALUES (:name)", name="Test"
        )
        db_instance.rollback_transaction()
        db_instance.start_transaction()
        result = db_instance.execute_query("SELECT * FROM sample_table")
        db_instance.commit_transaction()
        assert result == []

    def test_rollback_transaction(self, db_instance: Database):
        """トランザクションがロールバックされることを確認する"""
        db_instance.start_transaction()
        db_instance.rollback_transaction()
        assert db_instance.trans == []

    def test_nested_transaction(self, db_instance: Database):
        """ネストされたトランザクションを確認する"""
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
        db_instance.start_transaction()
        result = db_instance.execute_query("SELECT * FROM sample_table")
        db_instance.commit_transaction()
        assert len(result) == 1  # Test2はロールバックされているので1つだけの結果
        assert result[0][1] == "Test1"

    def test_nest_transaction_error(self, db_instance: Database):
        """
        nestされたトランザクション内で内部トランザクションがエラーになった場合、
        内部トランザクションがロールバックされ、外部トランザクションがコミットされることを確認
        """
        db_instance.start_transaction()
        db_instance.execute_query(
            "INSERT INTO sample_table (name) VALUES (:name)", name="Test1"
        )
        db_instance.start_nested_transaction()  # 内部トランザクション
        with pytest.raises(SQLAlchemyError):
            db_instance.execute_query("INVALID SQL QUERY")
        db_instance.commit_transaction()  # 外部トランザクションのコミット
        db_instance.start_transaction()
        result = db_instance.execute_query("SELECT * FROM sample_table")
        db_instance.commit_transaction()
        assert len(result) == 1  # Test2はロールバックされているので1つだけの結果
        assert result[0][1] == "Test1"

    def test_transaction_error(self, db_instance: Database):
        """トランザクション内でのエラー処理を確認する"""
        db_instance.start_transaction()
        with pytest.raises(SQLAlchemyError):
            db_instance.execute_query("INVALID SQL QUERY")  # 無効なクエリを実行
        assert db_instance.trans == []  # トランザクションは自動的に終了/ロールバックされていることを確認

    def test_execute_query_select(self, db_instance: Database):
        """select文が実行されることを確認する"""
        db_instance.start_transaction()
        result = db_instance.execute_query("SELECT * FROM sample_table")
        db_instance.commit_transaction()
        assert result == []

    def test_execute_query_insert(self, db_instance: Database):
        """insert文が実行されることを確認する"""
        db_instance.start_transaction()
        row_id = db_instance.execute_query(
            "INSERT INTO sample_table (name) VALUES (:name)", name="Test"
        )
        db_instance.commit_transaction()
        assert row_id == 0

    def test_visibility_before_commit(self, db_instance: Database):
        """insert文実行途中にdisconnectした場合、データが確定されないことを確認する"""
        db_instance.start_transaction()
        row_id = db_instance.execute_query(
            "INSERT INTO sample_table (name) VALUES (:name)", name="Test"
        )
        db_instance.disconnect()
        db_instance.connect()
        db_instance.start_transaction()
        result = db_instance.execute_query(
            "SELECT * FROM sample_table WHERE id=:id", id=row_id
        )
        db_instance.commit_transaction()
        assert len(result) == 0

    def test_execute_query_update(self, db_instance: Database):
        """update文が実行されることを確認する"""
        db_instance.start_transaction()
        db_instance.execute_query(
            "INSERT INTO sample_table (name) VALUES (:name)", name="Test"
        )
        db_instance.commit_transaction()
        db_instance.start_transaction()
        affected_rows = db_instance.execute_query(
            "UPDATE sample_table SET name=:new_name WHERE name=:old_name",
            new_name="Updated",
            old_name="Test",
        )
        db_instance.commit_transaction()
        assert affected_rows == 1

    def test_execute_query_with_transaction(self, db_instance: Database):
        """トランザクション内でのクエリ実行を確認する"""
        db_instance.execute_query_with_transaction(
            "INSERT INTO sample_table (name) VALUES (:name)", name="Test"
        )
        db_instance.start_transaction()
        result = db_instance.execute_query("SELECT * FROM sample_table")
        db_instance.commit_transaction()
        assert result[0][1] == "Test"

    def test_execute_query_with_transaction_error(self, db_instance: Database):
        """
        トランザクション内でinvalidなクエリ実行の場合、 トランザクションが
        ロールバックされることを確認する
        """
        with pytest.raises(SQLAlchemyError):
            db_instance.execute_query_with_transaction("INVALID SQL QUERY")
        assert db_instance.trans == []

    def test_exists_table(self, db_instance: Database):
        """テーブルが存在することを確認する"""
        assert db_instance.exists_table("sample_table") is True
        assert db_instance.exists_table("not_exists_table") is False

    def test_drop_table(self, db_instance: Database):
        """テーブルが削除されることを確認する"""
        db_instance.drop_table("sample_table")
        assert db_instance.exists_table("sample_table") is False
        db_instance.create_tables()

    def test_concurrent_insert_with_threading(self, db_instance: Database):
        """
        並行してデータベースにデータを挿入できることを確認する
        """

        # 並行してデータベースにデータを挿入
        def insert_data(name: int):
            db_instance.execute_query_with_transaction(
                "INSERT INTO sample_table (name) VALUES (:name)", name=name
            )

        threads = [
            threading.Thread(target=insert_data, args=(name,))
            for name in range(10)
        ]
        for thread in threads:
            thread.start()

        # すべてのスレッドが終了するのを待つ
        for thread in threads:
            thread.join()

        # データベースのレコード数を確認
        db_instance.start_transaction()
        result = db_instance.execute_query("SELECT COUNT(*) FROM sample_table")
        # 10スレッドがそれぞれ1つのレコードを挿入しているので、合計10レコードが存在するはず
        assert result[0][0] == 10
