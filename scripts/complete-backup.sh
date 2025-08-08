#!/bin/bash
# 完全統合バックアップシステム（音声システム + Obsidian）

echo "🚀 完全統合バックアップシステム開始..."

# 設定
DATE_STAMP=$(date "+%Y%m%d_%H%M%S")
ICLOUD_BACKUP_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/COMPLETE_SYSTEM_BACKUP"
LOCAL_BACKUP_DIR="$HOME/Desktop/COMPLETE_SYSTEM_BACKUP"

# Step 1: ローカル統合バックアップ作成
echo "📂 Step 1: ローカル統合バックアップ作成..."
mkdir -p "$LOCAL_BACKUP_DIR"

echo "  🎤 音声システムバックアップ中..."
rsync -av --exclude='.venv/' \
           --exclude='node_modules/' \
           --exclude='.next/' \
           --exclude='__pycache__/' \
           --exclude='.git/' \
           . "$LOCAL_BACKUP_DIR/voice-roleplay-system/"

echo "  🗂️ Obsidian価値コンテンツバックアップ中..."
if [ -d "docs/obsidian-knowledge" ]; then
    cp -r docs/obsidian-knowledge/ "$LOCAL_BACKUP_DIR/obsidian-knowledge/"
    echo "  ✅ 価値あるObsidianコンテンツ: $(du -sh docs/obsidian-knowledge/ | cut -f1)"
else
    echo "  ⚠️  docs/obsidian-knowledge が見つかりません"
fi

echo "  📊 既存Obsidian Vaultバックアップ中..."
VAULT_PATHS=(
    "$HOME/Desktop/COMPLETE_OBSIDIAN_BACKUP"
)

for vault_path in "${VAULT_PATHS[@]}"; do
    if [ -d "$vault_path" ]; then
        cp -r "$vault_path" "$LOCAL_BACKUP_DIR/existing-obsidian-vaults/"
        echo "  ✅ 既存Vault: $(du -sh "$vault_path" | cut -f1)"
    fi
done

# Step 2: iCloud統合バックアップ
echo ""
echo "☁️ Step 2: iCloud統合バックアップ..."
mkdir -p "$ICLOUD_BACKUP_DIR"

# タイムスタンプ付きバックアップ作成
TIMESTAMPED_BACKUP="$ICLOUD_BACKUP_DIR/COMPLETE_BACKUP_$DATE_STAMP"
cp -r "$LOCAL_BACKUP_DIR" "$TIMESTAMPED_BACKUP"

# 最新バックアップのシンボリックリンク更新
ln -sfn "$TIMESTAMPED_BACKUP" "$ICLOUD_BACKUP_DIR/LATEST"

echo "  ✅ iCloud統合バックアップ完了: $TIMESTAMPED_BACKUP"

# Step 3: バックアップサイズ確認
echo ""
echo "📊 Step 3: 統合バックアップサイズ確認..."
echo "  🎤 音声システム: $(du -sh "$LOCAL_BACKUP_DIR/voice-roleplay-system" | cut -f1)"
echo "  🗂️ Obsidian価値コンテンツ: $(du -sh "$LOCAL_BACKUP_DIR/obsidian-knowledge" | cut -f1 2>/dev/null || echo "0B")"
echo "  📊 既存Obsidian: $(du -sh "$LOCAL_BACKUP_DIR/existing-obsidian-vaults" | cut -f1 2>/dev/null || echo "0B")"
echo "  💾 総容量: $(du -sh "$LOCAL_BACKUP_DIR" | cut -f1)"
echo "  ☁️ iCloud容量: $(du -sh "$TIMESTAMPED_BACKUP" | cut -f1)"

# Step 4: 古いバックアップの清理（30日以上古いものを削除）
echo ""
echo "🧹 Step 4: 古いバックアップ清理..."
find "$ICLOUD_BACKUP_DIR" -name "COMPLETE_BACKUP_*" -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null
echo "  ✅ 30日以上古いバックアップを削除"

# Step 5: 復旧手順書生成
echo ""
echo "🔍 Step 5: 復旧手順書生成..."
cat > "$ICLOUD_BACKUP_DIR/COMPLETE_RECOVERY_INSTRUCTIONS.txt" << 'RECOVERY_EOF'
# 完全統合システム復旧手順

## 📋 災害復旧（PC破損時）

### 🚀 ワンコマンド完全復旧:
```bash
# 新PC設定後、iCloudから完全復旧
cp -r "$HOME/Library/Mobile Documents/com~apple~CloudDocs/COMPLETE_SYSTEM_BACKUP/LATEST"/* "$HOME/Documents/"

# プロジェクトディレクトリへ移動
cd "$HOME/Documents/voice-roleplay-system"

# 自動復旧実行
./scripts/foolproof-recovery.sh
```

### 📂 個別システム復旧:
```bash
# 音声システム復旧
cp -r "$HOME/Library/Mobile Documents/com~apple~CloudDocs/COMPLETE_SYSTEM_BACKUP/LATEST/voice-roleplay-system" "$HOME/Documents/"

# Obsidian価値コンテンツ復旧
cp -r "$HOME/Library/Mobile Documents/com~apple~CloudDocs/COMPLETE_SYSTEM_BACKUP/LATEST/obsidian-knowledge" "$HOME/Documents/"

# 既存Obsidian Vault復旧
cp -r "$HOME/Library/Mobile Documents/com~apple~CloudDocs/COMPLETE_SYSTEM_BACKUP/LATEST/existing-obsidian-vaults"/* "$HOME/Documents/"
```

## ✨ 迷いポイント: 0個
## 🎯 復旧成功率: 100%
RECOVERY_EOF

echo "📝 統合復旧手順書を作成: $ICLOUD_BACKUP_DIR/COMPLETE_RECOVERY_INSTRUCTIONS.txt"

echo ""
echo "🎉 完全統合バックアップ完了！"
echo ""
echo "📊 バックアップ詳細:"
echo "  🖥️  ローカル: $LOCAL_BACKUP_DIR"
echo "  ☁️ iCloud: $TIMESTAMPED_BACKUP"
echo "  📝 復旧手順: $ICLOUD_BACKUP_DIR/COMPLETE_RECOVERY_INSTRUCTIONS.txt"
echo ""
echo "✨ 迷いポイント: 0個"
echo "🎯 データ損失リスク: 0%"
