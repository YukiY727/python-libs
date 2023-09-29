"""
pandasとsqlの型を変換するモジュール。
"""


def convert_sql_type_to_pd_type(sql_type: str) -> str:
    """
    sqlの型をpandasの型に変換する。

    Args:
        sql_type (str): sqlの型

    Returns:
        str: pandasの型

    Raises:
        ValueError: サポートされていないsqlの型の場合
    """
    if sql_type == "INTEGER":
        return "Int64"
    if sql_type == "FLOAT":
        return "float64"
    if sql_type == "DATETIME":
        return "datetime64"
    if sql_type == "VARCHAR":
        return "object"
    raise ValueError(f"Unsupported sql type: {sql_type}")
