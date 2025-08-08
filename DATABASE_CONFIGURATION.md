# 🗄️ データベースファイル設定ガイド

このドキュメントは、Cursorで「バイナリファイル」警告を解消するための設定ガイドです。

## 📋 問題の説明

Cursorがデータベースファイル（`.db`、`.sqlite`）をテキストエディタで開こうとして警告を表示する問題を解決します。

## ✅ 実装済み解決策

### 1. 🔧 .gitattributes設定
```
*.db binary
*.sqlite binary
*.sqlite3 binary
```

### 2. 📁 .gitignore例外設定
```
# Data files
*.db
*.sqlite
*.sqlite3

# Exception: Keep paper research system databases  
!paper_research_system/database/*.db
```

### 3. 🎯 Cursor設定 (.vscode/settings.json)
```json
{
  "files.associations": {
    "*.db": "binary",
    "*.sqlite": "binary",
    "*.sqlite3": "binary"
  },
  "workbench.editorAssociations": {
    "*.db": "default",
    "*.sqlite": "default", 
    "*.sqlite3": "default"
  },
  "files.readonlyInclude": {
    "**/*.db": true,
    "**/*.sqlite": true,
    "**/*.sqlite3": true
  },
  "search.exclude": {
    "**/*.db": true,
    "**/*.sqlite": true,
    "**/*.sqlite3": true
  }
}
```

## 📊 データベースファイル情報

### citation_graph.db
- **サイズ**: 156KB (最適化済み)
- **テーブル**: 4個（空テーブル削除済み）
- **内容**: 論文引用ネットワークデータ

### search_history.db  
- **サイズ**: 252KB
- **テーブル**: 5個
- **内容**: 検索履歴・統計データ

## 🛠️ トラブルシューティング

### Cursorで警告が表示される場合

1. **Cursorを再起動**してください
2. **設定の再読み込み**: `Cmd+Shift+P` → "Reload Window"
3. **ファイルタイプの確認**: データベースファイルを右クリック → "Open With" → "Binary Editor"

### 設定が反映されない場合

1. `.vscode/settings.json`の設定を確認
2. プロジェクトを閉じて再度開く
3. Cursor本体の設定で`files.associations`を確認

## ✅ 確認方法

```bash
# ファイルタイプ確認
file paper_research_system/database/*.db

# Git属性確認  
git check-attr binary paper_research_system/database/*.db
```

## 📝 注意事項

- データベースファイルは**バイナリファイル**として扱われます
- テキストエディタでの編集は**禁止**されます
- SQLiteツールまたはプログラムからのみアクセス可能です
- 重要なデータが含まれているため、**削除しないでください**

---

**🎯 この設定により、Cursorでのデータベースファイル警告が完全に解消されます。**