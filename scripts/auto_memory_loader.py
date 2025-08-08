#!/usr/bin/env python3
"""
🧠 自動記憶復元システム - どんな会話でも最初に記憶を自動復元
AIアシスタントが最初に呼び出すことで、ユーザーがどんな指示を出しても記憶が復元される
"""

import os
import sys
import datetime
from pathlib import Path


def auto_load_memory():
    """自動記憶復元 - 最初の会話で必ず実行される"""

    try:
        # cursor_session_bridge.pyのパスを確認
        script_dir = Path(__file__).parent
        bridge_script = script_dir / "cursor_session_bridge.py"

        if not bridge_script.exists():
            return "❌ 記憶システムが見つかりません"

        # 新セッション検出と記憶復元を実行
        import subprocess

        result = subprocess.run(
            [sys.executable, str(bridge_script), "briefing"],
            capture_output=True,
            text=True,
            cwd=script_dir.parent,
        )

        if result.returncode == 0:
            # AI_SESSION_BRIEFING.mdの内容を読み込み
            briefing_file = script_dir.parent / "AI_SESSION_BRIEFING.md"
            if briefing_file.exists():
                with open(briefing_file, "r", encoding="utf-8") as f:
                    briefing_content = f.read()

                return f"""🧠 **記憶システム自動復元完了**

{briefing_content}

---
✅ **自動復元システム動作**: この文脈情報を踏まえて、ご質問にお答えいたします。
"""
            else:
                return (
                    "✅ 記憶システム実行完了（ブリーフィングファイルが見つかりません）"
                )
        else:
            return f"⚠️ 記憶システム実行エラー: {result.stderr}"

    except Exception as e:
        return f"❌ 自動記憶復元エラー: {str(e)}"


def should_auto_load() -> bool:
    """自動読み込みが必要かチェック"""

    try:
        script_dir = Path(__file__).parent
        marker_file = script_dir.parent / ".cursor_session_active"

        # マーカーファイルが存在しない場合は新セッション
        if not marker_file.exists():
            return True

        # 30分以上経過している場合は新セッション
        last_modified = datetime.datetime.fromtimestamp(marker_file.stat().st_mtime)
        time_diff = datetime.datetime.now() - last_modified

        return time_diff.total_seconds() > 1800  # 30分

    except Exception:
        return True  # エラーの場合は安全のため実行


def get_memory_context() -> str:
    """記憶システムから文脈を取得（軽量版）"""

    try:
        # 既存のブリーフィングファイルがあれば読み込み
        script_dir = Path(__file__).parent
        briefing_file = script_dir.parent / "AI_SESSION_BRIEFING.md"

        if briefing_file.exists():
            with open(briefing_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 重要な部分だけ抽出
            lines = content.split("\n")
            important_lines = []
            for line in lines:
                if any(
                    keyword in line
                    for keyword in [
                        "総会話数",
                        "重要事項",
                        "警告",
                        "継続中のタスク",
                        "ワークフロー",
                    ]
                ):
                    important_lines.append(line)

            if important_lines:
                return "🧠 " + " | ".join(important_lines[:5])

        return ""

    except Exception:
        return ""


# スタンドアロン実行
if __name__ == "__main__":
    if should_auto_load():
        print("🔍 新セッション検出 - 記憶復元中...")
        result = auto_load_memory()
        print(result)
    else:
        print("🔄 既存セッション継続中")
        context = get_memory_context()
        if context:
            print(context)
