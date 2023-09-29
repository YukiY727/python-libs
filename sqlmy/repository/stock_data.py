"""
stock_dataテーブルのリポジトリモジュール。
"""

from sqlmy.database import Database
from sqlmy.models import stock_data


# pylint: disable=too-few-public-methods
class StockDataRepository:
    """
    stock_dataテーブルのリポジトリクラス。
    """

    def __init__(self, database: Database):
        self.database = database
        self.table = stock_data
