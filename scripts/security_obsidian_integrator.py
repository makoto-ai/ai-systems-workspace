#!/usr/bin/env python3
"""
📝 Security Obsidian Integrator - セキュリティ×Obsidian統合システム
セキュリティデータのObsidian自動保存・ナレッジ化
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import datetime

class SecurityObsidianIntegrator:
    """セキュリティデータのObsidian統合システム"""
    
    def __init__(self, obsidian_vault_path: str = "docs/obsidian-knowledge"):
        self.vault_path = Path(obsidian_vault_path)
        self.vault_path.mkdir(parents=True, exist_ok=True)
        
        # セキュリティ専用フォルダ構造
        self.security_folders = {
            "security": self.vault_path / "security-automation",
            "threat_reports": self.vault_path / "security-automation" / "threat-reports",
            "learning_data": self.vault_path / "security-automation" / "learning-data", 
            "predictions": self.vault_path / "security-automation" / "predictions",
            "improvements": self.vault_path / "security-automation" / "improvements",
            "system_logs": self.vault_path / "security-automation" / "system-logs"
        }
        
        # フォルダ作成
        for folder in self.security_folders.values():
            folder.mkdir(parents=True, exist_ok=True)
            
        print("📝 セキュリティ×Obsidian統合システム初期化完了")
    
    def save_security_report(self, report_data: Dict[str, Any]) -> str:
        """セキュリティレポートをObsidianに保存"""
        
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
        filename = f"security_report_{timestamp}.md"
        file_path = self.security_folders["threat_reports"] / filename
        
        # Markdownコンテンツ生成
        content = f"""# セキュリティレポート {timestamp}

## 📊 概要
- **スキャン日時**: {report_data.get('scan_timestamp', timestamp)}
- **総問題数**: {report_data.get('summary', {}).get('total_issues', 0)}件
- **重大**: {report_data.get('summary', {}).get('critical_issues', 0)}件
- **高**: {report_data.get('summary', {}).get('high_issues', 0)}件
- **中**: {report_data.get('summary', {}).get('medium_issues', 0)}件
- **セキュリティスコア**: {report_data.get('summary', {}).get('security_score', 0)}/100点

## 🔍 検出された脆弱性

### 重大度別分類
"""
        
        vulnerabilities = report_data.get('vulnerabilities', {})
        
        for vuln_type, issues in vulnerabilities.items():
            if issues:
                content += f"\n#### {vuln_type.replace('_', ' ').title()}\n"
                for issue in issues[:5]:  # 最初の5件のみ表示
                    content += f"- **{issue.get('severity', 'MEDIUM')}**: {issue.get('file', 'unknown')}\n"
                    content += f"  - {issue.get('description', 'No description')}\n"
                if len(issues) > 5:
                    content += f"  - *...他{len(issues)-5}件*\n"
        
        # 推奨事項
        recommendations = report_data.get('recommendations', [])
        if recommendations:
            content += "\n## 🎯 推奨修復事項\n"
            for i, rec in enumerate(recommendations, 1):
                content += f"{i}. {rec}\n"
        
        # タグ追加
        content += f"\n\n---\n#security #automated #report #{timestamp[:7]}"
        
        # ファイル保存
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📝 セキュリティレポート保存完了: {file_path}")
        return str(file_path)
    
    def save_learning_insights(self, learning_data: Dict[str, Any]) -> str:
        """学習結果をObsidianに保存"""
        
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
        filename = f"learning_insights_{timestamp}.md"
        file_path = self.security_folders["learning_data"] / filename
        
        content = f"""# 学習インサイト {timestamp}

## 📚 学習サイクル結果
- **分析レポート数**: {learning_data.get('data_summary', {}).get('reports_analyzed', 0)}件
- **処理イベント数**: {learning_data.get('data_summary', {}).get('events_processed', 0)}件
- **学習パターン数**: {learning_data.get('data_summary', {}).get('patterns_learned', 0)}件
- **予測脅威数**: {learning_data.get('data_summary', {}).get('threats_predicted', 0)}件

## 🔄 学習したパターン

### 頻出脅威
"""
        
        patterns = learning_data.get('patterns', {})
        frequent_threats = patterns.get('frequent_threats', {})
        
        for threat_type, frequency in frequent_threats.items():
            content += f"- **{threat_type}**: {frequency}回発生\n"
        
        # 予測結果
        predictions = learning_data.get('predictions', {})
        high_risk_threats = predictions.get('high_risk_threats', [])
        
        if high_risk_threats:
            content += "\n## 🔮 脅威予測\n"
            for threat in high_risk_threats[:3]:
                content += f"- **{threat.get('threat_type', 'unknown')}**\n"
                content += f"  - リスクスコア: {threat.get('risk_score', 0)}\n"
                content += f"  - 予測: {threat.get('prediction', 'No prediction')}\n"
        
        # 改善提案
        suggestions = learning_data.get('suggestions', {})
        immediate_actions = suggestions.get('immediate_actions', [])
        
        if immediate_actions:
            content += "\n## 🚨 即座対応が必要\n"
            for action in immediate_actions:
                content += f"- **{action.get('action', 'Unknown action')}**\n"
                content += f"  - 優先度: {action.get('priority', 'MEDIUM')}\n"
                content += f"  - 推定時間: {action.get('estimated_time', 'Unknown')}\n"
        
        content += f"\n\n---\n#security #learning #ai #insights #{timestamp[:7]}"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📝 学習インサイト保存完了: {file_path}")
        return str(file_path)
    
    def create_security_knowledge_index(self) -> str:
        """セキュリティナレッジのインデックスページ作成"""
        
        index_file = self.security_folders["security"] / "README.md"
        
        content = f"""# 🔒 セキュリティ自動化ナレッジベース

最終更新: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}

## 📁 フォルダ構成

### [[threat-reports/|脅威レポート]]
- 自動生成されたセキュリティスキャンレポート
- 脆弱性の詳細分析結果
- 推奨修復事項

### [[learning-data/|学習データ]]  
- AI学習結果とインサイト
- 脅威パターンの分析
- 予測結果

### [[predictions/|予測]]
- 将来の脅威予測
- リスク評価
- 予防アクション

### [[improvements/|改善]]
- 実行された改善事項
- 効果測定結果
- ベストプラクティス

### [[system-logs/|システムログ]]
- セキュリティシステムの動作ログ
- エラー・警告の記録
- パフォーマンスデータ

## 🔄 自動化フロー

1. **セキュリティスキャン実行** → `threat-reports/` に自動保存
2. **学習サイクル実行** → `learning-data/` にインサイト保存  
3. **予測生成** → `predictions/` に結果保存
4. **改善実施** → `improvements/` に記録

## 🏷️ タグシステム

- `#security` - セキュリティ関連全般
- `#automated` - 自動生成コンテンツ
- `#learning` - AI学習関連
- `#prediction` - 予測・分析結果
- `#critical` - 緊急対応必要
- `#improvement` - 改善・最適化

---
*このナレッジベースは自動化システムにより管理されています*
"""
        
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📝 ナレッジインデックス作成完了: {index_file}")
        return str(index_file)

if __name__ == "__main__":
    # テスト実行
    integrator = SecurityObsidianIntegrator()
    
    # インデックス作成
    integrator.create_security_knowledge_index()
    
    print("📝 セキュリティ×Obsidian統合システム準備完了！")