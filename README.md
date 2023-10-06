````
# libs

`libs`はデータベース操作やユーティリティ関数を提供するPythonライブラリです。

## 機能

- SQLデータベースとの連携機能。
- 日付や時間に関するユーティリティ関数。
- データ変換ユーティリティ。

## インストール方法

Poetryを使用してプロジェクトに`libs`を追加:

\```bash
poetry add git+https://github.com/YukiY727/python-libs@HEAD
\```

## 使用方法

### データベース接続

\```python
from libs.sqlmy.database import Database
# ...（使用例）
\```

### ユーティリティ関数

\```python
from libs.utils.time_zone import convert_to_jst
# ...（使用例）
\```

## コントリビューション

バグの報告や新機能の提案など、プロジェクトへの貢献を歓迎します！
GitHubのIssueやPull Requestを通じてフィードバックや提案をお寄せください。

## ライセンス

このプロジェクトはMITライセンスのもとで公開されています。詳細は`LICENSE`ファイルを参照してください。
````
