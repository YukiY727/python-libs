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
)

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

# 他にも必要なテーブル定義をここに追加する
