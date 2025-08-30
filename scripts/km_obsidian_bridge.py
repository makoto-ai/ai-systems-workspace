#!/usr/bin/env python3
"""
Keyboard Maestro ↔ Obsidian ブリッジスクリプト（修復版）
真っ白問題を解決
"""
import sys
import os
import datetime
from pathlib import Path

def save_from_clipboard_km(source_app="unknown"):
    """KMからクリップボード経由でObsidianに保存"""
    try:
        import subprocess
        
        # クリップボード内容取得
        clipboard_content = subprocess.check_output(['pbpaste'], text=True)
        
        if not clipboard_content.strip():
            print("❌ クリップボードが空です")
            return False
        
        # Obsidianパス設定
        vault_path = Path("docs/obsidian-knowledge")
        quick_notes = vault_path / "quick-notes"
        quick_notes.mkdir(parents=True, exist_ok=True)
        
        # ファイル名生成
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"KM自動転送_{source_app}_{timestamp}.md"
        
        # 修復版Markdown生成
        content = f"""# KM自動転送 - {source_app}

📅 **保存時刻**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
📱 **転送元**: {source_app}  
🔧 **システム**: KM→Python→Obsidian（修復版）

## 📋 転送内容

{clipboard_content}

---

*🤖 Keyboard Maestro経由で自動転送*
"""
        
        # ファイル保存（UTF-8、確実保存）
        file_path = quick_notes / filename
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
        
        print(f"✅ KM転送成功: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ KM転送失敗: {e}")
        return False

if __name__ == "__main__":
    source = sys.argv[1] if len(sys.argv) > 1 else "KM"
    save_from_clipboard_km(source)
