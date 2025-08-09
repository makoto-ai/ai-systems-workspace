
# 🔄 プロジェクト復元ガイド
生成日時: 2025-08-09 09:03:26

## 📋 最新のセッション履歴

## 🔧 重要な設定ファイル
- MCP設定: .cursor/ (14個)
- 環境設定: config/ 
- システム監視: main_hybrid.py, system_monitor.py

## 🛡️ 安全な復元手順
1. `git log --oneline -10` で履歴確認
2. `git checkout <コミットハッシュ>` で状態復元
3. `python scripts/project_memory_system.py --verify` で検証

## 🚨 緊急時復元
```bash
git checkout master
python scripts/project_memory_system.py --emergency-restore
```
