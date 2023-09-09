"""
singleton.pyのテスト
"""
import threading
import time

from utils.singleton import SingletonMeta


class TestSingleton:
    """シングルトンのテスト"""

    # pylint: disable=too-few-public-methods
    class SingletonClass(metaclass=SingletonMeta):
        """test用のシングルトンクラス"""

        def __init__(self):
            self.value = 0

    # pylint: enable=too-few-public-methods
    def test_singleton_meta(self):
        """シングルトンメタクラスのテスト"""
        # インスタンスを2つ作成
        instance1 = self.SingletonClass()
        instance2 = self.SingletonClass()

        # 両方のインスタンスが同一であることを確認
        assert instance1 is instance2

        # インスタンスの属性を変更し、もう一方のインスタンスの属性も変わっていることを確認
        instance1.value = 10
        assert instance2.value == 10

    def test_singleton_thread_safety(self):
        """スレッドセーフなシングルトンのテスト"""

        # pylint: disable=too-few-public-methods
        class ThreadSafeSingletonClass(metaclass=SingletonMeta):
            """test用のスレッドセーフなシングルトンクラス"""

            def __init__(self):
                # `time.sleep(0.1)` はここでの重要な役割を果たします。具体的には、
                # この遅延は複数のスレッドがほぼ同時にシングルトンのインスタンスを生成しようとするシナリオをシミュレートするためのものです。
                # スレッドセーフティの保証は、多くの場面で非常に短い時間窓内での同時アクセスが問題となるため、このようなシミュレーションは非常に重要です。
                # この`sleep`がない場合、テスト中のすべてのスレッドが非常に迅速に完了してしまい、実際の多重アクセスシナリオを正確に反映しない可能性があります。
                # したがって、この遅延は、ロックメカニズムが実際の同時アクセスシナリオで正しく動作することを確認するために意図的に追加されています。
                time.sleep(0.1)
                self.value = 0

        # pylint: enable=too-few-public-methods
        instances = []

        def create_instance():
            instance = ThreadSafeSingletonClass()
            instances.append(instance)

        # 複数のスレッドで同時にインスタンスを作成する
        threads = [threading.Thread(target=create_instance) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # すべてのインスタンスが同一であることを確認
        for instance in instances[1:]:
            assert instances[0] is instance
