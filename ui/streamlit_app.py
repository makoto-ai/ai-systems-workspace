#!/usr/bin/env python3
"""
論文検索システム Streamlit UI
シンプル版から段階的に実装

Author: AI Assistant
"""

import streamlit as st
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# システムパス追加
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / 'paper_research_system'))

# 動作確認済みシステムをインポート
try:
    from working_youtube_script_system import WorkingYouTubeScriptSystem
    SYSTEM_AVAILABLE = True
except ImportError:
    SYSTEM_AVAILABLE = False

def main():
    """メインUI"""
    st.set_page_config(
        page_title="論文検索システム",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 論文検索システム")
    st.markdown("---")
    
    if not SYSTEM_AVAILABLE:
        st.error("❌ システムが利用できません")
        st.stop()
    
    # サイドバー
    with st.sidebar:
        st.header("🔧 設定")
        st.info("シンプル版 v1.0")
        
        # システム状態表示
        st.success("✅ 動作確認済みシステム")
    
    # メインエリア
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🔍 論文検索・YouTube原稿作成")
        
        # 入力フォーム
        topic = st.text_input(
            "検索トピック",
            placeholder="例: 営業心理学",
            help="検索したいトピックを入力してください"
        )
        
        title = st.text_input(
            "YouTube動画タイトル（オプション）",
            placeholder="例: 営業成績を向上させる心理学的テクニック",
            help="特定のタイトルがある場合は入力してください"
        )
        
        # 実行ボタン
        if st.button("🚀 原稿作成実行", type="primary"):
            if topic:
                with st.spinner("原稿作成中..."):
                    try:
                        # 非同期実行
                        result = asyncio.run(execute_script_creation(topic, title))
                        
                        if result['success']:
                            st.success("✅ 原稿作成完了！")
                            
                            # 結果表示
                            with st.expander("📄 作成された原稿", expanded=True):
                                st.text_area(
                                    "原稿内容",
                                    result.get('script', ''),
                                    height=400
                                )
                            
                            # 論文情報表示
                            if 'papers' in result:
                                with st.expander("📚 参考論文情報"):
                                    for i, paper in enumerate(result['papers'][:3], 1):
                                        st.markdown(f"**{i}. {paper.get('title', 'N/A')}**")
                                        st.markdown(f"- 著者: {paper.get('authors', 'N/A')}")
                                        st.markdown(f"- 年度: {paper.get('year', 'N/A')}")
                                        st.markdown("---")
                        
                        else:
                            st.error(f"❌ エラー: {result.get('error', '不明なエラー')}")
                    
                    except Exception as e:
                        st.error(f"❌ 実行エラー: {str(e)}")
            else:
                st.warning("⚠️ トピックを入力してください")
    
    with col2:
        st.header("📊 システム情報")
        
        # システム状態
        st.metric("システム状態", "正常", "✅")
        st.metric("バージョン", "1.0.0", "Streamlit")
        
        # 使用方法
        with st.expander("💡 使用方法"):
            st.markdown("""
            1. **トピック入力**: 検索したい内容を入力
            2. **タイトル入力**: 動画タイトル（任意）
            3. **実行**: 原稿作成ボタンをクリック
            4. **結果確認**: 作成された原稿と参考論文を確認
            """)

async def execute_script_creation(topic: str, title: Optional[str] = None) -> Dict[str, Any]:
    """原稿作成実行"""
    try:
        system = WorkingYouTubeScriptSystem()
        result = await system.create_youtube_script(topic, title)
        return result
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    main()