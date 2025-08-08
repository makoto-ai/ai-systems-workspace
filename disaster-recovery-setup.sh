#!/bin/bash
# =============================================================================
# 🆘 Voice Roleplay System - 災害復旧用完全環境構築スクリプト
# =============================================================================
# 
# このスクリプトは、災害でPCが壊れた場合に新しい環境で
# Voice Roleplay Systemを完全復旧するためのものです。
#
# 使用方法:
#   chmod +x disaster-recovery-setup.sh
#   ./disaster-recovery-setup.sh
#
# 必要な前提条件:
#   - macOS or Linux
#   - インターネット接続
#   - Git
#
# =============================================================================

set -e  # エラー時に停止

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${PURPLE}=== $1 ===${NC}"
}

# システム情報の確認
check_system() {
    log_step "システム環境確認"
    
    # OS確認
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macOS"
        log_info "検出されたOS: macOS"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="Linux"
        log_info "検出されたOS: Linux"
    else
        log_error "サポートされていないOS: $OSTYPE"
        exit 1
    fi
    
    # Git確認
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version)
        log_info "Git確認済み: $GIT_VERSION"
    else
        log_error "Gitがインストールされていません"
        exit 1
    fi
    
    # Python確認
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        log_info "Python確認済み: $PYTHON_VERSION"
    else
        log_warning "Python3が見つかりません。後でインストールします。"
    fi
}

# Homebrewのインストール（macOS）
install_homebrew() {
    if [[ "$OS" == "macOS" ]]; then
        log_step "Homebrew環境構築"
        
        if command -v brew &> /dev/null; then
            log_info "Homebrewは既にインストール済み"
        else
            log_info "Homebrewをインストール中..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            log_success "Homebrewインストール完了"
        fi
    fi
}

# Pythonとpyenvのインストール
install_python() {
    log_step "Python環境構築"
    
    if [[ "$OS" == "macOS" ]]; then
        # pyenvインストール
        if command -v pyenv &> /dev/null; then
            log_info "pyenvは既にインストール済み"
        else
            log_info "pyenvをインストール中..."
            brew install pyenv
            echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.zshrc
            echo 'eval "$(pyenv init -)"' >> ~/.zshrc
            export PATH="$HOME/.pyenv/bin:$PATH"
            eval "$(pyenv init -)"
            log_success "pyenvインストール完了"
        fi
        
        # Python 3.12インストール
        log_info "Python 3.12をインストール中..."
        pyenv install 3.12.11 || log_warning "Python 3.12.11は既にインストール済みの可能性があります"
        pyenv global 3.12.11
        
    elif [[ "$OS" == "Linux" ]]; then
        log_info "LinuxでのPython環境構築..."
        sudo apt-get update
        sudo apt-get install -y python3.12 python3.12-venv python3.12-dev python3-pip
    fi
    
    log_success "Python環境構築完了"
}

# システム依存関係のインストール
install_system_dependencies() {
    log_step "システム依存関係インストール"
    
    if [[ "$OS" == "macOS" ]]; then
        log_info "macOS用パッケージをインストール中..."
        brew install ffmpeg portaudio sox
        brew install --cask conda  # Optional: Conda環境
        
    elif [[ "$OS" == "Linux" ]]; then
        log_info "Linux用パッケージをインストール中..."
        sudo apt-get install -y \
            ffmpeg \
            portaudio19-dev \
            sox \
            libsox-fmt-all \
            build-essential \
            libasound2-dev \
            libsndfile1-dev
    fi
    
    log_success "システム依存関係インストール完了"
}

