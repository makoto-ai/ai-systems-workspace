#!/bin/bash
# 🚨 緊急復旧システム
# 削除されたファイルの即座復旧

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROTECTION_SCRIPT="$SCRIPT_DIR/CRITICAL_FILE_PROTECTION.py"
BACKUP_DIR="$SCRIPT_DIR/.critical_backups"

# 色設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${RED}🚨 緊急復旧システム${NC}"
echo "=============================="

# バックアップディレクトリ確認
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}❌ バックアップディレクトリが見つかりません: $BACKUP_DIR${NC}"
    echo -e "${YELLOW}💡 保護システムを初期化してください${NC}"
    exit 1
fi

# 利用可能なバックアップを表示
echo -e "${BLUE}📁 利用可能なバックアップ:${NC}"
backups_found=0
if [ -d "$BACKUP_DIR" ]; then
    for backup in "$BACKUP_DIR"/*.backup; do
        if [ -f "$backup" ]; then
            backup_name=$(basename "$backup")
            backup_size=$(du -h "$backup" | cut -f1)
            backup_date=$(stat -f %Sm -t "%Y-%m-%d %H:%M" "$backup" 2>/dev/null || date -r "$backup" "+%Y-%m-%d %H:%M" 2>/dev/null)
            echo -e "  ${GREEN}✅${NC} $backup_name (${backup_size}, ${backup_date})"
            ((backups_found++))
        fi
    done
fi

if [ $backups_found -eq 0 ]; then
    echo -e "${RED}❌ 復旧可能なバックアップが見つかりません${NC}"
    exit 1
fi

echo ""
echo -e "${PURPLE}📊 バックアップ統計: ${backups_found}個のファイル${NC}"

# 復旧オプション
echo ""
echo -e "${YELLOW}🔄 復旧オプション:${NC}"
echo "1. 特定ファイルの復旧"
echo "2. 最新バックアップ一括復旧"
echo "3. 全バックアップ表示"
echo "4. キャンセル"

read -p "選択してください (1-4): " choice

case $choice in
    1)
        echo ""
        read -p "復旧したいファイル名を入力してください: " target_file
        echo -e "${BLUE}🔍 '$target_file' に関連するバックアップを検索中...${NC}"
        
        found_backup=""
        for backup in "$BACKUP_DIR"/*.backup; do
            if [[ "$(basename "$backup")" == *"$target_file"* ]]; then
                found_backup="$backup"
                break
            fi
        done
        
        if [ -n "$found_backup" ]; then
            echo -e "${GREEN}✅ バックアップ発見: $(basename "$found_backup")${NC}"
            echo ""
            read -p "このバックアップから復旧しますか？ (y/n): " confirm
            if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
                python3 "$PROTECTION_SCRIPT" restore "$target_file"
            else
                echo -e "${YELLOW}復旧をキャンセルしました${NC}"
            fi
        else
            echo -e "${RED}❌ '$target_file' に関連するバックアップが見つかりませんでした${NC}"
        fi
        ;;
        
    2)
        echo ""
        echo -e "${YELLOW}⚠️ 最新バックアップから一括復旧を実行します${NC}"
        read -p "続行しますか？ (y/n): " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            echo -e "${BLUE}🔄 一括復旧実行中...${NC}"
            
            # 最新の5個のバックアップを復旧
            count=0
            for backup in $(ls -t "$BACKUP_DIR"/*.backup 2>/dev/null | head -5); do
                if [ -f "$backup" ]; then
                    backup_name=$(basename "$backup" .backup)
                    original_name=$(echo "$backup_name" | sed 's/_[0-9]*_[0-9]*$//')
                    
                    echo -e "  復旧中: $original_name"
                    python3 "$PROTECTION_SCRIPT" restore "$original_name"
                    ((count++))
                fi
            done
            
            echo -e "${GREEN}✅ ${count}個のファイルを復旧しました${NC}"
        else
            echo -e "${YELLOW}復旧をキャンセルしました${NC}"
        fi
        ;;
        
    3)
        echo ""
        echo -e "${BLUE}📋 全バックアップ詳細:${NC}"
        for backup in "$BACKUP_DIR"/*.backup; do
            if [ -f "$backup" ]; then
                echo "----------------------------------------"
                echo "ファイル: $(basename "$backup")"
                echo "サイズ: $(du -h "$backup" | cut -f1)"
                echo "作成日: $(stat -f %Sm -t "%Y-%m-%d %H:%M:%S" "$backup" 2>/dev/null || date -r "$backup" "+%Y-%m-%d %H:%M:%S" 2>/dev/null)"
                echo "パス: $backup"
            fi
        done
        ;;
        
    4)
        echo -e "${YELLOW}緊急復旧をキャンセルしました${NC}"
        exit 0
        ;;
        
    *)
        echo -e "${RED}❌ 無効な選択です${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}🎯 緊急復旧処理完了${NC}"
echo -e "${BLUE}💡 今後の削除は './safe-delete.sh' を使用してください${NC}"