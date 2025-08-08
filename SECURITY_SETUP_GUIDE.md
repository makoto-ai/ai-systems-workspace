# 🔒 セキュリティ設定・監査ログシステム

## 📋 概要

このシステムは「出力セキュリティの確保」と「運用履歴のログ化」を目的として設計されています。Auto/Claude/GPT/Maxモード問わず常時有効となる構成です。

## 🛡️ 実装されたファイル

### 1. 出力制限・環境保護設定ファイル
**ファイル**: `.cursor/mcp_security.json`

#### 主要機能
- **出力先制限**: 特定ディレクトリ・外部連携制限
- **ファイル保護**: `.env`, `secrets/` などの改変ブロック
- **上書き警告**: 自動生成ファイルに対する保護
- **セキュリティ基準**: ガードレールとして機能

#### 保護対象
```
保護ファイル:
- .env, .env.*
- secrets.json, credentials.json
- api_keys.json, config.json

保護ディレクトリ:
- secrets/, credentials/, keys/
- .git/, node_modules/, venv/
- .cursor/, config_backup_0808/
```

### 2. 監査ログファイル（監査証跡の明示）
**ファイル**: `.cursor/mcp_audit.json`

#### 主要機能
- **AIモデル追跡**: Claude/GPT-4/Groq/Google等の使用記録
- **MCP構成追跡**: 使用されたMCP/テンプレート構成の記録
- **GitHub連携**: GitHub MCPとの連携を前提とした監査
- **コンプライアンス**: GDPR/SOX/ISO27001/NIST準拠

#### 記録項目
```json
{
  "timestamp": "2025-01-27T10:30:00",
  "user_id": "user_identifier",
  "ai_model": "claude-3-5-sonnet",
  "mcp_configuration": "mcp_security.json",
  "template_used": "youtube_script",
  "operation_type": "content_generation",
  "purpose": "YouTube原稿生成",
  "status": "success"
}
```

### 3. APIキーなどの秘匿設定
**ファイル**: `env.example` (テンプレート)

#### 管理対象API
- **Claude API**: `ANTHROPIC_API_KEY`
- **OpenAI API**: `OPENAI_API_KEY`
- **Groq API**: `GROQ_API_KEY`
- **Google API**: `GOOGLE_API_KEY`, `GOOGLE_SCHOLAR_API_KEY`
- **Whisper API**: `WHISPER_API_KEY`
- **HuggingFace**: `HUGGINGFACE_HUB_TOKEN`

#### セキュリティ機能
- **自動保護**: `.env`ファイルの作成・改変・削除をブロック
- **Git除外**: `.gitignore`に`.env`関連ファイルを追加
- **暗号化**: 機密データの暗号化対応

## 🔧 設定の有効化

### 自動有効化
設定は以下のモードで自動的に有効になります：

- **Auto Mode**: 厳格な検証 + 強化ログ
- **Claude Mode**: Anthropic準拠 + Constitutional AI
- **GPT Mode**: OpenAI準拠 + コンテンツフィルタリング
- **Max Mode**: 高度セキュリティ + リアルタイム保護

### 手動確認
```bash
# セキュリティ設定テスト実行
python test_security_config.py
```

## 📊 監査ログの確認

### ログファイル
- **監査ログ**: `logs/audit_trail.json`
- **セキュリティログ**: `logs/security_audit.log`
- **テストログ**: `logs/security_test.log`

### ログ形式
```json
{
  "timestamp": "ISO 8601形式",
  "user_id": "ユーザー識別子",
  "session_id": "セッションID",
  "ai_model": "使用AIモデル",
  "operation_type": "操作タイプ",
  "status": "成功/失敗",
  "security_level": "セキュリティレベル",
  "compliance_status": "コンプライアンス状況"
}
```

## 🚨 セキュリティ警告

### 重要な注意事項
1. **`.env`ファイル**: 絶対にGitにコミットしない
2. **APIキー**: 定期的にローテーション
3. **バックアップ**: 暗号化して保存
4. **アクセス制御**: 必要最小限の権限のみ付与

### 保護機能
- ✅ 機密ファイルの自動検出・ブロック
- ✅ 外部API呼び出しの制限
- ✅ レート制限の適用
- ✅ リアルタイム監視
- ✅ コンプライアンスチェック

## 📈 パフォーマンス監視

### 監視項目
- **API使用量**: トークン使用量・コスト追跡
- **レスポンス時間**: レイテンシー監視
- **エラー率**: 失敗率の追跡
- **セキュリティ**: 違反検出・アラート

### アラート設定
- **セキュリティ違反**: 即座にアラート
- **パフォーマンス低下**: 閾値超過時
- **コスト超過**: 予算超過時
- **コンプライアンス違反**: 規制違反時

## 🔄 更新・メンテナンス

### 定期メンテナンス
- **週次**: ログファイルの圧縮・アーカイブ
- **月次**: セキュリティ設定の見直し
- **四半期**: コンプライアンス監査
- **年次**: 完全なセキュリティ評価

### バックアップ戦略
- **設定ファイル**: 自動バックアップ
- **ログファイル**: 圧縮・暗号化保存
- **監査証跡**: 長期保存（7年間）

## 📞 トラブルシューティング

### よくある問題
1. **設定ファイル読み込みエラー**
   - ファイルパスの確認
   - JSON形式の妥当性チェック

2. **ログファイル作成エラー**
   - ディレクトリ権限の確認
   - ディスク容量の確認

3. **セキュリティ制限の誤動作**
   - 設定値の見直し
   - ホワイトリストの追加

### サポート
- **ログ確認**: `logs/` ディレクトリ
- **設定確認**: `.cursor/` ディレクトリ
- **テスト実行**: `test_security_config.py`

## 📋 チェックリスト

### 初期設定
- [ ] `env.example` を `.env` にコピー
- [ ] APIキーを設定
- [ ] セキュリティテスト実行
- [ ] ログディレクトリ作成
- [ ] バックアップ設定確認

### 定期確認
- [ ] ログファイルの確認
- [ ] セキュリティ設定の見直し
- [ ] APIキーのローテーション
- [ ] コンプライアンスチェック
- [ ] パフォーマンス監視

---

**最終更新**: 2025-01-27  
**バージョン**: 2.0.0  
**対応モード**: Auto/Claude/GPT/Max 