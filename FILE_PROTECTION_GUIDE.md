# 🛡️ 重要ファイル完全保護システム

**絶対に重要ファイルを削除させない安全システム**

---

## 🚨 緊急時の対応

### **ファイルが削除された場合**
```bash
# 即座に緊急復旧システムを実行
./EMERGENCY_RECOVERY.sh
```

### **削除前の安全確認**
```bash
# 安全削除スクリプトを使用（推奨）
./safe-delete.sh ファイル名

# 例：キャッシュファイル削除
./safe-delete.sh __pycache__/ *.pyc
```

---

## 🛡️ 保護システムの機能

### **完全保護対象**
- **Pythonファイル**: `*.py` (メインシステム)
- **データベース**: `*.db`, `*.sql` (蓄積データ)
- **設定ファイル**: `*.json`, `*.yaml`, `*.toml`
- **ドキュメント**: `*.md`, `*.txt`
- **依存関係**: `requirements.txt`, `package.json`
- **Git**: `.git/`, `.gitignore`
- **仮想環境**: `.venv/`, `venv/`
- **Obsidian**: `obsidian-knowledge/`, `.obsidian/`

### **削除許可ファイル（安全）**
- **キャッシュ**: `__pycache__/`, `*.pyc`
- **一時ファイル**: `.DS_Store`, `*.tmp`, `*.log`
- **バックアップ**: `*.bak`, `*.backup`

---

## 📋 基本的な使い方

### **1. 保護システム状態確認**
```bash
python3 CRITICAL_FILE_PROTECTION.py status
```

### **2. 安全削除**
```bash
# 推奨方法
./safe-delete.sh 削除対象

# 直接実行
python3 CRITICAL_FILE_PROTECTION.py safe-rm 削除対象
```

### **3. 緊急復旧**
```bash
# 対話式復旧
./EMERGENCY_RECOVERY.sh

# 特定ファイル復旧
python3 CRITICAL_FILE_PROTECTION.py restore ファイル名
```

---

## ⚙️ 保護設定のカスタマイズ

### **設定ファイル**: `PROTECTION_CONFIG.json`

```json
{
  "protection_enabled": true,          // 保護有効/無効
  "backup_before_any_operation": true, // 操作前自動バックアップ
  "require_confirmation": true,        // 削除前確認
  "log_all_operations": true          // 全操作ログ記録
}
```

### **保護対象を追加**
```json
{
  "critical_files": [
    "**/*.py",              // 既存
    "**/*.custom",          // 追加したい拡張子
    "**/重要フォルダ/**"      // 追加したいフォルダ
  ]
}
```

---

## 🔍 システムの動作原理

### **1. 削除前チェック**
1. 対象ファイルが重要ファイルパターンに合致するかチェック
2. 削除許可リストに含まれるかチェック  
3. 重要ファイルの場合は削除をブロック

### **2. 自動バックアップ**
- 任意の操作前に自動でバックアップ作成
- `.critical_backups/` ディレクトリに保存
- タイムスタンプ付きファイル名で管理

### **3. ログ記録**
- 全ての操作を `protection_system.log` に記録
- 削除ブロック、バックアップ作成、復旧を追跡

---

## 🎯 実際の使用例

### **キャッシュファイル削除**
```bash
# 安全に削除
./safe-delete.sh __pycache__/

# 出力例：
🛡️ [INFO] バックアップ作成: __pycache__ → .critical_backups/__pycache___20250802_221530.backup
✅ 削除完了: __pycache__/
```

### **誤って重要ファイルを削除しようとした場合**
```bash
./safe-delete.sh main_fact_check.py

# 出力例：
🚫 BLOCKED: DELETE on critical file: main_fact_check.py
🚫 削除がブロックされました！
重要ファイル:
  - main_fact_check.py
```

### **緊急復旧**
```bash
./EMERGENCY_RECOVERY.sh

# 対話式メニューで復旧選択
```

---

## 🚀 保護システムの利点

### **✅ 完全保護**
- 重要ファイルは絶対に削除されない
- 間違った削除コマンドから完全保護
- システム全体の整合性維持

### **⚡ 即座復旧**
- 自動バックアップで即座復旧可能
- 削除前の状態に完全復元
- データ損失ゼロ

### **🔍 完全透明性**
- 全操作のログ記録
- どのファイルが保護されているか明確
- バックアップ状況の完全把握

---

## 💡 重要な注意事項

### **必ず使用すべき場面**
- **任意のファイル削除時**
- **ディレクトリクリーンアップ時**
- **システムメンテナンス時**

### **緊急時の連絡手順**
1. `./EMERGENCY_RECOVERY.sh` 実行
2. 利用可能バックアップ確認
3. 適切なバックアップから復旧

---

## 🎉 まとめ

**このシステムにより：**
- ✅ 重要ファイルは絶対に削除されません
- ✅ 万が一の場合も即座に復旧可能
- ✅ 全ての操作が記録・追跡されます
- ✅ 安心してシステム操作が可能

**今後は `./safe-delete.sh` のみを使用してください！**