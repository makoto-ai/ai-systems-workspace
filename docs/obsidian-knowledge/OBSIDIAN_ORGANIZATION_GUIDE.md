# 🗂️ 統合Obsidianワークスペース組織化ガイド

## 📋 システム別フォルダ構造

### 🎯 命名規則の原則
- **各システムは独立したフォルダ**
- **ファイル名にシステム識別子を含める**
- **日時形式統一**: `YYYYMMDD_HHMMSS`
- **日本語と英語の混在OK**

---

## 📁 フォルダ構造詳細

### 📚 `research-papers/` - 論文検索システム
```
research-papers/
├── sales-psychology/           # 営業心理学専門
├── management-psychology/      # マネジメント心理学
├── behavioral-economics/       # 行動経済学
├── general-psychology/         # 一般心理学
├── search-sessions/           # 検索セッション記録
└── 論文検索_[テーマ]_[日時].md  # 個別検索結果
```

**ファイル名例**:
- `論文検索_sales_psychology_20250802_145708.md`
- `論文検索_machine_learning_20250802_145708.md`

---

### 🤖 `ai-conversations/` - Cursor AI対話記録
```
ai-conversations/
├── daily-sessions/            # 日次セッション
├── project-discussions/       # プロジェクト議論
├── problem-solving/          # 問題解決記録
└── AI対話_[テーマ]_[日時].md    # 個別対話記録
```

**ファイル名例**:
- `AI対話_論文検索システム開発_20250802_145708.md`
- `AI対話_GitHub通知問題解決_20250802_143000.md`

---

### 💾 `ai-memory/` - Cursor記憶システム
```
ai-memory/
├── sessions/                 # セッション記録
├── enhanced/                # 拡張記憶データ
├── backups/                 # 重要対話バックアップ
├── context/                 # コンテキスト保存
├── safety/                  # 安全確認記録
└── tasks/                   # タスク管理
```

**ファイル名例**:
- `session_20250802_145708.json`
- `enhanced_context_20250802_145708.json`

---

### 🎙️ `voice-roleplay-system/` - 音声ロールプレイシステム（新設）
```
voice-roleplay-system/
├── conversation-logs/        # 会話ログ
├── performance-analysis/     # パフォーマンス分析
├── training-data/           # トレーニングデータ
├── speaker-profiles/        # スピーカープロファイル
└── ロールプレイ_[シナリオ]_[日時].md
```

**ファイル名例**:
- `ロールプレイ_営業交渉_20250802_145708.md`
- `パフォーマンス分析_20250802_145708.md`

---

### 🔧 `system-backups/` - システムバックアップ（新設）
```
system-backups/
├── daily-backups/           # 日次バックアップ記録
├── disaster-recovery/       # 災害復旧記録
├── system-status/          # システム状態記録
└── バックアップ_[システム名]_[日時].md
```

**ファイル名例**:
- `バックアップ_完全システム_20250802_145708.md`
- `復旧テスト_20250802_145708.md`

---

### 📖 `business-books/` - ビジネス書知識
```
business-books/
├── [書籍名]/
│   ├── 📚[書籍名].md        # メイン要約
│   ├── Chapters/           # チャプター別
│   ├── IIB - [書籍名].md   # インサイト・アイデア
│   └── BoaP - [書籍名].md  # 実践ポイント
```

---

### 💡 `learning-notes/` - 学習・気づき
```
learning-notes/
├── technical-insights/      # 技術的洞察
├── business-insights/      # ビジネス洞察
├── personal-growth/        # 個人成長
└── [カテゴリ]_[内容]_[日時].md
```

---

### 🚀 `project-ideas/` - プロジェクトアイデア
```
project-ideas/
├── ai-systems/             # AIシステム関連
├── business-automation/    # ビジネス自動化
├── personal-productivity/  # 個人生産性
└── アイデア_[分野]_[内容]_[日時].md
```

---

## 🔄 自動統合システム

### 📡 各システムからの自動保存
1. **論文検索システム** → `research-papers/`
2. **Cursor記憶システム** → `ai-memory/`, `ai-conversations/`
3. **音声ロールプレイ** → `voice-roleplay-system/`
4. **バックアップシステム** → `system-backups/`

### 🏷️ タグ統一規則
```
#論文検索 #AI対話 #ロールプレイ #バックアップ
#営業心理学 #マネジメント #技術開発 #システム構築
#重要 #緊急 #完了 #進行中
```

---

## 📊 統合検索・分析機能

### 🔍 横断検索が可能
- 全システムの知識を統合検索
- テーマ別・日付別・システム別でフィルタ
- 関連性の可視化

### 📈 知識ベース分析
- システム別データ蓄積量
- よく使用されるテーマ
- 知識の関連性マップ

---

## 🎯 運用ルール

### ✅ DO（推奨）
- システム名をファイル名に含める
- 日時形式を統一する
- 適切なフォルダに分類する
- タグを活用する

### ❌ DON'T（非推奨）
- システム間でファイル名が重複する
- フォルダ分けを無視する
- 無関係な内容を混在させる

---

**🎊 これで全システムが整理され、統合知識ベースとして機能します！**