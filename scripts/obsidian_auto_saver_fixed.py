#!/usr/bin/env python3
"""
Obsidian自動保存システム（修復版）
真っ白画面問題を解決したバージョン
"""

import os
import datetime
from pathlib import Path
import sys

class ObsidianAutoSaverFixed:
    """修復済みObsidian自動保存システム"""
    
    def __init__(self):
        self.vault_path = Path("docs/obsidian-knowledge")
        self.vault_path.mkdir(parents=True, exist_ok=True)
        
        # 基本フォルダ作成
        self.folders = {
            "quick-notes": self.vault_path / "quick-notes",
            "ai-conversations": self.vault_path / "ai-conversations", 
            "cursor-sessions": self.vault_path / "cursor-sessions",
            "code-snippets": self.vault_path / "code-snippets",
            "learning-notes": self.vault_path / "learning-notes"
        }
        
        for folder in self.folders.values():
            folder.mkdir(exist_ok=True)
    
    def save_clipboard_content(self, content: str, source: str = "unknown"):
        """クリップボードコンテンツを自動保存"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            date_stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # ソース別のタイトル生成
            if "cursor" in source.lower():
                title = "Cursor対話記録"
                category = "cursor-sessions"
            elif "claude" in source.lower():
                title = "Claude対話記録"
                category = "ai-conversations"
            elif "gpt" in source.lower() or "chatgpt" in source.lower():
                title = "ChatGPT対話記録"
                category = "ai-conversations"
            else:
                title = "自動保存コンテンツ"
                category = "quick-notes"
            
            # ファイル名生成
            filename = f"{title}_{date_stamp}.md"
            folder = self.folders[category]
            
            # 修復版Markdown生成（シンプル・確実）
            markdown_content = f"""# {title}

📅 **保存日時**: {timestamp}  
📱 **保存元**: {source}  
🔧 **システム**: 修復版自動保存

## 📝 保存内容

{content}

---

*🤖 自動保存システム（修復版）より*
"""
            
            # ファイル保存（エラーハンドリング強化）
            file_path = folder / filename
            
            # UTF-8で確実に保存
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                f.write(markdown_content)
            
            print(f"✅ 自動保存成功: {file_path.name}")
            return file_path
            
        except Exception as e:
            print(f"❌ 自動保存エラー: {e}")
            return None
    
    def save_conversation(self, user_input: str, ai_response: str, source: str = "AI対話"):
        """対話内容の専用保存"""
        conversation_content = f"""## 👤 ユーザー

{user_input}

## 🤖 AI応答

{ai_response}"""
        
        return self.save_clipboard_content(conversation_content, source)

def save_to_obsidian(content: str, source: str = "自動転送"):
    """外部から呼び出し可能な保存関数"""
    saver = ObsidianAutoSaverFixed()
    return saver.save_clipboard_content(content, source)

def save_conversation_to_obsidian(user_input: str, ai_response: str, source: str = "AI対話"):
    """外部から呼び出し可能な対話保存関数"""
    saver = ObsidianAutoSaverFixed()
    return saver.save_conversation(user_input, ai_response, source)

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        content = sys.argv[1]
        source = sys.argv[2] if len(sys.argv) >= 3 else "コマンドライン"
        save_to_obsidian(content, source)
    else:
        # テスト実行
        test_content = f"修復版テスト実行\n時刻: {datetime.datetime.now()}"
        save_to_obsidian(test_content, "システムテスト")

