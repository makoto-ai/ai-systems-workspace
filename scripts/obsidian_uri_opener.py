#!/usr/bin/env python3
"""
Obsidian URI Scheme連携デモ
作成したMarkdownファイルをObsidianで自動オープン
"""

import subprocess
import urllib.parse
from pathlib import Path


def open_in_obsidian(vault_name: str, file_path: str):
    """ObsidianアプリでファイルをオープンするURI生成"""

    # Obsidian URI scheme
    # obsidian://open?vault={vault_name}&file={file_path}

    encoded_file_path = urllib.parse.quote(file_path)
    encoded_vault_name = urllib.parse.quote(vault_name)

    uri = f"obsidian://open?vault={encoded_vault_name}&file={encoded_file_path}"

    print(f"🔗 Obsidian URI: {uri}")

    # macOSでURIを開く
    try:
        subprocess.run(["open", uri], check=True)
        print("✅ Obsidianで自動オープン成功！")
    except subprocess.CalledProcessError:
        print("❌ Obsidianが見つからないか、URI実行に失敗しました")
        print("💡 手動でObsidianを起動してからもう一度試してください")


if __name__ == "__main__":
    # 生成されたファイルをObsidianで開く例
    vault_name = "ai-systems-workspace"  # あなたのObsidianボルト名
    file_path = "cursor-sessions/cursor_session_20250731_180903.md"

    print("🚀 ObsidianでCursorセッション要約を自動オープン")
    open_in_obsidian(vault_name, file_path)
