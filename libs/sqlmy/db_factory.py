"""
Databaseクラスを受け取り、リポジトリを返すファクトリクラス
のモジュール。
"""

from libs.sqlmy.database import Database
from libs.sqlmy.repository.log_data import LogDataRepository
from libs.sqlmy.repository.stock_data import StockDataRepository


# pylint: disable=too-few-public-methods
class RepositoryFactory:
    """
    Databaseクラスを受け取り、リポジトリを返すファクトリクラス。
    """

    def __init__(self, database: Database):
        self.database = database
        self.repositories = {
            "stock_data": StockDataRepository(self.database),
            "log_data": LogDataRepository(self.database),
            # 他のテーブルのリポジトリもここに追加できます。
        }

    def get_repository(self, table_name: str):
        """
        table_nameに対応するリポジトリを返す。

        Args:
            table_name (str): テーブル名

        Returns:
            Repository: リポジトリ

        Raises:
            ValueError: テーブル名に対応するリポジトリが存在しない場合
        """
        repo = self.repositories.get(table_name)
        if not repo:
            raise ValueError(f"No repository found for table: {table_name}")
        return repo
