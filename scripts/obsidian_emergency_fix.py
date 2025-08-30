#!/usr/bin/env python3
"""
Obsidian自動転送緊急修復スクリプト
「真っ白画面」問題の解決
"""

import os
import datetime
from pathlib import Path

class ObsidianEmergencyFix:
    """Obsidian自動転送の緊急修復"""
    
    def __init__(self):
        self.vault_path = Path("docs/obsidian-knowledge")
        self.vault_path.mkdir(parents=True, exist_ok=True)
        
        # 基本フォルダ作成
        self.folders = {
            "quick-notes": self.vault_path / "quick-notes",
            "ai-conversations": self.vault_path / "ai-conversations",
            "cursor-sessions": self.vault_path / "cursor-sessions"
        }
        
        for folder in self.folders.values():
            folder.mkdir(exist_ok=True)
    
    def save_content_safely(self, content: str, title: str = None, category: str = "quick-notes"):
        """安全にObsidianに保存"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            date_stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if title is None:
                title = f"自動保存_{timestamp}"
            
            # 安全なファイル名生成
            safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_"))
            safe_title = safe_title.replace(" ", "_")[:30]
            filename = f"{safe_title}_{date_stamp}.md"
            
            folder = self.folders.get(category, self.folders["quick-notes"])
            
            # シンプルなMarkdown生成
            markdown_content = f"""# {title}

📅 **保存日時**: {timestamp}  
📁 **カテゴリ**: {category}  
🔧 **修復モード**: 緊急修復版

## 📝 内容

{content}

---

*✅ 緊急修復システムより保存*
"""
            
            # ファイル保存
            file_path = folder / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"✅ 緊急修復保存成功: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"❌ 緊急修復保存失敗: {e}")
            return None
    
    def test_save(self):
        """保存機能テスト"""
        test_content = f"""緊急修復テスト

このファイルがObsidianで正常に表示されれば、
自動転送機能の修復が成功しています。

テスト時刻: {datetime.datetime.now()}

**確認事項:**
- このテキストが見える ✅
- 真っ白画面ではない ✅
- フォーマットが正常 ✅
"""
        
        return self.save_content_safely(
            content=test_content,
            title="緊急修復テスト",
            category="quick-notes"
        )

if __name__ == "__main__":
    fixer = ObsidianEmergencyFix()
    result = fixer.test_save()
    if result:
        print(f"🎉 緊急修復テスト完了: {result}")
        print("👁️ Obsidianでファイルを確認してください")
    else:
        print("❌ 緊急修復テスト失敗")

