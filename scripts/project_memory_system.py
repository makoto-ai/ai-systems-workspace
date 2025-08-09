#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📝 プロジェクト記憶保持アシスタント
カーソル操作、MCP設定、進行状況を記録・復元するシステム

作成日: 2025-08-09
目的: Claude Projects/GPT APIと連携して記憶を保持
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
import subprocess
import logging
from typing import Dict, Any

try:
    import requests  # type: ignore
except Exception:  # 依存が無い場合でも壊さない
    requests = None  # type: ignore

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/project_memory.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProjectMemorySystem:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.memory_dir = self.project_root / "memory"
        self.memory_dir.mkdir(exist_ok=True)
        
        # 記録ファイル
        self.project_log = self.memory_dir / "project.log"
        self.cursor_state = self.memory_dir / "cursor_state.json"
        self.mcp_snapshot = self.memory_dir / "mcp_snapshot.json"
        self.session_history = self.memory_dir / "session_history.json"
        self.snapshots_dir = self.memory_dir / "snapshots"
        self.snapshots_dir.mkdir(exist_ok=True)
        self.events_log = self.project_root / "logs" / "project_events.jsonl"
        self.events_log.parent.mkdir(parents=True, exist_ok=True)
        
        # 初期化時にファイルを作成
        self._initialize_memory_files()
        
    def _initialize_memory_files(self):
        """記憶ファイルの初期化"""
        # プロジェクトログ初期化
        if not self.project_log.exists():
            with open(self.project_log, 'w', encoding='utf-8') as f:
                f.write(f"# 📝 プロジェクト記憶ログ\n作成日: {datetime.now().isoformat()}\n\n")
        
        # セッション履歴初期化
        if not self.session_history.exists():
            with open(self.session_history, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
        
        # Cursor状態初期化
        if not self.cursor_state.exists():
            with open(self.cursor_state, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
        
        # MCPスナップショット初期化
        if not self.mcp_snapshot.exists():
            with open(self.mcp_snapshot, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
        
        logger.info("記憶ファイル初期化完了")
        
    def capture_current_state(self, session_purpose: str = None) -> dict:
        """現在のプロジェクト状態をキャプチャ"""
        timestamp = datetime.now().isoformat()
        
        state = {
            "timestamp": timestamp,
            "session_purpose": session_purpose,
            "git_status": self._get_git_status(),
            "cursor_configs": self._get_cursor_configs(),
            "project_structure": self._get_project_structure(),
            "active_files": self._get_active_files(),
            "system_status": self._get_system_status()
        }
        
        # 状態ハッシュ
        state_str = json.dumps(state, sort_keys=True)
        state["state_hash"] = hashlib.md5(state_str.encode()).hexdigest()
        
        # 状態を保存
        with open(self.cursor_state, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        # MCPスナップショットを更新
        snapshot_info = self._create_mcp_snapshot()
        state["mcp_snapshot"] = snapshot_info
        with open(self.mcp_snapshot, 'w', encoding='utf-8') as f:
            json.dump(snapshot_info, f, ensure_ascii=False, indent=2)
        
        # イベントとして書き出し
        self._export_event({
            "type": "state_capture",
            "purpose": session_purpose,
            "state_hash": state["state_hash"],
            "timestamp": timestamp,
            "git": state["git_status"],
        })
        
        logger.info(f"プロジェクト状態キャプチャ完了: {state['state_hash'][:8]}")
        return state
    
    def save_session_memory(self, session_purpose: str, actions: list, results: list):
        """セッション記憶を保存"""
        session_data = {
            "timestamp": datetime.now().isoformat(),
            "session_purpose": session_purpose,
            "actions_taken": actions,
            "results_achieved": results,
            "state_before": self.capture_current_state(session_purpose),
            "state_after": self.capture_current_state(session_purpose + "_after")
        }
        
        # セッション履歴に追加
        history = self._load_session_history()
        history.append(session_data)
        
        with open(self.session_history, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        # プロジェクトログに追記
        self._append_to_project_log(session_data)
        
        # イベントエクスポート
        self._export_event({
            "type": "session_memory",
            "purpose": session_purpose,
            "timestamp": session_data["timestamp"],
            "git": session_data["state_after"]["git_status"],
        })
        
        logger.info(f"セッション記憶保存完了: {session_purpose}")
    
    def generate_restoration_guide(self) -> str:
        """復元ガイド生成"""
        recent_sessions = self._load_session_history()[-5:]  # 最新5セッション
        
        guide = f"""
# 🔄 プロジェクト復元ガイド
生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📋 最新のセッション履歴
"""
        
        for i, session in enumerate(recent_sessions, 1):
            guide += f"""
### {i}. {session['session_purpose']} ({session['timestamp'][:16]})
**実行したアクション:**
{self._format_actions(session['actions_taken'])}

**達成した結果:**
{self._format_results(session['results_achieved'])}

**復元コマンド:**
```bash
git checkout {session['state_after']['git_status']['commit_hash']}
```
"""
        
        guide += f"""
## 🔧 重要な設定ファイル
- MCP設定: .cursor/ ({len(self._get_cursor_configs())}個)
- 環境設定: config/ 
- システム監視: main_hybrid.py, system_monitor.py

## 🛡️ 安全な復元手順
1. `git log --oneline -10` で履歴確認
2. `git checkout <コミットハッシュ>` で状態復元
3. `python scripts/project_memory_system.py --verify` で検証

## 🚨 緊急時復元
```bash
git checkout master
python scripts/project_memory_system.py --emergency-restore
```
"""
        
        # ガイドを保存
        guide_file = self.memory_dir / "restoration_guide.md"
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(guide)
        
        # イベントエクスポート
        self._export_event({"type": "restore_guide_generated", "timestamp": datetime.now().isoformat()})
        
        return guide

    def _create_mcp_snapshot(self) -> Dict[str, Any]:
        """.cursor配下の設定のスナップショットを作成し、snapshotsにも保存する"""
        cursor_dir = self.project_root / ".cursor"
        snapshot = {"files": [], "timestamp": datetime.now().isoformat()}
        if not cursor_dir.exists():
            return snapshot
        
        files = sorted(cursor_dir.glob("*.json"))
        for f in files:
            try:
                content = json.loads(f.read_text(encoding='utf-8'))
                snapshot["files"].append({
                    "name": f.name,
                    "size": f.stat().st_size,
                    "hash": hashlib.md5(json.dumps(content, sort_keys=True).encode()).hexdigest()
                })
            except Exception as e:
                snapshot["files"].append({"name": f.name, "error": str(e)})
        
        # スナップショットの実体保存
        snap_file = self.snapshots_dir / f"mcp_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        snap_file.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding='utf-8')
        return snapshot

    def _export_event(self, event: Dict[str, Any]):
        """イベントをJSONLとして保存し、Webhookが指定されていれば送信"""
        event = {**event, "project": self.project_root.name}
        line = json.dumps(event, ensure_ascii=False)
        with open(self.events_log, 'a', encoding='utf-8') as f:
            f.write(line + "\n")
        
        webhook = os.getenv("PROJECT_LOG_WEBHOOK")
        if webhook and requests:
            try:
                requests.post(webhook, json=event, timeout=5)
            except Exception as e:
                logger.warning(f"Webhook送信失敗: {e}")
        
    def _get_git_status(self) -> dict:
        """Git状態取得"""
        try:
            # 現在のコミット
            commit_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], 
                cwd=self.project_root,
                text=True
            ).strip()
            
            # ブランチ名
            branch = subprocess.check_output(
                ["git", "branch", "--show-current"], 
                cwd=self.project_root,
                text=True
            ).strip()
            
            # 変更状況
            status = subprocess.check_output(
                ["git", "status", "--porcelain"], 
                cwd=self.project_root,
                text=True
            ).strip()
            
            return {
                "commit_hash": commit_hash,
                "branch": branch,
                "uncommitted_changes": len(status.split('\n')) if status else 0,
                "status_details": status
            }
        except Exception as e:
            logger.error(f"Git状態取得エラー: {e}")
            return {"error": str(e)}
    
    def _get_cursor_configs(self) -> dict:
        """Cursor設定取得"""
        cursor_dir = self.project_root / ".cursor"
        configs = {}
        
        if cursor_dir.exists():
            for config_file in cursor_dir.glob("*.json"):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        configs[config_file.name] = json.load(f)
                except Exception as e:
                    configs[config_file.name] = {"error": str(e)}
        
        return configs
    
    def _get_project_structure(self) -> dict:
        """プロジェクト構造取得"""
        important_dirs = ["app", "config", "scripts", "modules", "paper_research_system"]
        structure = {}
        
        for dir_name in important_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                py_files = list(dir_path.rglob("*.py"))
                structure[dir_name] = {
                    "exists": True,
                    "python_files": len(py_files),
                    "total_files": len(list(dir_path.rglob("*")))
                }
            else:
                structure[dir_name] = {"exists": False}
        
        return structure
    
    def _get_active_files(self) -> list:
        """アクティブファイル取得"""
        important_files = [
            "main_hybrid.py", 
            "system_monitor.py", 
            "modules/composer.py",
            "quality_metrics.py",
            "streamlit_app.py"
        ]
        
        active = []
        for file_name in important_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                stat = file_path.stat()
                active.append({
                    "file": file_name,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return active
    
    def _get_system_status(self) -> dict:
        """システム状態取得"""
        try:
            # プロセス確認
            ps_result = subprocess.check_output(
                ["ps", "aux"], text=True
            )
            main_hybrid_running = "main_hybrid.py" in ps_result
            
            return {
                "main_hybrid_running": main_hybrid_running,
                "python_files_count": len(list(self.project_root.rglob("*.py"))),
                "cursor_configs_count": len(list((self.project_root / ".cursor").glob("*.json")))
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _load_session_history(self) -> list:
        """セッション履歴読み込み"""
        if self.session_history.exists():
            try:
                with open(self.session_history, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"セッション履歴読み込みエラー: {e}")
        return []
    
    def _append_to_project_log(self, session_data: dict):
        """プロジェクトログに追記"""
        log_entry = f"""
---
## {session_data['session_purpose']} ({session_data['timestamp'][:16]})

### 実行内容:
{self._format_actions(session_data['actions_taken'])}

### 結果:
{self._format_results(session_data['results_achieved'])}

### Git状態:
- コミット: {session_data['state_after']['git_status'].get('commit_hash', 'N/A')[:8]}
- ブランチ: {session_data['state_after']['git_status'].get('branch', 'N/A')}

"""
        
        with open(self.project_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def _format_actions(self, actions: list) -> str:
        """アクション整形"""
        if not actions:
            return "- なし"
        return "\n".join(f"- {action}" for action in actions)
    
    def _format_results(self, results: list) -> str:
        """結果整形"""
        if not results:
            return "- なし"
        return "\n".join(f"- {result}" for result in results)

def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description="プロジェクト記憶保持システム")
    parser.add_argument("--capture", action="store_true", help="現在の状態をキャプチャ")
    parser.add_argument("--restore-guide", action="store_true", help="復元ガイド生成")
    parser.add_argument("--session", help="セッション目的を指定")
    
    args = parser.parse_args()
    
    memory_system = ProjectMemorySystem()
    
    if args.capture:
        state = memory_system.capture_current_state(args.session)
        print(f"✅ 状態キャプチャ完了: {state['state_hash'][:8]}")
    
    if args.restore_guide:
        guide = memory_system.generate_restoration_guide()
        print("✅ 復元ガイド生成完了")
        print(guide[:500] + "..." if len(guide) > 500 else guide)

if __name__ == "__main__":
    main()