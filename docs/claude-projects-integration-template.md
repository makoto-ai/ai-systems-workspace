# Claude Projects: 自動構成記録用テンプレート

## 📌 プロジェクト名
voice-roleplay-system

## 🧠 構成構想
- ComposerとClaude Projectsを接続
- Cloudflare Tunnel 経由で Dify or Streamlit UI を公開
- Claudeに構成記憶を保持させ、再起動・ページ切替に備える

## 🔄 処理フロー例
1. DOI入力
2. `verify_doi.py` 実行（Composerがルーティング）
3. 結果をClaudeが要約し、構成提案
4. 原稿テンプレートをClaudeが生成

## 📋 実装済みコンポーネント

### ✅ Composer設定
- `.cursor/composer.json` に `task_map` を追加
- DOI検証: `scripts/verify_doi.py`
- 幻覚チェック: `scripts/check_hallucination.py`
- 構造検証: `scripts/validate_structure.py`
- 原稿提案: `claude-3-opus`

### ✅ パイプライン実行
- `scripts/run_pipeline.sh` でタスク実行
- ログ出力とエラーハンドリング
- タイムアウト設定（30秒）

### ✅ MCP統合テスト
- `scripts/test_mcp_composer_integration.py`
- task_map検証
- DOI検証テスト
- パイプライン実行テスト
- MCP統合テスト

## 🎯 Claudeへの指示プロンプト

```
この構成ログを記憶し、自動構成の一貫性を保ってください。
以後、この構成をベースに再開してください。

現在のシステム構成：
- Composer: .cursor/composer.json でタスクマッピング
- MCP: scripts/run_pipeline.sh でパイプライン実行
- DOI検証: scripts/verify_doi.py でCrossRef API使用
- テスト: scripts/test_mcp_composer_integration.py で統合テスト

利用可能なタスク：
- doi_verification <doi>
- hallucination_check <text>
- structure_validation <file>
- quality_analysis
- security_scan
- performance_test
```

## 🔧 テスト実行コマンド

```bash
# MCP-Composer連携テスト
python3 scripts/test_mcp_composer_integration.py

# DOI検証テスト
python3 scripts/verify_doi.py 10.1038/s41586-020-2649-2

# パイプライン実行テスト
./scripts/run_pipeline.sh doi_verification 10.1038/s41586-020-2649-2
```

## 📊 期待される結果

### MCPリクエスト例
```json
{
  "input": "10.1038/s41586-020-2649-2",
  "task": "doi_verification"
}
```

### ルーティング結果
```
doi_verification → scripts/verify_doi.py
```

### 出力例
```json
{
  "valid": true,
  "doi": "10.1038/s41586-020-2649-2",
  "title": "論文タイトル",
  "authors": ["著者名"],
  "published_date": [2020],
  "verified_at": "2025-01-XX..."
}
```

## 🚀 次のステップ

1. **Cloudflare Tunnel設定**
   - Dify/Streamlit UIの公開
   - セキュリティ設定

2. **Claude Projects連携**
   - 構成記憶の永続化
   - 自動再開機能

3. **UI統合**
   - フロントエンド開発
   - リアルタイム更新

## 📝 注意事項

- すべてのスクリプトは `chmod +x` で実行権限を付与
- ログファイルは `logs/` ディレクトリに保存
- タイムアウトは30秒に設定
- エラーハンドリングは全スクリプトに実装済み 