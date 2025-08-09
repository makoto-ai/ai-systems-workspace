# Claude Projects: 自動構成記録用テンプレート

## 📌 プロジェクト名
ai-systems-workspace

## 🧠 構成構想
- ComposerとClaude Projectsを接続
- Cloudflare Tunnel 経由で Dify or Streamlit UI を公開
- Claudeに構成記憶を保持させ、再起動・ページ切替に備える

## 🔄 処理フロー例
1. DOI入力
2. `verify_doi.py` 実行（Composerがルーティング）
3. 結果をClaudeが要約し、構成提案
4. 原稿テンプレートをClaudeが生成

## 📊 現在の構成状況

### ✅ 実装済み機能
- **Composer設定**: `.cursor/composer.json` - task_map最適化済み
- **DOI検証**: `scripts/verify_doi.py` - CrossRef API連携済み
- **ハルシネーション検証**: `scripts/check_hallucination.py` - 動作確認済み
- **構造検証**: `scripts/validate_structure.py` - 動作確認済み
- **AIパイプライン**: `scripts/run_ai_pipeline.sh` - CI/CD統合済み

### 🔧 task_map構成
```json
{
  "doi_verification": "scripts/verify_doi.py",
  "hallucination_check": "scripts/check_hallucination.py", 
  "structure_validation": "scripts/validate_structure.py",
  "manuscript_suggestion": "claude-3-opus",
  "pipeline_trigger": "scripts/run_ai_pipeline.sh"
}
```

### 🤖 AIモデル分岐設定
- **Claude-3-Opus**: 長文要約・構成提案・原稿生成
- **GPT-4**: 構文検証・ハルシネーション検証・構造検証

## 🎯 テスト結果

### DOI検証テスト
```json
{
  "input": "10.1038/s41586-020-2649-2",
  "task": "doi_verification",
  "result": {
    "valid": true,
    "doi": "10.1038/s41586-020-2649-2",
    "title": "Array programming with NumPy",
    "authors": ["Charles R. Harris", "K. Jarrod Millman", ...],
    "published_date": [2020, 9, 17],
    "type": "journal-article"
  }
}
```

## 📝 Claudeへのプロンプト（Projects側に保持）

「この構成ログを記憶し、自動構成の一貫性を保ってください。以後、この構成をベースに再開してください。」

## 🔗 連携確認済み項目

| 項目 | 状態 | 実装方法 |
|------|------|----------|
| composer.json整備 | ✅ 完了 | task_mapを整理・Claudeルートを定義 |
| verify_doi.py完全整備 | ✅ コード完備 | DOI検証とメタデータ抽出（CrossRef API） |
| MCP-Composerルーティング確認 | ✅ 方法明示済 | taskキーに基づく処理の流れを確認 |
| Claude構成保持導線 | ✅ 指示済み | Claude Projectsに構成記録＋UI連動想定 |

## 🚀 次のステップ
1. Cloudflare Tunnel設定
2. Streamlit UI構築
3. Claude Projects連携強化
4. 自動化フロー完成
