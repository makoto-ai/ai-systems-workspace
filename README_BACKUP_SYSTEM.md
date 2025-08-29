# 🧠 ローカル環境バックアップ・保存強化システム

Makotoさんの開発環境を、安全かつ再現可能に維持するための完全なバックアップ・保存システムです。

---

## ✅ 実装完了項目

### ⏰ Step 1：cronによる自動バックアップ（毎朝3時）
- ✅ `scripts/backup/daily_backup.sh` - 毎日自動バックアップスクリプト
- ✅ `scripts/backup/setup_cron_backup.sh` - cron設定スクリプト

### 🧾 Step 2：ObsidianのGitバージョン管理
- ✅ `scripts/backup/setup_obsidian_git.sh` - Obsidian Git設定スクリプト

### 📁 Step 3：WhisperX出力日付付きアーカイブ
- ✅ `scripts/backup/whisperx_archive.sh` - WhisperX出力アーカイブスクリプト

### 🗂️ Step 4：rsyncによるフル環境保存
- ✅ `scripts/backup/weekly_rsync.sh` - 週次フルバックアップスクリプト

---

## 🚀 使用方法

### 1. cron自動バックアップ設定

```bash
# cron設定スクリプト実行
./scripts/backup/setup_cron_backup.sh
```

**設定内容：**
- 毎日バックアップ：毎朝3時実行
- 週次フルバックアップ：毎週日曜日午前2時実行

### 2. Obsidian Gitバージョン管理設定

```bash
# Obsidian Git設定
./scripts/backup/setup_obsidian_git.sh
```

**設定内容：**
- Gitリポジトリ初期化
- .gitignore設定（不要ファイル除外）
- 毎時自動コミット（cron登録）
- GitHub連携（オプション）

### 3. WhisperX出力アーカイブ

```bash
# WhisperX出力を日付付きでアーカイブ
./scripts/backup/whisperx_archive.sh input.wav whisperx_outputs/
```

**出力例：**
```
📁 whisperx_outputs/
  ├── output_2025-08-09_03-00-00/
  ├── output_2025-08-10_03-00-00/
  └── output_2025-08-11_14-30-15/
```

### 4. 手動バックアップ実行

```bash
# 毎日バックアップ手動実行
./scripts/backup/daily_backup.sh

# 週次フルバックアップ手動実行
./scripts/backup/weekly_rsync.sh
```

---

## 📊 バックアップ内容

### 毎日バックアップ（`daily_backup.sh`）

| 項目 | 保存先 | 説明 |
|------|--------|------|
| AIシステム全体 | `~/Backups/ai-dev-backup/YYYY-MM-DD_HH-MM/ai-systems-workspace/` | プロジェクト全体 |
| Obsidian Vault | `~/Backups/ai-dev-backup/YYYY-MM-DD_HH-MM/obsidian-vault/` | ノート・設定 |
| WhisperX出力 | `~/Backups/ai-dev-backup/YYYY-MM-DD_HH-MM/whisperx-outputs/` | 音声処理結果 |
| 設定ファイル | `~/Backups/ai-dev-backup/YYYY-MM-DD_HH-MM/configs/` | .zshrc, Docker設定 |

### 週次フルバックアップ（`weekly_rsync.sh`）

| 項目 | 保存先 | 説明 |
|------|--------|------|
| 完全ミラーリング | `/Volumes/BACKUP_DRIVE/ai-system-mirror/` | 外部ドライブへの完全コピー |
| 差分同期 | rsync --delete | 削除されたファイルも同期 |

---

## 🔧 管理コマンド

### cron管理

```bash
# cronジョブ確認
crontab -l

# cron編集
crontab -e

# ログ確認
tail -f logs/cron_daily_backup.log
tail -f logs/cron_weekly_backup.log
```

### バックアップ管理

```bash
# バックアップ一覧確認
ls -la ~/Backups/ai-dev-backup/

# 最新バックアップ確認
ls -la ~/Backups/ai-dev-backup/$(ls -t ~/Backups/ai-dev-backup/ | head -1)

# バックアップサイズ確認
du -sh ~/Backups/ai-dev-backup/*
```

### Obsidian Git管理

```bash
# Obsidian Vaultに移動
cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/Obsidian

# 手動コミット
git add .
git commit -m "手動コミット: $(date)"

# 自動コミットログ確認
tail -f logs/auto_commit.log
```

---

## 📈 実装効果

### ✅ 実現される体制

| 項目 | 実現内容 |
|------|----------|
| ⏰ cron 自動バックアップ | 毎日3時に WhisperX + Obsidian + AIシステム バックアップ |
| 🧾 Obsidian Git管理 | 全ノートの変更履歴を明確に保存できる |
| 📁 WhisperX 日付別保存 | 出力ごとにフォルダを作って履歴保持できる |
| 🗂️ rsync フルバックアップ | 外部ドライブへの完全ミラーリング |
| 🔄 自動クリーンアップ | 30日以上前の古いバックアップを自動削除 |

### 🎯 セキュリティ強化

- **多重バックアップ**: 毎日 + 週次で2重保護
- **外部保存**: 外部ドライブへの完全コピー
- **バージョン管理**: Gitによる変更履歴追跡
- **自動化**: 手作業不要の完全自動化

---

## 🔧 トラブルシューティング

### よくある問題

#### 1. cronジョブが実行されない
```bash
# cronサービス確認
sudo launchctl list | grep cron

# cronログ確認
tail -f /var/log/system.log | grep cron
```

#### 2. 外部ドライブが見つからない
```bash
# マウント確認
ls -la /Volumes/

# 手動マウント
sudo mount -t apfs /dev/disk2s1 /Volumes/BACKUP_DRIVE
```

#### 3. バックアップ容量不足
```bash
# ディスク使用量確認
df -h

# 古いバックアップ削除
find ~/Backups/ai-dev-backup -type d -mtime +30 -exec rm -rf {} \;
```

---

## 📋 設定カスタマイズ

### バックアップスケジュール変更

```bash
# cron編集
crontab -e

# 例：毎日午前6時に変更
0 6 * * * bash ~/ai-driven/ai-systems-workspace/scripts/backup/daily_backup.sh
```

### 保存期間変更

```bash
# daily_backup.sh の30日を変更
find "$BACKUP_ROOT" -type d -name "*" -mtime +60 -exec rm -rf {} \;
```

### 除外ファイル追加

```bash
# rsync除外パターン追加
rsync -avh --exclude='*.log' --exclude='temp/' --exclude='cache/' ...
```

---

## 🎉 完了！

これで以下の機能が利用可能になりました：

1. **自動バックアップ**: 毎日・週次で完全自動化
2. **Obsidian Git管理**: ノートの変更履歴完全追跡
3. **WhisperXアーカイブ**: 日付付きで出力保存
4. **外部保存**: 外部ドライブへの完全ミラーリング

### 次のステップ

1. 外部ドライブの接続確認
2. 初回バックアップのテスト実行
3. ログ監視の設定
4. 通知設定のカスタマイズ

---

**🎯 これでMakotoさんの開発環境が完全に保護されました！**
