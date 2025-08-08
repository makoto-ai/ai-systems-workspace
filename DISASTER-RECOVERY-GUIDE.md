# 🆘 Voice Roleplay System - 災害復旧ガイド

## 📋 目次
1. [災害時の完全復旧手順](#災害時の完全復旧手順)
2. [必要なバックアップファイル](#必要なバックアップファイル)
3. [システム要件](#システム要件)
4. [ステップバイステップ復旧](#ステップバイステップ復旧)
5. [APIキー再設定](#apiキー再設定)
6. [トラブルシューティング](#トラブルシューティング)
7. [復旧後の確認](#復旧後の確認)

---

## 🆘 災害時の完全復旧手順

### 緊急事態シナリオ
- **PCの完全破損・紛失**
- **ハードドライブクラッシュ**
- **ランサムウェア攻撃**
- **システム完全フォーマット**

**このガイドに従えば、上記の状況からでも100%復旧可能です。**

---

## 💾 必要なバックアップファイル

### 📦 最重要バックアップ（必須）
| ファイル名 | 種類 | サイズ | 保存場所 |
|------------|------|--------|----------|
| `voice-roleplay-complete-backup-YYYYMMDD-HHMMSS.bundle` | Gitバンドル | ~254KB | 複数の外部ストレージ |
| `disaster-recovery-setup.sh` | 復旧スクリプト | ~15KB | 同上 |
| `DISASTER-RECOVERY-GUIDE.md` | このガイド | ~10KB | 同上 |

### 🔐 APIキー情報（別途保管）
- **Groq API Key** （最重要）
- **HuggingFace Token**
- **OpenAI API Key** （オプション）
- **Claude API Key** （オプション）
- **Gemini API Key** （オプション）

### 📍 推奨バックアップ場所
1. **Google Drive / Dropbox** - クラウドストレージ
2. **GitHub Private Repository** - プライベートリポジトリ
3. **USBメモリ** - 物理バックアップ
4. **別PCまたはサーバー** - 別環境バックアップ

---

## 💻 システム要件

### ✅ サポートOS
- **macOS** 10.15+ (Catalina以降)
- **Ubuntu** 20.04+ LTS
- **Debian** 11+
- **Other Linux** distributions (要調整)

### 🔧 必要ソフトウェア
- **Git** 2.28+
- **インターネット接続** (パッケージダウンロード用)
- **ターミナル/コマンドライン** アクセス

### 💾 ハードウェア要件
- **RAM**: 8GB以上 (推奨16GB)
- **ストレージ**: 10GB以上の空き容量
- **CPU**: x86_64アーキテクチャ (Apple Silicon対応済み)

---

## 🚀 ステップバイステップ復旧

### Phase 1: 緊急バックアップファイル入手
```bash
# 1. クラウドストレージから緊急ファイルをダウンロード
# 2. 以下のファイルを同じディレクトリに配置
#    - voice-roleplay-complete-backup-YYYYMMDD-HHMMSS.bundle
#    - disaster-recovery-setup.sh
#    - DISASTER-RECOVERY-GUIDE.md (このファイル)
```

### Phase 2: 復旧スクリプト実行
```bash
# 実行権限付与
chmod +x disaster-recovery-setup.sh

# 災害復旧スクリプト実行（自動で全環境構築）
./disaster-recovery-setup.sh
```

### Phase 3: 復旧完了確認
```bash
# 復旧されたディレクトリに移動
cd ~/voice-roleplay-dify-restored

# システム確認
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080

# ブラウザで確認
# http://localhost:8080
```

---

## 🔐 APIキー再設定

### 1. 環境変数ファイル設定
```bash
cd ~/voice-roleplay-dify-restored
cp .env.template .env
vim .env  # または好みのエディタで編集
```

### 2. 必須APIキー設定
```bash
# .envファイル内容例
GROQ_API_KEY=gsk_your_actual_groq_key_here
HF_TOKEN=hf_your_actual_huggingface_token_here

# オプション（高機能化のため）
OPENAI_API_KEY=sk-your_actual_openai_key_here
CLAUDE_API_KEY=sk-ant-your_actual_claude_key_here
GEMINI_API_KEY=your_actual_gemini_key_here
```

### 3. APIキー取得先
| サービス | URL | 取得方法 |
|----------|-----|----------|
| **Groq** | https://console.groq.com/keys | アカウント作成 → API Keys → Create |
| **HuggingFace** | https://huggingface.co/settings/tokens | Settings → Access Tokens → New Token |
| **OpenAI** | https://platform.openai.com/api-keys | API Keys → Create new secret key |
| **Claude** | https://console.anthropic.com/ | Console → API Keys → Create Key |
| **Gemini** | https://makersuite.google.com/app/apikey | MakerSuite → Get API Key |

---

## 🛠️ トラブルシューティング

### ❗ よくある問題と解決法

#### 問題1: Python環境エラー
```bash
# 解決法
pyenv install 3.12.11
pyenv global 3.12.11
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

#### 問題2: 依存関係インストールエラー
```bash
# macOSの場合
brew install ffmpeg portaudio sox

# Linuxの場合
sudo apt-get update
sudo apt-get install ffmpeg portaudio19-dev sox libsox-fmt-all
```

#### 問題3: VOICEVOX接続エラー
```bash
# VOICEVOXエンジンダウンロード・起動
# 1. https://voicevox.hiroshiba.jp/ からダウンロード
# 2. アプリケーション起動
# 3. 確認: curl http://localhost:50021/version
```

#### 問題4: 権限エラー
```bash
# ファイル権限修正
chmod +x disaster-recovery-setup.sh
chmod -R 755 ~/voice-roleplay-dify-restored
```

### 🆘 緊急連絡先
復旧に失敗した場合の緊急対応：
1. **Gitバンドル手動展開**: `git clone backup.bundle`
2. **手動環境構築**: `docs/env-setup.md` 参照
3. **コミュニティサポート**: プロジェクトIssues

---

## ✅ 復旧後の確認

### 🎯 システム機能確認チェックリスト

#### Phase 1: 基本動作確認
- [ ] **サーバー起動**: `http://localhost:8080/health` → `{"status":"ok"}`
- [ ] **API確認**: `http://localhost:8080/docs` → Swagger UI表示
- [ ] **仮想環境**: `source venv/bin/activate` → エラーなし

#### Phase 2: 音声機能確認
- [ ] **WhisperX**: `curl http://localhost:8080/speech/models` → モデル一覧表示
- [ ] **VOICEVOX**: `curl http://localhost:50021/version` → バージョン情報

#### Phase 3: AI機能確認
- [ ] **Groq接続**: `curl http://localhost:8080/ai/providers` → プロバイダー一覧
- [ ] **Text分析**: `curl http://localhost:8080/text/supported-formats` → 形式一覧

#### Phase 4: 統合テスト
- [ ] **音声→テキスト変換**: `/speech/transcribe` エンドポイント
- [ ] **AI分析**: `/ai/chat` エンドポイント 
- [ ] **テキスト→音声変換**: `/voice/tts` エンドポイント

### 🎉 復旧成功の証明
すべてのチェックリストが✅になれば、**災害からの完全復旧が成功**です！

---

## 🔄 今後の災害対策

### 💾 定期バックアップ（推奨）
```bash
# 月1回実行推奨
git bundle create voice-roleplay-backup-$(date +%Y%m%d).bundle HEAD

# 複数場所にコピー
cp voice-roleplay-backup-*.bundle /path/to/cloud/storage/
cp voice-roleplay-backup-*.bundle /path/to/usb/drive/
```

### 📱 バックアップ自動化（上級者向け）
```bash
# crontabに追加（月1回自動バックアップ）
0 0 1 * * cd /path/to/project && git bundle create backup-$(date +%Y%m%d).bundle HEAD
```

---

## 📞 緊急時連絡先

**災害復旧に関する問題が発生した場合：**
1. このガイドの手順を再確認
2. `docs/env-setup.md` で詳細設定確認
3. GitHubプロジェクトのIssues作成
4. コミュニティフォーラムで質問

---

**🎯 このガイドがあれば、どんな災害からでも100%復旧可能です！**

*最終更新日: 2025年7月5日* 