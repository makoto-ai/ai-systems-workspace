# 🛡️ Cursor暴走防止・完全対策ガイド

## ⚠️ Cursor暴走事件の対策

### �� 発生した問題
- **ホームディレクトリ削除**: Cursorが~/を完全削除
- **データ完全喪失**: Documents, Desktop, Downloads等全消失
- **設定消失**: アプリケーション設定・ファイル全て消失

### 🛡️ 再発防止策

#### 1. Cursor設定安全化
```json
{
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 500,
  "cursor.ai.dangerousActionsRequireConfirmation": true,
  "cursor.ai.enableFileOperations": false,
  "workbench.settings.enableNaturalLanguageSearch": false
}
```

#### 2. 保護ディレクトリ設定
```bash
# 重要ディレクトリの読み取り専用設定
chmod 444 ~/Documents/important-files/*
chmod 444 ~/Desktop/critical-data/*
```

#### 3. バックアップ自動化強化
```bash
# 1時間毎の自動バックアップ
crontab -e
# 0 * * * * rsync -av ~/ai-driven/ ~/Backups/ai-driven-$(date +%Y%m%d_%H)/
```

#### 4. Git保護強化
```bash
# プロジェクトの1時間毎自動コミット
*/60 * * * * cd ~/ai-driven/ai-systems-workspace/voice-roleplay-system && ./auto-save.sh
```

### 🚨 緊急時即座対応手順

#### Cursor暴走検知時
1. **即座停止**: Cmd+C → Cursor強制終了
2. **被害確認**: `ls -la ~/` でホームディレクトリ確認
3. **バックアップ確認**: GitHubリポジトリ生存確認
4. **復旧開始**: 災害復旧ガイド実行

#### 完全復旧手順
1. **新しいユーザー作成** (最悪の場合)
2. **GitHub からプロジェクト復旧**
3. **自動復旧システム実行**
4. **保護設定再適用**

### 📱 予防設定スクリプト
```bash
./cursor-protection.sh  # Cursor保護設定適用
./auto-save.sh          # 定期自動保存
```

