#!/usr/bin/env python3
"""
Keyboard Maestro自動設定スクリプト
AppleScriptを使わないObsidian連携設定
"""

import os
import json
from pathlib import Path

def create_km_macro_json():
    """KMマクロ設定JSON生成"""
    
    # プロジェクトの絶対パス取得
    project_path = Path.cwd()
    script_path = project_path / "scripts" / "km_obsidian_bridge.py"
    
    macro_config = {
        "Activate": "Normal",
        "CreationDate": 693595200.0,
        "Macros": [
            {
                "Actions": [
                    {
                        "ActionUID": 1001,
                        "MacroActionType": "ExecuteShell",
                        "Path": "/usr/bin/python3",
                        "Parameters": f'cd "{project_path}" && python3 "{script_path}" Cursor',
                        "TimeOutAbortsMacro": True,
                        "TimeOutPeriod": 10,
                        "TrimResults": True,
                        "TrimResultsNew": True
                    }
                ],
                "CreationDate": 693595200.0,
                "ModificationDate": 693595200.0,
                "Name": "Obsidian自動保存（修復版）",
                "Triggers": [
                    {
                        "FireType": "Pressed",
                        "KeyCode": 15,
                        "MacroTriggerType": "HotKey",
                        "Modifiers": 4352,
                        "TriggerUID": 2001
                    }
                ],
                "UID": "12345678-1234-1234-1234-123456789ABC"
            }
        ],
        "Name": "Obsidian自動保存",
        "UID": "87654321-4321-4321-4321-CBA987654321"
    }
    
    return macro_config

def save_km_macro():
    """KMマクロ設定を保存"""
    try:
        config = create_km_macro_json()
        
        # KMマクロファイル保存
        km_macro_path = Path("Obsidian自動保存.kmmacros")
        
        with open(km_macro_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ KMマクロ設定ファイル作成: {km_macro_path}")
        print("📋 設定内容:")
        print(f"   • ホットキー: Cmd+Shift+R")
        print(f"   • 実行スクリプト: {Path.cwd()}/scripts/km_obsidian_bridge.py")
        print(f"   • 動作: クリップボード → Obsidian保存")
        
        return km_macro_path
        
    except Exception as e:
        print(f"❌ KMマクロ設定作成失敗: {e}")
        return None

if __name__ == "__main__":
    print("🤖 Keyboard Maestro自動設定開始...")
    result = save_km_macro()
    if result:
        print("🎉 自動設定完了！")
        print("📥 次のステップ:")
        print("   1. Keyboard Maestroを開く")
        print(f"   2. ファイル → インポート → {result}")
        print("   3. 設定完了！")
    else:
        print("❌ 自動設定失敗")
