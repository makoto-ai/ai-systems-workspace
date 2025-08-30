#!/usr/bin/env python3
"""
KMファイル自動振り分けマクロ復旧スクリプト
元の記憶に基づいてマクロを再構成
"""

import json
import subprocess
from pathlib import Path

def create_file_sorter_macro():
    """ファイル自動振り分けマクロ作成"""
    
    # route_downloads_v2.shの絶対パス
    script_path = "/Users/araimakoto/bin/route_downloads_v2.sh"
    
    macro_config = {
        "Activate": "Normal",
        "CreationDate": 693595200.0,
        "Macros": [
            {
                "Actions": [
                    {
                        "ActionUID": 2001,
                        "MacroActionType": "FolderWatch",
                        "Path": "~/Downloads",
                        "RecursiveFolderWatch": False,
                        "WatchForFileChanges": True,
                        "WatchForFileDeletes": False,
                        "WatchForSubfolderChanges": False
                    },
                    {
                        "ActionUID": 2002,
                        "MacroActionType": "ExecuteShell",
                        "Path": "/usr/bin/bash",
                        "Parameters": f'{script_path} "%TriggerValue%"',
                        "TimeOutAbortsMacro": True,
                        "TimeOutPeriod": 30,
                        "TrimResults": True,
                        "TrimResultsNew": True
                    }
                ],
                "CreationDate": 693595200.0,
                "ModificationDate": 693595200.0,
                "Name": "Downloads自動振り分け",
                "Triggers": [
                    {
                        "FireType": "AddedToFolder",
                        "MacroTriggerType": "FolderWatch",
                        "Path": "~/Downloads",
                        "TriggerUID": 3001
                    }
                ],
                "UID": "DOWNLOADS-AUTO-SORTER-12345"
            }
        ],
        "Name": "ファイル自動振り分け",
        "UID": "FILE-AUTO-SORTER-GROUP-12345"
    }
    
    return macro_config

def save_file_sorter_macro():
    """ファイル振り分けマクロを保存"""
    try:
        config = create_file_sorter_macro()
        
        macro_path = Path("Downloads自動振り分け復旧.kmmacros")
        
        with open(macro_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ ファイル振り分けマクロ復旧ファイル作成: {macro_path}")
        print("📋 設定内容:")
        print("   • 監視フォルダ: ~/Downloads")
        print("   • 実行スクリプト: /Users/araimakoto/bin/route_downloads_v2.sh")
        print("   • トリガー: ファイル追加時")
        
        return macro_path
        
    except Exception as e:
        print(f"❌ マクロ復旧ファイル作成失敗: {e}")
        return None

if __name__ == "__main__":
    print("🔧 KMファイル振り分けマクロ復旧開始...")
    result = save_file_sorter_macro()
    if result:
        print("🎉 復旧ファイル作成完了！")
        print("📥 次のステップ:")
        print("   1. Keyboard Maestroを開く")
        print(f"   2. ファイル → インポート → {result}")
        print("   3. Downloads監視マクロ復活！")
    else:
        print("❌ 復旧ファイル作成失敗")
