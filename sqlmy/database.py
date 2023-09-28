"""
databaseを管理するモジュール。
"""
import threading
from functools import wraps
from typing import Any

from sqlalchemy import (
    Connection,
    MetaData,
    Transaction,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy_utils import create_database, database_exists, drop_database

from utils.singleton import SingletonMeta


class Database(metaclass=SingletonMeta):
    """
    sqlalchemyのエンジンと接続を管理するクラス。

    Attributes:
        metadata (MetaData): sqlalchemyのMetaDataオブジェクト
        engine (Engine): sqlalchemyのエンジン
        connection (Connection): sqlalchemyのコネクション
        trans (RootTransaction): sqlalchemyのトランザクション
        initialized (bool): 初期化済みかどうかを表すフラグ
    """

    def __init__(self, metadata: MetaData, engine_url: str):
        """
        Databaseのコンストラクタ。

        Args:
            metadata (MetaData): sqlalchemyのMetaDataオブジェクト
            engine_url (str): sqlalchemyのエンジンURL
                dialect+driver://username:password@host:port/database
                dialect: 使用するデータベースのタイプ
                        （例：postgresql, mysql, sqlite, oracle など）。
                driver: 使用するデータベースのドライバ
                        （例：psycopg2 はPostgreSQL用の人気のあるドライバ）。
                        ドライバ部分はオプションであり、省略するとデフォルトのドライバが使用されます。
                username: データベースへのログインユーザー名。
                password: データベースへのログインパスワード。
                host: データベースのホスト名またはIPアドレス。
                port: データベースのポート番号。
                database: 接続するデータベース名。
        """
        self.metadata = metadata
        self.engine = create_engine(engine_url)
        self.connection: Connection | None = None
        self.trans: list[Transaction] = []
        self.initialized = False
        self._lock = threading.Lock()

    def connect(self):
        """
        データベースに接続する。接続が既に確立されている場合は何もしない。
        """
        if not self.connection:
            self.connection = self.engine.connect()
            self.initialized = True

    def disconnect(self):
        """
        データベースから切断する。接続が確立されていない場合は何もしない。
        データベースから切断すると、
        リソースが解放される
        トランザクションが開始されている場合はロールバックされる
        """
        if self.connection:
            self.connection.close()
            self.connection = None
            self.initialized = False
            self.trans = []

    @staticmethod
    def _ensure_connection(func):
        """
        メソッドを呼び出す前に接続を確立する。
        """

        @wraps(func)
        def wrapper(self: "Database", *args, **kwargs):
            if not self.initialized:
                self.connect()
            return func(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def _error_not_start_transaction(func):
        """
        トランザクションが開始されていない場合に発生するエラー。
        """

        @wraps(func)
        def wrapper(self: "Database", *args, **kwargs):
            if not self.trans:
                raise SQLAlchemyError("Transaction is not started.")
            return func(self, *args, **kwargs)

        return wrapper

    @_ensure_connection
    def create_tables(self):
        """
        初期化されていない場合、初期化し、テーブルを作成する。
        """
        self.metadata.create_all(self.engine)
        self.metadata.reflect(bind=self.engine)

    @_ensure_connection
    def start_transaction(self):
        """
        トランザクションを開始する。すでにトランザクションが開始されている場合は何もしない。
        """
        if not self.trans:
            self.trans.append(self.connection.begin())

    @_ensure_connection
    def start_nested_transaction(self):
        """
        ネストされたトランザクションを開始する。
        """
        self.trans.append(self.connection.begin_nested())

    @_error_not_start_transaction
    @_ensure_connection
    def commit_transaction(self):
        """
        現在のトランザクションをコミットする。トランザクションが開始されていない場合はエラーを出す。

        Raises:
            SQLAlchemyError: トランザクションが開始されていない場合
        """
        current_trans = self.trans.pop()
        current_trans.commit()

    @_error_not_start_transaction
    def rollback_transaction(self):
        """
        現在のトランザクションをロールバックする。トランザクションが開始されていない場合はエラーを出す。

        Raises:
            SQLAlchemyError: トランザクションが開始されていない場合
        """
        current_trans = self.trans.pop()
        current_trans.rollback()

    @_error_not_start_transaction
    @_ensure_connection
    def execute_query(self, query: str, **params) -> Any:
        """
        与えられたクエリを実行し、結果を返す。

        Args:
            query (str): 実行するクエリ
            **params: クエリに渡すパラメータ

        Returns:
            クエリの結果。SELECT文の場合は結果セット、INSERT文の場合は最後の行ID、その他の場合は影響を受けた行数。

        Raises:
            SQLAlchemyError: クエリの実行に失敗した場合
        """
        if not self.connection:
            raise SQLAlchemyError("Database is not initialized.")
        try:
            result_proxy = self.connection.execute(text(query), params)

            # クエリがSELECT文かどうかを確認
            if query.strip().upper().startswith("SELECT"):
                return result_proxy.fetchall()
            if query.strip().upper().startswith("INSERT"):
                return result_proxy.lastrowid  # 挿入された行のIDを返す
            return result_proxy.rowcount  # 影響を受けた行数を返す
        except SQLAlchemyError as error:
            self.rollback_transaction()
            # SQLAlchemyのエラーに関するハンドリング
            raise error

    @_ensure_connection
    def execute_query_with_transaction(self, query: str, **params) -> Any:
        """
        与えられたクエリをトランザクション内で実行する。

        Args:
            query (str): 実行するクエリ
            **params: クエリに渡すパラメータ

        Returns:
            クエリの結果。SELECT文の場合は結果セット、INSERT文の場合は最後の行ID、その他の場合は影響を受けた行数。

        """
        with self._lock:
            self.start_transaction()
            result = self.execute_query(query, **params)
            self.commit_transaction()
        return result

    def exists_table(self, table_name: str) -> bool:
        """
        指定されたテーブルが存在するかどうかを返す。

        Args:
            table_name (str): テーブル名

        Returns:
            bool: テーブルが存在するかどうか
        """
        inspector = inspect(self.engine)
        return table_name in inspector.get_table_names()

    def drop_table(self, table_name: str):
        """
        指定されたテーブルを削除する。

        Args:
            table_name (str): テーブル名

        Raises:
            SQLAlchemyError: テーブルが存在しない場合
        """
        if self.exists_table(table_name):
            self.metadata.tables[table_name].drop(self.engine)
        else:
            raise SQLAlchemyError(f"Table {table_name} does not exist.")

    def create_database(self):
        """
        データベースを作成する。
        """
        if not database_exists(self.engine.url):
            create_database(self.engine.url)

    def drop_database(self):
        """
        データベースを削除する。
        """
        if database_exists(self.engine.url):
            drop_database(self.engine.url)

    def exists_database(self) -> bool:
        """
        データベースが存在するかどうかを返す。

        Returns:
            bool: データベースが存在するかどうか
        """
        return database_exists(self.engine.url)

    def __del__(self):
        """
        オブジェクトが破棄される前にデータベース接続を切断する。
        """
        self.disconnect()
