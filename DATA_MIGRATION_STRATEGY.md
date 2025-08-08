# データ移行戦略
## 音声ロールプレイシステム v2.0.0 - JSONファイル → DB移行

## 移行概要

### 現在のデータ構造
```
data/
├── usage_limits.json (47KB) - ユーザー利用制限・設定
├── ab_tests/ - A/Bテスト設定
├── ml_models/ - MLモデルデータ
└── voicevox/ - 音声設定
```

### 移行対象データ
1. **usage_limits.json** → PostgreSQL (users, user_usage_limits)
2. **アプリケーション設定** → PostgreSQL (scenarios)
3. **A/Bテスト設定** → PostgreSQL (実験管理テーブル)
4. **MLモデル** → 分析DB (モデルメタデータ)

## 段階的移行計画

### Phase 1: 基盤準備 (Week 1)
```
1. PostgreSQL環境セットアップ
   - 本番用クラスター構築
   - レプリケーション設定
   - バックアップ設定

2. TimescaleDB環境セットアップ  
   - 時系列DB構築
   - パーティション設定
   - 圧縮ポリシー設定

3. Redis クラスター構築
   - マスター/スレーブ設定
   - 分散設定
   - 監視設定
```

### Phase 2: 移行スクリプト開発 (Week 1-2)
```python
# migration_scripts/migrate_usage_limits.py
import json
import asyncio
import asyncpg
from datetime import datetime

async def migrate_usage_limits():
    # JSONファイル読み込み
    with open('data/usage_limits.json', 'r') as f:
        usage_data = json.load(f)
    
    # PostgreSQL接続
    conn = await asyncpg.connect('postgresql://...')
    
    for user_id, data in usage_data.items():
        # users テーブルに挿入
        await conn.execute("""
            INSERT INTO users (user_id, email, created_at, notification_settings)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO UPDATE SET
                notification_settings = $4,
                updated_at = CURRENT_TIMESTAMP
        """, user_id, data.get('email', ''), 
             datetime.fromisoformat(data['created_at']),
             json.dumps(data['reminder_settings']))
        
        # user_usage_limits テーブルに挿入
        await conn.execute("""
            INSERT INTO user_usage_limits (
                user_id, roleplay_sessions_remaining,
                total_roleplay_sessions, consecutive_days,
                last_reset_date, recent_sessions
            ) VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (user_id) DO UPDATE SET
                roleplay_sessions_remaining = $2,
                total_roleplay_sessions = $3,
                updated_at = CURRENT_TIMESTAMP
        """, user_id, data['roleplay_sessions_remaining'],
             data['total_roleplay_sessions'], data['consecutive_days'],
             datetime.fromisoformat(data['last_reset_date']).date(),
             json.dumps(data['recent_sessions']))
    
    await conn.close()
    print(f"移行完了: {len(usage_data)} ユーザー")

# 実行
asyncio.run(migrate_usage_limits())
```

### Phase 3: 段階的切り替え (Week 2-3)
```
1. 読み込み処理の段階的移行
   - 新機能: DB読み込み
   - 既存機能: JSONファイル読み込み (フォールバック)

2. 書き込み処理の並行実行
   - DB + JSONファイル 両方に書き込み
   - 整合性チェック

3. JSONファイル読み込み停止
   - DB読み込みに完全移行
   - JSONファイル読み込みコード削除
```

### Phase 4: パフォーマンス最適化 (Week 3-4)
```
1. インデックス最適化
   - クエリパフォーマンス測定
   - 最適なインデックス追加
   - 実行計画分析

2. Redisキャッシュ導入
   - セッション管理移行
   - AI応答キャッシュ
   - 音声合成キャッシュ

3. 接続プール最適化
   - 同時接続数調整
   - タイムアウト設定
   - リトライ戦略
```

## 安全性保証

### 1. データバックアップ戦略
```bash
# 移行前フルバックアップ
pg_dump voice_roleplay_db > backup_pre_migration.sql
cp -r data/ data_backup_$(date +%Y%m%d)/

# 移行中リアルタイムバックアップ
pg_basebackup -D backup_realtime/
```

### 2. ロールバック計画
```
Level 1: アプリケーション設定変更
  - 環境変数でDB接続無効化
  - JSONファイル読み込みに復帰
  - 5分以内の復旧

Level 2: データベース復旧  
  - バックアップからDB復元
  - アプリケーション再起動
  - 30分以内の復旧

Level 3: 完全システム復旧
  - 移行前状態に完全復元
  - 全コンポーネント再構築
  - 2時間以内の復旧
```

### 3. 移行検証
```python
# validation_scripts/verify_migration.py
async def verify_data_integrity():
    # JSON vs DB データ比較
    json_data = load_json_data()
    db_data = await load_db_data()
    
    for user_id in json_data:
        assert json_data[user_id]['roleplay_sessions_remaining'] == \
               db_data[user_id]['roleplay_sessions_remaining']
        assert json_data[user_id]['total_roleplay_sessions'] == \
               db_data[user_id]['total_roleplay_sessions']
    
    print("✅ データ整合性確認完了")

async def verify_performance():
    # レスポンス時間測定
    start_time = time.time()
    user_data = await get_user_usage_limits("test_user")
    db_response_time = time.time() - start_time
    
    assert db_response_time < 0.1  # 100ms以内
    print(f"✅ DB応答時間: {db_response_time:.3f}s")
```

## 移行スケジュール

### Week 1: 基盤構築
- [ ] PostgreSQL/TimescaleDB/Redis 環境構築
- [ ] 移行スクリプト開発
- [ ] テスト環境での移行テスト

### Week 2: 段階的移行開始  
- [ ] 読み込み処理移行 (フォールバック付き)
- [ ] 書き込み処理並行実行
- [ ] データ整合性監視

### Week 3: 完全移行
- [ ] JSONファイル読み込み停止
- [ ] DB読み込み専用化
- [ ] パフォーマンス最適化

### Week 4: 安定化・監視
- [ ] 本番監視体制確立
- [ ] パフォーマンス調整
- [ ] ユーザー受け入れテスト

## 成功基準

### パフォーマンス目標
- データ取得: <100ms (JSONファイル: ~50ms)
- データ更新: <200ms (JSONファイル: ~100ms)  
- 同時接続: 30名対応 (JSONファイル: 1名)
- 可用性: 99.9%以上

### 機能目標
- 全データ移行完了: 100%
- 機能互換性: 100%
- データ整合性: 100%
- ゼロダウンタイム: 達成
