"""
log_hundler.py テスト
"""

import logging

import pytest

from libs.sqlmy.database import Database
from libs.utils.logs.handler import setup_logging


class TestLogDatabase:
    """
    logをデータベースに書き込むテスト
    """

    def test_log_database(self, db_instance: Database):
        """
        logのmessageがデータベースに書き込まれることを確認する
        """
        logger = setup_logging(db_instance)
        logger.info("test")
        db_instance.connect()
        db_instance.start_transaction()
        result = db_instance.execute_query("SELECT * FROM logs")
        assert result[0].message == "test"

    @pytest.mark.parametrize(
        "level,message",
        [
            (logging.DEBUG, "This is a debug message"),
            (logging.INFO, "This is an info message"),
            (logging.WARNING, "This is a warning message"),
            (logging.ERROR, "This is an error message"),
            (logging.CRITICAL, "This is a critical message"),
        ],
    )
    def test_log_levels(self, db_instance: Database, level, message):
        """
        logのlevelがデータベースに書き込まれることを確認する
        """
        logger = setup_logging(db_instance)
        logger.setLevel(level)
        logger.log(level, message)

        db_instance.start_transaction()
        query = "SELECT log_level FROM logs WHERE message = :message"
        result = db_instance.execute_query(query, message=message)

        assert result[0].log_level == logging.getLevelName(level)
