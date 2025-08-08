# 🆘 究極の災害復旧ガイド - PC破損・Cursor暴走対応

## 📋 対応ケース
- **PC完全破損・紛失**
- **ハードドライブクラッシュ**  
- **Cursor暴走によるホームディレクトリ削除**
- **ランサムウェア・ウイルス感染**
- **システム完全フォーマット**

## 🚀 30分完全復旧手順

### Step 1: 基本環境準備 (5分)
```bash
# 新しいMac/PCで実行
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install git pyenv node
```

### Step 2: プロジェクト復旧 (5分)  
```bash
cd ~
git clone https://github.com/makoto-ai/voice-roleplay-system.git
cd voice-roleplay-system
```

### Step 3: Python環境復旧 (10分)
```bash
pyenv install 3.12.8
pyenv local 3.12.8  
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Node.js環境復旧 (5分)
```bash
cd frontend/voice-roleplay-frontend
npm ci
cd ../../
```

### Step 5: 自動復旧システム起動 (3分)
```bash
./auto-start-on-open-complete.sh
```

### Step 6: 確認・完了 (2分)
```bash
npm run check-automation
npm run status
npm run integrity-check
```

## 🎯 復旧後の状態
- ✅ 基本開発環境完全復旧
- ✅ 4大自動化システム稼働
- ✅ 13個の自動化スクリプト実行可能
- ✅ Cursor自動復旧設定有効
- ✅ 全データ・設定完全復元

## 💾 復旧データソース
1. **GitHub Repository**: 全ソースコード・設定
2. **依存関係定義**: requirements.txt, package-lock.json
3. **自動化スクリプト**: 13個の.shファイル
4. **Cursor設定**: .vscode/以下全ファイル
5. **GitHub Actions**: 5個のワークフロー

## 🔒 APIキー再設定（必要時）
```bash
# .envファイルに再設定
GROQ_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here  
ANTHROPIC_API_KEY=your_key_here
GOOGLE_GENERATIVE_AI_API_KEY=your_key_here
```

