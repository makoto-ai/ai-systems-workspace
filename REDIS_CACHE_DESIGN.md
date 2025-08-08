# Redis キャッシュ層設計
## 音声ロールプレイシステム v2.0.0 - 高速アクセス・セッション管理

## キャッシュ戦略

### 1. セッション管理キャッシュ
```
キー形式: session:{session_id}
TTL: 30分 (アクティブセッション)
データ構造: Hash

例:
session:550e8400-e29b-41d4-a716-446655440000 = {
    "user_id": "user123",
    "status": "active",
    "speaker_id": 6,
    "conversation_context": "{...}",
    "last_activity": "2025-01-30T10:30:00Z",
    "performance_stats": "{...}"
}
```

### 2. ユーザー状態キャッシュ
```
キー形式: user:{user_id}:state
TTL: 1時間
データ構造: Hash

例:
user:user123:state = {
    "current_session_id": "550e8400-...",
    "last_login": "2025-01-30T09:00:00Z",
    "preferences": "{...}",
    "daily_session_count": 3,
    "remaining_sessions": 47
}
```

### 3. AI応答キャッシュ
```
キー形式: ai_response:{hash(prompt)}
TTL: 1時間
データ構造: String (JSON)

例:
ai_response:abc123def = {
    "prompt_hash": "abc123def",
    "response": "こんにちは、どのようなご質問でしょうか？",
    "provider": "groq",
    "model": "llama-3.1-70b",
    "cached_at": "2025-01-30T10:25:00Z"
}
```

### 4. 音声合成キャッシュ
```
キー形式: voice:{speaker_id}:{hash(text)}
TTL: 24時間
データ構造: String (Base64音声データ)

例:
voice:6:def456ghi = "UklGRnoGAABXQVZFZm10IBAAAAABAAEA..."
```

### 5. パフォーマンスメトリクスキャッシュ
```
キー形式: metrics:{metric_type}:{time_window}
TTL: 5分
データ構造: Sorted Set

例:
metrics:response_time:1h = [
    (1706600400, 1250), # (timestamp, response_time_ms)
    (1706600460, 980),
    (1706600520, 1100)
]
```

### 6. リアルタイム統計
```
キー形式: stats:realtime:{date}
TTL: 24時間
データ構造: Hash

例:
stats:realtime:2025-01-30 = {
    "active_sessions": 15,
    "total_sessions_today": 127,
    "avg_response_time": 1450,
    "system_load": 0.65,
    "error_rate": 0.02
}
```

## Redis クラスター設計

### 1. マスター/スレーブ構成
```
Redis Master (Write): 
  - セッション書き込み
  - キャッシュ更新
  - リアルタイム統計

Redis Slave (Read):
  - 読み込み専用
  - 負荷分散
  - フェイルオーバー
```

### 2. データ分散戦略
```
スロット分散:
  - セッションデータ: 0-5460
  - AIキャッシュ: 5461-10922  
  - 音声キャッシュ: 10923-16383
```

## キャッシュ運用ポリシー

### 1. 自動パージ
- 期限切れセッション: 即座削除
- 古いAI応答: LRU方式
- 大容量音声ファイル: 使用頻度ベース

### 2. 事前ウォームアップ
- よく使用される応答パターン
- 人気シナリオのコンテキスト
- 基本的な音声合成データ

### 3. 障害時フォールバック
- Redis障害時: PostgreSQLから直接読み込み
- 部分障害時: 利用可能ノードで継続
- 復旧時: 段階的キャッシュ再構築

## パフォーマンス目標

### レスポンス時間短縮効果
- セッション取得: 50ms → 5ms (90%短縮)
- AI応答キャッシュヒット: 1500ms → 50ms (97%短縮) 
- 音声合成キャッシュヒット: 800ms → 30ms (96%短縮)

### 同時接続サポート
- フェーズ1: 5名同時 (メモリ使用量: ~100MB)
- フェーズ2: 10名同時 (メモリ使用量: ~200MB)
- フェーズ3: 30名同時 (メモリ使用量: ~600MB)

## 監視指標

### キャッシュ効果測定
- ヒット率: 目標 >85%
- 平均レスポンス時間: 目標 <100ms
- メモリ使用率: 目標 <80%
- 接続数: 目標 <1000 (同時)

### アラート設定
- ヒット率 <70%: WARNING
- レスポンス時間 >200ms: WARNING
- メモリ使用率 >90%: CRITICAL
- 接続失敗率 >5%: CRITICAL
