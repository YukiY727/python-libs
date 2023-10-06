"""
金融アプリケーションのデータベースモデルを定義するモジュール
"""
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
)

from libs.utils.time_zone.time import current_japan_time

metadata = MetaData()

stock_data = Table(
    "stock_data",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("company_id", Integer, nullable=False),
    Column("source", String(255), nullable=False),
    Column("date", Date, nullable=False),
    Column("open_price", Float, nullable=False),
    Column("close_price", Float, nullable=False),
    Column("high_price", Float, nullable=False),
    Column("low_price", Float, nullable=False),
    Column("volume", Float, nullable=False),
    Column("adjusted_close_price", Float, nullable=False),
    Column("dividend", Float, nullable=False),
    Column("split_coefficient", Float, nullable=False),
    Column("created_at", DateTime, nullable=False),
)

logs = Table(
    "logs",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("timestamp", DateTime(timezone=True), default=current_japan_time()),
    Column("log_level", String(50)),
    Column("message", Text),
    Column("source", String(100), nullable=True),  # アプリケーションやソース名
    Column("thread_id", String(50), nullable=True),  # スレッドID
    Column("process_id", String(50), nullable=True),  # プロセスID
    Column("user_id", String(100), nullable=True),  # ユーザーID
    Column("session_id", String(100), nullable=True),  # セッションID
    Column("logger_name", String(100), nullable=True),  # ロガーの名前
    Column("stack_trace", Text, nullable=True),  # スタックトレース
    Column("ip_address", String(50), nullable=True),  # IPアドレス
    Column("user_agent", String(300), nullable=True),  # ユーザーエージェント
    Column("environment", String(50), nullable=True),  # 環境情報
    Column("tags", String(100), nullable=True),  # タグ
    Column("additional_data", Text, nullable=True),  # 任意の追加データ
)
