# コントリビューターガイド

## 👋 ようこそ！

このプロジェクトに参加していただき、ありがとうございます。このガイドは、新しいコントリビューターがプロジェクトに参加する際の手順とルールを説明します。

## 📋 目次

1. [プロジェクト概要](#プロジェクト概要)
2. [開発環境セットアップ](#開発環境セットアップ)
3. [コーディング規約](#コーディング規約)
4. [貢献の流れ](#貢献の流れ)
5. [品質管理](#品質管理)
6. [セキュリティ](#セキュリティ)
7. [トラブルシューティング](#トラブルシューティング)

## 🎯 プロジェクト概要

### プロジェクトの目的
- 研究論文からYouTube動画用原稿を自動生成するAIシステム
- 論文の信頼性確保と品質管理の自動化
- 教育コンテンツ制作の効率化

### 主要技術スタック
- **Python 3.8+**: メイン開発言語
- **Streamlit**: Web UI
- **OpenAI/Claude API**: AI機能
- **MCP**: AI連携プロトコル

## 🛠️ 開発環境セットアップ

### 前提条件
- Python 3.8以上
- Git
- テキストエディタ（VS Code推奨）

### 1. リポジトリのクローン
```bash
git clone https://github.com/your-username/ai-systems-workspace.git
cd ai-systems-workspace
```

### 2. 仮想環境の作成
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate  # Windows
```

### 3. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定
```bash
cp env.example .env
# .envファイルを編集してAPIキーを設定
```

### 5. データベースの初期化
```bash
python -c "from database import init_db; init_db()"
```

### 6. システムの起動確認
```bash
python streamlit_app.py
```

## 📝 コーディング規約

### Python規約
- **PEP 8**: Python公式スタイルガイドに準拠
- **型ヒント**: 必須（`typing`モジュール使用）
- **ドキュメント文字列**: 全ての関数・クラスに必須

### 命名規則
```python
# クラス名: PascalCase
class YouTubeScriptGenerator:
    pass

# 関数・変数名: snake_case
def generate_script():
    pass

# 定数: UPPER_SNAKE_CASE
MAX_RETRIES = 3
```

### ファイル構造
```
project/
├── scripts/           # 自動化スクリプト
├── docs/             # ドキュメント
├── config/           # 設定ファイル
├── logs/             # ログファイル
├── tests/            # テストファイル
└── modules/          # モジュール
```

### コメント規約
```python
def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    データを処理して結果を返す
    
    Args:
        data: 処理対象のデータ
        
    Returns:
        処理結果のデータ
        
    Raises:
        ValueError: データ形式が不正な場合
    """
    # 処理ロジック
    pass
```

## 🔄 貢献の流れ

### 1. イシューの作成
- バグ報告や機能要望はGitHub Issuesで作成
- イシューテンプレートを使用
- 詳細な説明と再現手順を記載

### 2. ブランチの作成
```bash
git checkout -b feature/your-feature-name
# または
git checkout -b fix/your-bug-fix
```

### 3. 開発・テスト
```bash
# テストの実行
python -m pytest tests/

# 品質チェック
python scripts/check_hallucination.py
python scripts/validate_structure.py
```

### 4. コミット
```bash
git add .
git commit -m "feat: 新機能の追加"
git commit -m "fix: バグ修正"
git commit -m "docs: ドキュメント更新"
```

### 5. プルリクエスト
- 詳細な説明を記載
- 関連するイシューをリンク
- レビュアーを指定

## ✅ 品質管理

### テスト要件
- **単体テスト**: 全ての関数に必須
- **統合テスト**: API連携部分
- **品質テスト**: 生成された原稿の品質

### テスト実行
```bash
# 全テスト実行
python -m pytest

# 特定のテスト実行
python -m pytest tests/test_script_generation.py

# カバレッジ確認
python -m pytest --cov=.
```

### 品質チェック
```bash
# コード品質チェック
python scripts/quality_metrics.py

# セキュリティチェック
python scripts/security_check.py

# パフォーマンスチェック
python scripts/performance_test.py
```

## 🔒 セキュリティ

### APIキー管理
- **絶対にコミットしない**: APIキーは`.env`ファイルに保存
- **環境変数使用**: 本番環境では環境変数を使用
- **定期的な更新**: APIキーは定期的に更新

### データ保護
```python
# 機密データの暗号化
from cryptography.fernet import Fernet

def encrypt_sensitive_data(data: str) -> bytes:
    key = Fernet.generate_key()
    f = Fernet(key)
    return f.encrypt(data.encode())
```

### 入力値検証
```python
def validate_input(data: Dict) -> bool:
    """入力値の検証"""
    required_fields = ['title', 'content']
    return all(field in data for field in required_fields)
```

## 🐛 トラブルシューティング

### よくある問題

#### 1. 依存関係のエラー
```bash
# 解決方法
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

#### 2. APIキーエラー
```bash
# 確認方法
python -c "import os; print(os.getenv('OPENAI_API_KEY'))"
```

#### 3. データベースエラー
```bash
# 再初期化
python -c "from database import reset_db; reset_db()"
```

### ログの確認
```bash
# ログファイルの確認
tail -f logs/system_monitor.log
tail -f logs/error_handler.log
```

### デバッグモード
```bash
# デバッグモードで起動
DEBUG_MODE=true python streamlit_app.py
```

## 📚 学習リソース

### 必須読書
- [Python公式ドキュメント](https://docs.python.org/)
- [Streamlit公式ガイド](https://docs.streamlit.io/)
- [OpenAI APIドキュメント](https://platform.openai.com/docs)

### 推奨ツール
- **VS Code**: 推奨エディタ
- **Postman**: APIテスト
- **Docker**: 環境統一

### コミュニティ
- **GitHub Discussions**: 技術的な質問
- **Slack**: リアルタイムコミュニケーション
- **定期ミーティング**: 週次進捗確認

## 🎯 貢献の種類

### コード貢献
- バグ修正
- 新機能開発
- パフォーマンス改善
- セキュリティ強化

### ドキュメント貢献
- README更新
- API仕様書作成
- チュートリアル作成
- 翻訳

### テスト貢献
- テストケース追加
- 品質改善
- 自動化スクリプト

### デザイン貢献
- UI/UX改善
- ユーザビリティ向上
- アクセシビリティ対応

## 🏆 貢献者向け特典

### 認証システム
- 貢献度に応じたバッジ
- プロフィールページでの表示
- 特別なアクセス権限

### 学習機会
- 技術勉強会への参加
- カンファレンス参加支援
- 書籍購入支援

## 📞 サポート

### 質問・相談
- **技術的な質問**: GitHub Issues
- **緊急時**: Slack #emergency
- **一般的な質問**: GitHub Discussions

### メンター制度
- 経験豊富な開発者がサポート
- 1on1ミーティング
- コードレビュー

---

## 📋 チェックリスト

### 初回セットアップ
- [ ] リポジトリのクローン
- [ ] 仮想環境の作成
- [ ] 依存関係のインストール
- [ ] 環境変数の設定
- [ ] システムの起動確認

### 開発開始前
- [ ] イシューの作成
- [ ] ブランチの作成
- [ ] 開発環境の確認

### プルリクエスト前
- [ ] テストの実行
- [ ] 品質チェック
- [ ] ドキュメント更新
- [ ] レビュー依頼

---

*最終更新: 2025年1月*

**質問や提案があれば、お気軽にお声がけください！** 🚀
