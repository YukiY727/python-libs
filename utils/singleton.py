"""
thread safeなsingletonのクラスを作成するためのメタクラス
cls._lock = threading.Lock() の部分は、このシングルトンメタクラスを使って新しいクラスを作成するたびに、
そのクラスにロックオブジェクトをアタッチしています。このロックは、
複数のスレッドが同時にシングルトンインスタンスを作成しようとしたときの競合を避けるために使われます。

シングルトンパターンは、あるクラスのインスタンスが1つしか存在しないことを保証するデザインパターンです。
しかし、マルチスレッド環境では、2つのスレッドがほぼ同時にシングルトンインスタンスの作成を試みると、
意図せず2つの異なるインスタンスが作成される可能性があります。

この問題を防ぐために、スレッドセーフなシングルトンの実装では、インスタンスの作成をロックを使って同期化します。
具体的には、インスタンスがまだ存在しないときにのみ新しいインスタンスを作成する部分を
ロックで囲むことで、一度に1つのスレッドだけがその部分のコードを実行できるようにします。
"""
import threading


class SingletonMeta(type):
    """Thread-safeなシングルトンメタクラス"""

    _instances: dict = {}

    def __init__(cls, *args, **kwargs):
        """クラスの初期化時にロックを設定"""
        super().__init__(*args, **kwargs)
        cls._lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        """
        インスタンスが存在しない場合はインスタンスを作成し、
        存在する場合は既存のインスタンスを返す。
        """
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
