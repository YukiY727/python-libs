"""
stock_dataテーブルのリポジトリモジュール。
"""

from libs.sqlmy.database import Database
from libs.sqlmy.models import stock_data


# pylint: disable=too-few-public-methods
class StockDataRepository:
    """
    stock_dataテーブルのリポジトリクラス。
    """

    def __init__(self, database: Database):
        self.database = database
        self.table = stock_data
