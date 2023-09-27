"""
databaseを管理するモジュール。
"""
from sqlalchemy import (
    Connection,
    MetaData,
    Transaction,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.exc import SQLAlchemyError

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
        """
        self.metadata = metadata
        self.engine = create_engine(engine_url)
        self.connection: Connection | None = None
        self.trans: list[Transaction] = []
        self.initialized = False

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
        """
        if self.connection:
            self.connection.close()
            self.connection = None
            self.initialized = False

    def create_tables(self):
        """
        初期化されていない場合、初期化し、テーブルを作成する。
        """
        if not self.initialized:
            self.connect()
        self.metadata.create_all(self.engine)

    def start_transaction(self):
        """
        トランザクションを開始する。すでにトランザクションが開始されている場合は何もしない。
        """
        if not self.initialized:
            self.connect()
        if not self.trans:
            self.trans.append(self.connection.begin())

    def start_nested_transaction(self):
        """
        ネストされたトランザクションを開始する。接続が初期化されていない場合はエラーを出す。
        """
        if not self.initialized:
            raise SQLAlchemyError("Connection is not initialized.")
        self.trans.append(self.connection.begin_nested())

    def commit_transaction(self):
        """
        現在のトランザクションをコミットする。トランザクションが開始されていない場合はエラーを出す。

        Raises:
            SQLAlchemyError: トランザクションが開始されていない場合
        """
        if not self.trans:
            raise SQLAlchemyError("Transaction is not started.")
        current_trans = self.trans.pop()
        current_trans.commit()

    def rollback_transaction(self):
        """
        現在のトランザクションをロールバックする。トランザクションが開始されていない場合はエラーを出す。

        Raises:
            SQLAlchemyError: トランザクションが開始されていない場合
        """
        if not self.trans:
            raise SQLAlchemyError("Transaction is not started.")
        current_trans = self.trans.pop()
        current_trans.rollback()

    def execute_query(self, query: str, **params):
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
            raise SQLAlchemyError("Connection is not initialized.")

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

    def __del__(self):
        """
        オブジェクトが破棄される前にデータベース接続を切断する。
        """
        self.disconnect()