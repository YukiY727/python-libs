"""
db_factory.pyのテスト
"""
from libs.sqlmy.database import Database
from libs.sqlmy.db_factory import RepositoryFactory


class TestDbFactory:
    """
    DbFactoryクラスのテストクラス。
    """

    def test_get_repository(self, db_instance: Database):
        """
        get_repositoryメソッドのテストメソッド。
        """
        factory = RepositoryFactory(db_instance)
        repo = factory.get_repository("stock_data")
        assert repo.database == db_instance
        assert repo.table.name == "stock_data"

    def test_get_repository_with_invalid_table_name(self, db_instance):
        """
        存在しないテーブル名を指定した場合、ValueErrorが発生することを
        確認するテストメソッド。
        """
        factory = RepositoryFactory(db_instance)
        try:
            factory.get_repository("invalid_table_name")
        except ValueError as error:
            assert (
                str(error)
                == "No repository found for table: invalid_table_name"
            )
