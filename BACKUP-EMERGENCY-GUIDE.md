# 🚨 バックアップ緊急復旧ガイド

## 🎯 概要

このガイドは**論文検索システム**を含むプロジェクト全体の完全復旧手順を記載しています。
**不完全バックアップ防止システム**により、データ損失リスクを最小化していますが、緊急時の手順を明記します。

## 📋 バックアップ検証システム

### ✅ 完全性チェック項目

| 項目 | 最小要件 | 検証方法 |
|------|----------|----------|
| 論文システムサイズ | 50MB以上 | `du -sm paper_research_system` |
| 重要ファイル | 6ファイル | 個別存在確認 |
| 仮想環境 | NumPy/SciPy/NetworkX | `import`テスト |
| データベース | 実データ付き | `citation_graph.db`サイズ |

### 🛡️ 自動防止機能

```bash
# バックアップ前の自動検証
./backup-verify.sh  # 合格しないとバックアップ中止

# 検証付きバックアップ実行
./auto-save.sh "メッセージ"  # 3段階検証付き
```

## 🔧 緊急復旧手順

### 📥 **Method 1: GitHubからの復旧**

```bash
# 1. 最新版をクローン
git clone https://github.com/makoto-ai/voice-roleplay-system.git
cd voice-roleplay-system
git checkout hallucination-elimination-system

# 2. 論文システム確認
cd paper_research_system
./run.sh  # 自動で仮想環境構築

# 3. 動作テスト
python main_citation_network.py analyze -a "test_network"
```

### 📦 **Method 2: tar.gz圧縮ファイルからの復旧**

```bash
# 1. 圧縮ファイルから展開
tar -xzf paper_research_system_backup_YYYYMMDD_HHMMSS.tar.gz

# 2. 論文システム確認
cd /Users/araimakoto/ai-driven/ai-systems-workspace/paper_research_system
source .venv/bin/activate

# 3. 動作テスト
python main_integrated.py "sales psychology" --save-obsidian
```

### 🔄 **Method 3: Obsidianからの部分復旧**

```bash
# 論文データのみ復旧
~/Desktop/Obsidian-Complete-Backup/  # 3.8GBの完全バックアップ
```

## 🧪 復旧後の検証手順

### 1️⃣ **基本動作確認**

```bash
# 検証スクリプト実行
./backup-verify.sh

# 論文検索テスト
cd paper_research_system
./run.sh
python main_integrated.py "test query" --max-papers 3
```

### 2️⃣ **高度機能確認**

```bash
# 引用ネットワーク分析
python main_citation_network.py build "test" --max-papers 3 --max-depth 1
python main_citation_network.py visualize -a "test"

# Obsidian連携確認
python main_integrated.py "business" --save-obsidian
```

### 3️⃣ **データベース整合性確認**

```bash
# データベースファイル確認
ls -lah database/
# citation_graph.db: 200KB以上
# search_history.db: 存在確認

# SQLiteデータ確認
sqlite3 database/citation_graph.db ".tables"
sqlite3 database/citation_graph.db "SELECT COUNT(*) FROM papers;"
```

## 🚨 トラブルシューティング

### ❌ **Issue: 仮想環境エラー**

```bash
# 仮想環境再構築
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### ❌ **Issue: NumPy/SciPyエラー**

```bash
# 依存関係再インストール
pip install --upgrade numpy scipy networkx
python -c "import numpy, scipy, networkx; print('✅ All OK')"
```

### ❌ **Issue: データベース破損**

```bash
# データベース再構築
rm database/citation_graph.db
python main_citation_network.py build "test" --max-papers 5
```

## 📞 緊急時連絡先

- **GitHub Repository**: https://github.com/makoto-ai/voice-roleplay-system
- **バックアップブランチ**: `hallucination-elimination-system`
- **ローカルバックアップ**: `~/paper_research_system_backup_*.tar.gz`

## 🎯 予防措置

### 📅 **定期バックアップ**

```bash
# 毎回のコミット前に自動検証
./auto-save.sh "定期バックアップ"

# 週次フルバックアップ
tar -czf ~/weekly_backup_$(date +%Y%m%d).tar.gz .
```

### 🔍 **定期検証**

```bash
# 月次検証
./backup-verify.sh
./test-incomplete-backup.sh  # 防止機能テスト
```

---

**⚠️ 重要**: このシステムは**完全性検証機能**により、不完全なバックアップを自動的に阻止します。
**エラー0件**の状態でのみバックアップが実行されるため、データ損失リスクは最小化されています。