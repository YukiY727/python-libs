"""
stock_dataテーブルのリポジトリモジュール。
"""

from sqlmy.database import Database
from sqlmy.models import logs


# pylint: disable=too-few-public-methods
class LogDataRepository:
    """
    stock_dataテーブルのリポジトリクラス。
    """

    def __init__(self, database: Database):
        self.database = database
        self.table = logs
