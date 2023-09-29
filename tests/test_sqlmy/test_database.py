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
class TestDatabaseConnection:
    """
    database.Databaseの接続に関するテスト
    """

    def test_connection(self, db_instance: Database):
        """connectionが確立されることを確認する"""
        db_instance.connect()
        assert db_instance.connection is not None

    def test_disconnection(self, db_instance: Database):
        """connectionが切断されることを確認する"""
        db_instance.connect()
        db_instance.disconnect()
        assert db_instance.connection is None


class TestDatabaseTransaction:
    """
    database.Databaseのトランザクションに関するテスト
    """

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

    def test_transaction_error(self, db_instance: Database):
        """トランザクション内でのエラー処理を確認する"""
        db_instance.start_transaction()
        with pytest.raises(SQLAlchemyError):
            db_instance.execute_query("INVALID SQL QUERY")  # 無効なクエリを実行
        assert db_instance.trans == []  # トランザクションは自動的に終了/ロールバックされていることを確認

    def test_nested_transaction(self, db_instance: Database):
        """ネストされたトランザクションを確認する"""
        db_instance.start_transaction()
        db_instance.execute_query(
            "INSERT INTO sample_table (name) VALUES (:name)", name="Test1"
        )
        db_instance.start_nested_transaction()
        db_instance.execute_query(
            "INSERT INTO sample_table (name) VALUES (:name)", name="Test2"
        )
        db_instance.rollback_transaction()
        db_instance.commit_transaction()
        db_instance.start_transaction()
        result = db_instance.execute_query("SELECT * FROM sample_table")
        db_instance.commit_transaction()
        assert len(result) == 1
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


class TestDatabaseQueryExecution:
    """
    database.Databaseのexecute_queryに関するテスト
    """

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
        """トランザクション内でinvalidなクエリ実行の場合、トランザクションがロールバックされることを確認する"""
        with pytest.raises(SQLAlchemyError):
            db_instance.execute_query_with_transaction("INVALID SQL QUERY")
        assert db_instance.trans == []

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


class TestDatabaseTableOperations:
    """
    database.Databaseのテーブル操作に関するテスト
    """

    def test_create_tables(self, db_instance: Database):
        """テーブルが作成されることを確認する"""
        assert db_instance.exists_table("sample_table")

    def test_exists_table(self, db_instance: Database):
        """テーブルが存在することを確認する"""
        assert db_instance.exists_table("sample_table") is True
        assert db_instance.exists_table("not_exists_table") is False

    def test_drop_table(self, db_instance: Database):
        """テーブルが削除されることを確認する"""
        db_instance.drop_table("sample_table")
        assert db_instance.exists_table("sample_table") is False
        db_instance.create_tables()


class TestDatabaseSchema:
    """
    database.Databaseのスキーマ操作に関するテスト
    """

    def test_get_table_schema_type(self, db_instance: Database):
        """テーブルのスキーマを取得する"""
        column_type_dict = db_instance.get_table_column_and_type(
            "sample_table"
        )
        assert column_type_dict == {
            "id": "INTEGER",
            "name": "VARCHAR",
        }

    def test_get_table_schema_type_error(self, db_instance: Database):
        """存在しないテーブルのスキーマを取得する"""
        with pytest.raises(ValueError):
            db_instance.get_table_column_and_type("not_exists_table")

    def test_make_pd_type_dict_from_schema(self, db_instance: Database):
        """テーブルのスキーマからpandasの型の辞書を作成する"""
        pd_type_dict = db_instance.make_pd_type_dict_from_schema(
            "sample_table"
        )
        assert pd_type_dict == {
            "id": "Int64",
            "name": "object",
        }
