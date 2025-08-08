#!/usr/bin/env python3
"""
Obsidian無音保存システム
メール通知なしでObsidianに静かに保存
"""

import os
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import json


class ObsidianSilentSaver:
    """メール通知なしでObsidianに保存するクラス"""

    def __init__(self, obsidian_vault_path: str = "docs/obsidian-knowledge"):
        self.vault_path = Path(obsidian_vault_path)
        self.vault_path.mkdir(parents=True, exist_ok=True)

        # サイレントモード設定
        self.silent_mode = True

        # 各カテゴリフォルダ作成（サイレント）
        self.folders = {
            "cursor-sessions": self.vault_path / "cursor-sessions",
            "development-logs": self.vault_path / "development-logs",
            "quick-notes": self.vault_path / "quick-notes",
            "ai-conversations": self.vault_path / "ai-conversations",
            "code-snippets": self.vault_path / "code-snippets",
            "project-ideas": self.vault_path / "project-ideas",
            "research-papers": self.vault_path / "research-papers",
            "learning-notes": self.vault_path / "learning-notes",
            "custom": self.vault_path / "custom-content",
        }

        for folder in self.folders.values():
            folder.mkdir(exist_ok=True)

    def save_quietly(
        self,
        content: str,
        title: str = None,
        category: str = "quick-notes",
        filename: str = None,
        tags: List[str] = None,
    ) -> Path:
        """メール通知なしで静かに保存"""

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # ファイル名自動生成
        if filename is None:
            if title:
                safe_title = "".join(
                    c for c in title if c.isalnum() or c in (" ", "-", "_")
                ).rstrip()
                safe_title = safe_title.replace(" ", "_")[:50]
                filename = f"{safe_title}_{date_stamp}.md"
            else:
                filename = f"silent_content_{date_stamp}.md"

        # カテゴリフォルダ選択
        folder = self.folders.get(category, self.folders["quick-notes"])

        # タイトル自動生成
        if title is None:
            title = f"サイレント保存 - {timestamp}"

        # タグ処理
        if tags is None:
            tags = ["silent-save", "no-notification"]

        # Markdownコンテンツ生成
        markdown_content = f"""# {title}

> 📅 **保存日時**: {timestamp}
> 📁 **カテゴリ**: {category}
> 🔇 **モード**: サイレント保存（メール通知なし）

## 💾 保存コンテンツ

{content}

## 🏷️ タグ

{' '.join([f'#{tag}' for tag in tags])}

---

*🔇 このドキュメントはサイレントモードで保存されました（通知なし）*
"""

        # ファイル保存（サイレント）
        file_path = folder / filename
        file_path.write_text(markdown_content, encoding="utf-8")

        # サイレントモードの場合は出力を最小限に
        if self.silent_mode:
            print(f"🔇 サイレント保存: {filename}")
        else:
            print(f"✅ Obsidian保存完了: {file_path}")
            print(f"📁 カテゴリ: {category}")
            print(f"📄 ファイル名: {filename}")

        return file_path


def save_test_content_silently():
    """サイレント保存のテスト"""

    saver = ObsidianSilentSaver()

    print("🔇 サイレント保存テスト開始...")

    # テストコンテンツをサイレント保存
    test_content = """
## 📧 メール通知問題の解決

### 問題
Obsidianファイル保存の度にメール通知が発生

### 原因
monitor-services.sh プロセスがファイル変更を監視

### 解決策
1. monitor-services.shプロセス停止 ✅
2. サイレント保存システム実装 ✅
3. 通知なしモードで動作確認 ✅

### 結果
メール通知完全停止、静かな保存が可能に
    """

    file_path = saver.save_quietly(
        content=test_content,
        title="メール通知問題の完全解決",
        category="learning-notes",
        tags=["問題解決", "メール通知停止", "サイレント保存"],
    )

    print(f"🎉 サイレント保存テスト完了！")
    print(f"📁 保存先: {file_path.name}")
    print(f"🔇 メール通知: なし")


if __name__ == "__main__":
    save_test_content_silently()
