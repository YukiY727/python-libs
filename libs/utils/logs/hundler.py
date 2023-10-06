"""
logをデータベースに書き込むモジュール
"""
import logging

from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from libs.sqlmy.database import Database
from libs.utils.time_zone.time import current_japan_time


class DatabaseLogHandler(logging.Handler):
    """
    logをデータベースに書き込むハンドラ
    """

    def __init__(self, database: Database):
        super().__init__()
        self.database = database

    def emit(self, record: logging.LogRecord):
        """
        logをデータベースに書き込む

        Args:
            record (logging.LogRecord): ログレコード

        Raises:
            Exception: データベースへの書き込みに失敗した場合
        """
        # ログメッセージをフォーマット
        log_entry = self.format(record)
        timestamp = current_japan_time()

        # ログエントリをデータベースに書き込む
        try:
            self.database.connect()
            self.database.start_transaction()
            query = """
            INSERT INTO logs (
                timestamp, log_level, message, logger_name, stack_trace
            )
            VALUES (
                :timestamp, :log_level, :message, :logger_name, :stack_trace
            )
            """
            self.database.execute_query(
                query,
                timestamp=timestamp,
                log_level=record.levelname,
                message=log_entry,
                logger_name=record.name,
                stack_trace=record.exc_text,  # 例外のスタックトレース
            )
            self.database.commit_transaction()
            self.database.disconnect()
        # except Exception:
        #     self.handleError(record)
        except IntegrityError:
            self.handleError(record)
        except OperationalError:
            self.handleError(record)
        except SQLAlchemyError:
            self.handleError(record)


# ログハンドラとロガーのセットアップ
def setup_logging(database: Database) -> logging.Logger:
    """
    loggingモジュールの設定を行う

    Args:
        database (Database): データベースインスタンス

    Returns:
        logger (Logger): ロガー
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    handler = DatabaseLogHandler(database)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
