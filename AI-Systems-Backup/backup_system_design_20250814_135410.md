# 完全バックアップシステム設計と運用ノート（テキスト版）

## 目的
- 震災・PC破損・盗難・初期化時でも、新PC＋パスワードだけで確実に復旧できる体制。
- RPO（許容データ損失）= 最大24時間、RTO（復旧時間）= 数時間目標。

## バックアップ対象
- ~/ai-driven/ai-systems-workspace（コード・設定・スクリプト）
- ~/Backups/db（PostgreSQLダンプ）
- ~/Library/Mobile Documents/com~apple~CloudDocs/Obsidian（Obsidian）
- ~/whisperx_outputs（音声処理出力）

## 実装コンポーネント
- ローカル日次バックアップ: `scripts/backup/daily_backup.sh`
  - 先行DBダンプ: `scripts/backup/db_dump.sh`
  - rsyncで `~/Backups/ai-dev-backup/YYYY-MM-DD_HH-MM/` へ保存
  - 30日超の世代を自動削除
- オフサイト暗号化（Cloudflare R2 + restic）: `scripts/backup/restic_backup.sh`
  - 暗号化・重複排除・差分転送
  - 実行後 `restic check --read-data-subset=1%`
  - 保持ポリシー: 日次14 / 週次8 / 月次6（`restic forget --prune`）
- 復元検証（週次）: `scripts/backup/restic_restore_verify.sh`
  - サンプル複数ファイルのリストア＋ハッシュ照合
  - Slack/Mail通知は任意（環境変数設定で有効化）

## スケジュール（cron）
- 毎日 03:00: `daily_backup.sh`（DBダンプ→rsync）
- 毎日 04:00: `restic_backup.sh`（R2暗号化＋check）
- 毎週 日曜 04:30: `restic_restore_verify.sh`（復元検証）

## 設定ファイル
- restic: `scripts/backup/restic.env`
  - RESTIC_REPOSITORY="s3:https://<ACCOUNT_ID>.r2.cloudflarestorage.com/<BUCKET>"
  - AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / RESTIC_PASSWORD（パスワード管理で保管）
  - BACKUP_PATHS に対象ディレクトリ、EXCLUDES に不要パス
  - 保持: `RESTIC_KEEP_DAILY=14` `RESTIC_KEEP_WEEKLY=8` `RESTIC_KEEP_MONTHLY=6`
- DBダンプ: `scripts/backup/db.env`
  - 推奨: `DATABASE_URL="postgres://USER:PASSWORD@HOST:5432/DBNAME"`
  - 代替: PGHOST/PGUSER/PGPASSWORD/PGDATABASE

## 復旧手順（新PC）
1. Homebrew + restic を導入
2. `RESTIC_REPOSITORY` と `RESTIC_PASSWORD`（およびR2のアクセスキー）を環境に設定
3. ファイル復元: `restic restore latest --target ~/`
4. 依存復旧: `pip install -r requirements.txt` など
5. DB復旧（必要時）: `pg_restore -d <DB名> ~/Backups/db/pg_<DB名>_<日時>.dump`

## 日常運用
- ログ確認: `logs/cron_daily_backup.log` / `logs/cron_restic_backup.log` / `logs/cron_restore_verify.log`
- 使用量:
  - R2: `restic stats --mode raw-data`
  - ローカル: `du -sh ~/Backups/ai-dev-backup/* | tail`
- 頻度変更:
  - cronの時間を編集
  - restic保持ポリシー（`RESTIC_KEEP_*`）を調整

## セキュリティ
- RESTIC_PASSWORD と R2アクセスキーは必ずパスワードマネージャで保管。
- Git等のバージョン管理に `.env` / `restic.env` / `db.env` を含めない。

## 既知の除外（EXCLUDES）
- `**/.venv` `**/__pycache__` `**/.git` `**/node_modules` `**/*.log` など

## 直近の検証結果（実施日: $(date '+%Y-%m-%d %H:%M')）
- DBダンプ: 成功（`~/Backups/db/pg_*.dump` 生成）
- R2スナップショット: 作成済み（restic check OK）
- 復元ドライラン: サンプル3ファイルのハッシュ一致、`pg_restore --list` OK

## 変更履歴（メモ）
- $(date '+%Y-%m-%d'): Obsidian / whisperx_outputs を対象に追加、cron登録、ドライラン実施。

