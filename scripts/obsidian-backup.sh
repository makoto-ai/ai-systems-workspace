#!/bin/bash
# Obsidian完全バックアップスクリプト
# 全てのObsidian vaultを自動でiCloudにバックアップ

echo "🗂️ Obsidian完全バックアップシステム開始..."

# 作業ディレクトリ設定
BACKUP_DIR="$HOME/Desktop/COMPLETE_OBSIDIAN_BACKUP"
ICLOUD_BACKUP_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/OBSIDIAN_MASTER_BACKUP"
DATE_STAMP=$(date "+%Y%m%d_%H%M%S")

# Step 1: ローカルバックアップ作成
echo "📂 Step 1: ローカルバックアップ作成..."
mkdir -p "$BACKUP_DIR"

# 全てのObsidian vaultを検索してバックアップ
VAULT_PATHS=(
    "$PWD/docs/obsidian-knowledge"
    "$HOME/Downloads/Obsidian Professional Kit"
    "$HOME/Downloads/Obsidian Starter Kit-2"
)

VAULT_NAMES=(
    "Valuable_Content"
    "Professional_Kit"
    "Starter_Kit_2"
)

for i in "${!VAULT_PATHS[@]}"; do
    VAULT_PATH="${VAULT_PATHS[$i]}"
    VAULT_NAME="${VAULT_NAMES[$i]}"
    
    if [ -d "$VAULT_PATH" ]; then
        echo "  📋 $VAULT_NAME をバックアップ中..."
        cp -r "$VAULT_PATH" "$BACKUP_DIR/$VAULT_NAME"
        echo "  ✅ $VAULT_NAME バックアップ完了"
    else
        echo "  ⚠️  $VAULT_NAME が見つかりません: $VAULT_PATH"
    fi
done

# Step 2: iCloudバックアップ
echo ""
echo "☁️ Step 2: iCloudバックアップ..."
mkdir -p "$ICLOUD_BACKUP_DIR"

# タイムスタンプ付きバックアップ作成
TIMESTAMPED_BACKUP="$ICLOUD_BACKUP_DIR/OBSIDIAN_BACKUP_$DATE_STAMP"
cp -r "$BACKUP_DIR" "$TIMESTAMPED_BACKUP"

# 最新バックアップのシンボリックリンク更新
ln -sfn "$TIMESTAMPED_BACKUP" "$ICLOUD_BACKUP_DIR/LATEST"

echo "  ✅ iCloudバックアップ完了: $TIMESTAMPED_BACKUP"

# Step 3: バックアップサイズ確認
echo ""
echo "📊 Step 3: バックアップサイズ確認..."
du -sh "$BACKUP_DIR"/* 2>/dev/null
echo "  💾 総容量: $(du -sh "$BACKUP_DIR" | cut -f1)"
echo "  ☁️ iCloud容量: $(du -sh "$TIMESTAMPED_BACKUP" | cut -f1)"

# Step 4: 古いバックアップの清理（30日以上古いものを削除）
echo ""
echo "🧹 Step 4: 古いバックアップ清理..."
find "$ICLOUD_BACKUP_DIR" -name "OBSIDIAN_BACKUP_*" -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null
echo "  ✅ 30日以上古いバックアップを削除"

# Step 5: 復旧テスト情報生成
echo ""
echo "🔍 Step 5: 復旧情報生成..."
cat > "$ICLOUD_BACKUP_DIR/RECOVERY_INSTRUCTIONS.txt" << 'RECOVERY_EOF'
# Obsidian完全復旧手順

## 📋 災害復旧（PC破損時）

### �� ワンコマンド復旧:
```bash
# iCloudから最新バックアップを復旧
cp -r "$HOME/Library/Mobile Documents/com~apple~CloudDocs/OBSIDIAN_MASTER_BACKUP/LATEST"/* "$HOME/Documents/"
```

### 📂 個別vault復旧:
```bash
# メインvault復旧
cp -r "$HOME/Library/Mobile Documents/com~apple~CloudDocs/OBSIDIAN_MASTER_BACKUP/LATEST/Vault_Main" "$HOME/Documents/Obsidian_Vault_Restored"

# 復旧vault復旧  
cp -r "$HOME/Library/Mobile Documents/com~apple~CloudDocs/OBSIDIAN_MASTER_BACKUP/LATEST/Vault_Recovered" "$HOME/Documents/Obsidian_Recovered_Restored"

# 再構築vault復旧
cp -r "$HOME/Library/Mobile Documents/com~apple~CloudDocs/OBSIDIAN_MASTER_BACKUP/LATEST/Vault_Rebuild" "$HOME/Documents/Obsidian_Rebuild_Restored"
```

## ✨ 迷いポイント: 0個
RECOVERY_EOF

echo "📝 復旧手順書を作成: $ICLOUD_BACKUP_DIR/RECOVERY_INSTRUCTIONS.txt"

echo ""
echo "🎉 Obsidian完全バックアップ完了！"
echo ""
echo "📊 バックアップ詳細:"
echo "  🖥️  ローカル: $BACKUP_DIR"
echo "  ☁️ iCloud: $TIMESTAMPED_BACKUP"
echo "  📝 復旧手順: $ICLOUD_BACKUP_DIR/RECOVERY_INSTRUCTIONS.txt"
echo ""
echo "✨ 迷いポイント: 0個"