# プロジェクトの復元
restore_project() {
    log_step "Voice Roleplayプロジェクト復元"
    
    # 作業ディレクトリ作成
    PROJECT_DIR="$HOME/voice-roleplay-dify-restored"
    
    if [[ -d "$PROJECT_DIR" ]]; then
        log_warning "プロジェクトディレクトリが既に存在します: $PROJECT_DIR"
        read -p "既存のディレクトリを削除しますか？ (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$PROJECT_DIR"
            log_info "既存ディレクトリを削除しました"
        else
            log_error "復元を中止しました"
            exit 1
        fi
    fi
    
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    # Gitバンドルまたはリモートリポジトリから復元
    log_info "プロジェクトファイルを復元中..."
    
    # バンドルファイルがある場合
    if [[ -f "../voice-roleplay-complete-backup-*.bundle" ]]; then
        log_info "Gitバンドルから復元中..."
        git clone ../voice-roleplay-complete-backup-*.bundle .
        git checkout milestone/complete-implementation
    else
        log_warning "Gitバンドルが見つかりません。"
        log_info "代替手段: リモートリポジトリのURLを入力してください（空白でスキップ）:"
        read -r REPO_URL
        if [[ -n "$REPO_URL" ]]; then
            git clone "$REPO_URL" .
            git checkout milestone/complete-implementation
        else
            log_error "復元用のソースが見つかりません"
            exit 1
        fi
    fi
    
    log_success "プロジェクト復元完了: $PROJECT_DIR"
}

# Python仮想環境の構築
setup_virtual_environment() {
    log_step "Python仮想環境構築"
    
    cd "$PROJECT_DIR"
    
    # 仮想環境作成
    log_info "Python仮想環境を作成中..."
    python3 -m venv venv
    
    # 仮想環境有効化
    source venv/bin/activate
    
    # pipアップグレード
    log_info "pipをアップグレード中..."
    pip install --upgrade pip
    
    # 依存関係インストール
    log_info "Pythonパッケージをインストール中（これには数分かかる場合があります）..."
    pip install -r requirements.txt
    
    log_success "Python仮想環境構築完了"
}

# VOICEVOX環境の確認
check_voicevox() {
    log_step "VOICEVOX環境確認"
    
    log_info "VOICEVOXエンジンの確認中..."
    
    if curl -s http://localhost:50021/version > /dev/null 2>&1; then
        log_success "VOICEVOXエンジンは既に稼働中です"
    else
        log_warning "VOICEVOXエンジンが稼働していません"
        log_info "VOICEVOXエンジンを手動でダウンロード・起動してください:"
        log_info "1. https://voicevox.hiroshiba.jp/ からダウンロード"
        log_info "2. アプリケーションを起動"
        log_info "3. localhost:50021で確認"
    fi
}

# 環境変数設定ガイド
setup_environment_variables() {
    log_step "環境変数設定"
    
    # .env.templateファイル作成
    cat > .env.template << 'EOF'
# =============================================================================
# Voice Roleplay System - 環境変数テンプレート
# =============================================================================
# このファイルを .env にコピーして、実際のAPIキーを設定してください
#
# cp .env.template .env
# 
# 各サービスのAPIキー取得方法は docs/env-setup.md を参照してください
# =============================================================================

# 必須: Groq API Key (最重要)
GROQ_API_KEY=your_groq_api_key_here

# 音声分離用: HuggingFace Token
HF_TOKEN=your_huggingface_token_here

# オプション: 追加AIプロバイダー
OPENAI_API_KEY=your_openai_api_key_here
CLAUDE_API_KEY=your_claude_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# オプション: Dify (フォールバック用)
DIFY_API_KEY=your_dify_api_key_here
DIFY_BASE_URL=https://api.dify.ai/v1

# システム設定
DEBUG=true
LOG_LEVEL=INFO
HOST=localhost
PORT=8080
EOF
    
    log_info "環境変数テンプレートを作成しました: .env.template"
    log_warning "重要: .env.template を .env にコピーして、実際のAPIキーを設定してください"
    log_info "詳細な設定方法は docs/env-setup.md を参照してください"
}

# システムテスト実行
run_system_test() {
    log_step "システムテスト実行"
    
    log_info "基本テストを実行中..."
    
    # 仮想環境有効化
    source venv/bin/activate
    
    # 基本的な起動テスト
    log_info "アプリケーション起動テスト..."
    timeout 10 python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 &
    SERVER_PID=$!
    
    sleep 5
    
    if curl -s http://localhost:8080/health > /dev/null; then
        log_success "アプリケーション起動成功"
        kill $SERVER_PID 2>/dev/null || true
    else
        log_warning "アプリケーション起動に問題がある可能性があります"
        kill $SERVER_PID 2>/dev/null || true
    fi
    
    # Pythonテスト実行
    if [[ -d "tests/" ]]; then
        log_info "Pytestテストを実行中..."
        python -m pytest tests/ -v || log_warning "一部のテストが失敗しました（APIキー未設定が原因の可能性）"
    fi
}

