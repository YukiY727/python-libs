"""
時間に関するユーティリティ
"""
from datetime import datetime

import pytz


def current_japan_time():
    """
    現在の日本時間を返す
    """
    return datetime.now(pytz.timezone("Asia/Tokyo"))