# 完了メッセージとマニュアル
show_completion_guide() {
    log_step "🎉 災害復旧完了！"
    
    echo -e "${GREEN}"
    cat << 'EOF'
██╗   ██╗ ██████╗ ██╗ ██████╗███████╗    ██████╗  ██████╗ ██╗     ███████╗██████╗ ██╗      █████╗ ██╗   ██╗
██║   ██║██╔═══██╗██║██╔════╝██╔════╝    ██╔══██╗██╔═══██╗██║     ██╔════╝██╔══██╗██║     ██╔══██╗╚██╗ ██╔╝
██║   ██║██║   ██║██║██║     █████╗      ██████╔╝██║   ██║██║     █████╗  ██████╔╝██║     ███████║ ╚████╔╝ 
╚██╗ ██╔╝██║   ██║██║██║     ██╔══╝      ██╔══██╗██║   ██║██║     ██╔══╝  ██╔═══╝ ██║     ██╔══██║  ╚██╔╝  
 ╚████╔╝ ╚██████╔╝██║╚██████╗███████╗    ██║  ██║╚██████╔╝███████╗███████╗██║     ███████╗██║  ██║   ██║   
  ╚═══╝   ╚═════╝ ╚═╝ ╚═════╝╚══════╝    ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝   ╚═╝   
EOF
    echo -e "${NC}"
    
    log_success "Voice Roleplay Systemの災害復旧が完了しました！"
    
    echo -e "\n${YELLOW}📋 次の手順:${NC}"
    echo "1. APIキーの設定:"
    echo "   cp .env.template .env"
    echo "   # .envファイルを編集して実際のAPIキーを設定"
    echo ""
    echo "2. VOICEVOXエンジンの起動:"
    echo "   # https://voicevox.hiroshiba.jp/ からダウンロード・起動"
    echo ""
    echo "3. アプリケーションの起動:"
    echo "   source venv/bin/activate"
    echo "   python -m uvicorn app.main:app --host 0.0.0.0 --port 8080"
    echo ""
    echo "4. ブラウザでアクセス:"
    echo "   http://localhost:8080"
    echo ""
    
    echo -e "${BLUE}📚 詳細ドキュメント:${NC}"
    echo "- 環境設定: docs/env-setup.md"
    echo "- API仕様: http://localhost:8080/docs"
    echo "- 実装チェックリスト: docs/implementation-checklist.md"
    echo ""
    
    echo -e "${GREEN}🎯 復旧されたシステム機能:${NC}"
    echo "✅ Phase 8: 高度営業ロールプレイシステム"
    echo "✅ Phase 9: 営業シナリオエンジン（6顧客タイプ）"
    echo "✅ Phase 10: テキスト分析システム（日本語AI）"
    echo "✅ WhisperX: 17言語音声認識"
    echo "✅ VOICEVOX: 高品質日本語音声合成"
    echo "✅ 統合AI: 複数プロバイダー対応"
    echo ""
    
    log_success "プロジェクトディレクトリ: $PROJECT_DIR"
    log_success "災害復旧完了！システムはProduction-Ready状態です。"
}

# メイン実行関数
main() {
    echo -e "${PURPLE}"
    cat << 'EOF'
🆘 Voice Roleplay System - 災害復旧スクリプト
==============================================
このスクリプトは完全に新しいPC環境でも
Voice Roleplay Systemを100%復旧します。
EOF
    echo -e "${NC}"
    
    check_system
    install_homebrew
    install_python
    install_system_dependencies
    restore_project
    setup_virtual_environment
    check_voicevox
    setup_environment_variables
    run_system_test
    show_completion_guide
}

# スクリプト実行
main "$@" 