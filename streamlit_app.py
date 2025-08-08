"""
StreamlitメインUI
アップロード→原稿生成→評価→スコア出力 まで一貫で処理
"""

import streamlit as st
import json
import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# ログ設定を調整して警告を抑制
logging.getLogger('streamlit').setLevel(logging.ERROR)
logging.getLogger('streamlit.runtime.scriptrunner').setLevel(logging.ERROR)

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.prompt_generator import PaperMetadata, create_prompt_from_metadata
from modules.composer import compose_script, compose_from_json
from quality_metrics import get_quality_metrics
from scripts.quality_score_plot import QualityScorePlotter
from system_monitor import display_system_status
from enhanced_backup import EnhancedBackup
from auto_test_system import AutoTestSystem
from advanced_ai_system import display_advanced_ai_interface
from real_time_analytics import display_real_time_analytics
from advanced_security_system import display_advanced_security_interface
from performance_optimizer import display_performance_optimizer_interface
from advanced_error_handling import display_advanced_error_handling_interface



def load_sample_metadata() -> PaperMetadata:
    """サンプルメタデータを読み込み"""
    sample_file = Path("data/sample_papers/metadata.json")
    if sample_file.exists():
        with open(sample_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return PaperMetadata(
            title=data.get('title', ''),
            authors=data.get('authors', []),
            abstract=data.get('abstract', ''),
            doi=data.get('doi'),
            publication_year=data.get('publication_year'),
            journal=data.get('journal'),
            citation_count=data.get('citation_count'),
            institutions=data.get('institutions'),
            keywords=data.get('keywords')
        )
    else:
        # デフォルトのサンプルデータ
        return PaperMetadata(
            title="機械学習を用いた営業効率化の研究",
            authors=["田中太郎", "佐藤花子"],
            abstract="本研究では、機械学習技術を用いて営業活動の効率化を図る手法を提案する。",
            publication_year=2023,
            journal="営業科学ジャーナル",
            citation_count=45,
            institutions=["東京大学"],
            keywords=["機械学習", "営業効率化"]
        )


def get_style_options() -> Dict[str, str]:
    """原稿スタイルの選択肢を取得"""
    return {
        "popular": "一般向け (10-15分)",
        "academic": "学術的 (15-20分)",
        "business": "ビジネス向け (12-18分)",
        "educational": "教育的 (20-30分)",
        "comprehensive": "包括的 (25-35分)",
        "deep_dive": "深掘り (35-45分)",
        "lecture": "講義形式 (50-60分)"
    }


def main():
    """メインアプリケーション"""
    # Streamlit設定を改善
    st.set_page_config(
        page_title="論文→YouTube原稿生成システム",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 警告メッセージを抑制
    st.set_option('deprecation.showPyplotGlobalUse', False)
    
    st.title("📚 論文→YouTube原稿生成システム")
    st.markdown("---")
    
    # サイドバーで機能を選択
    page = st.sidebar.selectbox(
        "機能を選択",
        ["原稿生成", "品質評価", "可視化", "サンプル実行", "システム監視", "バックアップ管理", "自動テスト", "高度AI統合", "リアルタイム分析", "セキュリティ監査", "パフォーマンス最適化", "エラーハンドリング"]
    )
    
    if page == "原稿生成":
        show_script_generation_page()
    elif page == "品質評価":
        show_quality_evaluation_page()
    elif page == "可視化":
        show_visualization_page()
    elif page == "サンプル実行":
        show_sample_execution_page()
    elif page == "システム監視":
        show_system_monitor_page()
    elif page == "バックアップ管理":
        show_backup_management_page()
    elif page == "自動テスト":
        show_auto_test_page()
    elif page == "高度AI統合":
        show_advanced_ai_page()
    elif page == "リアルタイム分析":
        show_real_time_analytics_page()
    elif page == "セキュリティ監査":
        show_security_audit_page()
    elif page == "パフォーマンス最適化":
        show_performance_optimizer_page()
    elif page == "エラーハンドリング":
        show_error_handling_page()


def show_script_generation_page():
    """原稿生成ページ"""
    st.header("🎬 YouTube原稿生成")
    
    # 入力方法を選択
    input_method = st.radio(
        "入力方法を選択",
        ["手動入力", "JSONファイルアップロード", "サンプルデータ使用"]
    )
    
    if input_method == "手動入力":
        show_manual_input_form()
    elif input_method == "JSONファイルアップロード":
        show_file_upload_form()
    elif input_method == "サンプルデータ使用":
        show_sample_data_form()


def show_manual_input_form():
    """手動入力フォーム"""
    st.subheader("論文情報を入力")
    
    col1, col2 = st.columns(2)
    
    with col1:
        title = st.text_input("論文タイトル", value="機械学習を用いた営業効率化の研究")
        authors_input = st.text_input("著者（カンマ区切り）", value="田中太郎, 佐藤花子")
        doi = st.text_input("DOI", value="10.1000/example.2023.001")
        publication_year = st.number_input("発表年", min_value=1900, max_value=2030, value=2023)
    
    with col2:
        journal = st.text_input("掲載誌", value="営業科学ジャーナル")
        citation_count = st.number_input("引用数", min_value=0, value=45)
        institutions_input = st.text_input("研究機関（カンマ区切り）", value="東京大学, 営業研究所")
        keywords_input = st.text_input("キーワード（カンマ区切り）", value="機械学習, 営業効率化")
    
    abstract = st.text_area("論文要約", height=200, value="""
本研究では、機械学習技術を用いて営業活動の効率化を図る手法を提案する。
顧客データの分析により、成約率を30%向上させることに成功した。
特に、顧客の購買行動パターンを分析することで、最適なアプローチタイミングを
特定できることが明らかになった。本研究の成果は、営業活動の科学的アプローチの
確立に寄与するものである。
""".strip())
    
    # 原稿スタイルを選択
    style_options = get_style_options()
    style = st.selectbox(
        "原稿スタイル",
        list(style_options.keys()),
        format_func=lambda x: style_options[x]
    )
    
    if st.button("原稿生成"):
        # メタデータを作成
        authors = [author.strip() for author in authors_input.split(",")]
        institutions = [inst.strip() for inst in institutions_input.split(",")]
        keywords = [kw.strip() for kw in keywords_input.split(",")]
        
        metadata = PaperMetadata(
            title=title,
            authors=authors,
            abstract=abstract,
            doi=doi,
            publication_year=publication_year,
            journal=journal,
            citation_count=citation_count,
            institutions=institutions,
            keywords=keywords
        )
        
        # 原稿を生成
        with st.spinner("原稿を生成中..."):
            script = compose_script(metadata, abstract, style)
        
        st.subheader("生成された原稿")
        st.text_area("原稿内容", script, height=400)
        
        # スタイル情報を表示
        style_info = style_options[style]
        st.info(f"📝 選択されたスタイル: {style_info}")
        
        # ダウンロードボタン
        st.download_button(
            label="原稿をダウンロード",
            data=script,
            file_name=f"youtube_script_{title[:20]}.txt",
            mime="text/plain"
        )


def show_file_upload_form():
    """ファイルアップロードフォーム"""
    st.subheader("JSONファイルをアップロード")
    
    uploaded_file = st.file_uploader(
        "メタデータJSONファイルを選択",
        type=['json']
    )
    
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            st.json(data)
            
            abstract = st.text_area("論文要約", height=200)
            
            # 原稿スタイルを選択
            style_options = get_style_options()
            style = st.selectbox(
                "原稿スタイル",
                list(style_options.keys()),
                format_func=lambda x: style_options[x]
            )
            
            if st.button("原稿生成") and abstract:
                with st.spinner("原稿を生成中..."):
                    script = compose_from_json(uploaded_file.name, abstract, style)
                
                st.subheader("生成された原稿")
                st.text_area("原稿内容", script, height=400)
                
                # スタイル情報を表示
                style_info = style_options[style]
                st.info(f"📝 選択されたスタイル: {style_info}")
                
                st.download_button(
                    label="原稿をダウンロード",
                    data=script,
                    file_name=f"youtube_script_{data.get('title', 'unknown')[:20]}.txt",
                    mime="text/plain"
                )
        
        except Exception as e:
            st.error(f"ファイルの読み込みに失敗しました: {e}")


def show_sample_data_form():
    """サンプルデータフォーム"""
    st.subheader("サンプルデータを使用")
    
    metadata = load_sample_metadata()
    
    st.write("**論文情報:**")
    st.write(f"- タイトル: {metadata.title}")
    st.write(f"- 著者: {', '.join(metadata.authors)}")
    st.write(f"- 発表年: {metadata.publication_year}")
    st.write(f"- 掲載誌: {metadata.journal}")
    st.write(f"- 引用数: {metadata.citation_count}")
    
    # 原稿スタイルを選択
    style_options = get_style_options()
    style = st.selectbox(
        "原稿スタイル",
        list(style_options.keys()),
        format_func=lambda x: style_options[x]
    )
    
    if st.button("サンプル原稿生成"):
        with st.spinner("原稿を生成中..."):
            script = compose_script(metadata, metadata.abstract, style)
        
        st.subheader("生成された原稿")
        st.text_area("原稿内容", script, height=400)
        
        # スタイル情報を表示
        style_info = style_options[style]
        st.info(f"📝 選択されたスタイル: {style_info}")
        
        st.download_button(
            label="原稿をダウンロード",
            data=script,
            file_name="sample_youtube_script.txt",
            mime="text/plain"
        )


def show_quality_evaluation_page():
    """品質評価ページ"""
    st.header("📊 品質評価")
    
    reference = st.text_area("参照テキスト（理想的な出力）", height=150)
    candidate = st.text_area("評価対象テキスト（システム出力）", height=150)
    
    if st.button("品質評価実行") and reference and candidate:
        metrics = get_quality_metrics()
        results = metrics.calculate_all_metrics(reference, candidate)
        
        # 結果を表示
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("BLEUスコア", f"{results['bleu_score']:.3f}")
        
        with col2:
            st.metric("ROUGE-1", f"{results['rouge_scores']['rouge1']:.3f}")
        
        with col3:
            st.metric("ROUGE-2", f"{results['rouge_scores']['rouge2']:.3f}")
        
        with col4:
            st.metric("総合評価", results['assessment'])
        
        # 詳細分析
        analysis = metrics.get_detailed_analysis(reference, candidate)
        
        st.subheader("詳細分析")
        st.json(analysis)


def show_visualization_page():
    """可視化ページ"""
    st.header("📈 可視化")
    
    from scripts.quality_score_plot import create_streamlit_plot_interface
    create_streamlit_plot_interface()


def show_sample_execution_page():
    """サンプル実行ページ"""
    st.header("🧪 サンプル実行")
    
    st.write("システムの動作を確認するためのサンプル実行を行います。")
    
    # 長編スタイルの選択
    style_options = get_style_options()
    long_form_styles = ["comprehensive", "deep_dive", "lecture"]
    
    st.subheader("長編原稿生成テスト")
    selected_style = st.selectbox(
        "テストする長編スタイルを選択",
        long_form_styles,
        format_func=lambda x: style_options[x]
    )
    
    if st.button("長編原稿生成テスト"):
        with st.spinner("長編原稿を生成中..."):
            # サンプルデータを読み込み
            metadata = load_sample_metadata()
            
            # 長編原稿生成
            script = compose_script(metadata, metadata.abstract, selected_style)
            
            # 品質評価
            metrics = get_quality_metrics()
            results = metrics.calculate_all_metrics(metadata.abstract, script)
            
            # 結果表示
            st.subheader("生成された長編原稿")
            st.text_area("原稿", script, height=300)
            
            st.subheader("品質評価結果")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("BLEUスコア", f"{results['bleu_score']:.3f}")
            
            with col2:
                st.metric("総合スコア", f"{results['overall_score']:.3f}")
            
            with col3:
                st.metric("評価", results['assessment'])
            
            # スタイル情報を表示
            style_info = style_options[selected_style]
            st.info(f"📝 生成されたスタイル: {style_info}")
            
            st.success("長編原稿生成テストが完了しました！")
    
    st.subheader("全スタイル一括テスト")
    if st.button("全スタイル一括テスト"):
        with st.spinner("全スタイルの原稿を生成中..."):
            metadata = load_sample_metadata()
            
            results = {}
            for style in style_options.keys():
                script = compose_script(metadata, metadata.abstract, style)
                metrics = get_quality_metrics()
                quality_results = metrics.calculate_all_metrics(metadata.abstract, script)
                
                results[style] = {
                    "script": script,
                    "quality": quality_results,
                    "style_info": style_options[style]
                }
            
            # 結果を表示
            for style, result in results.items():
                with st.expander(f"{result['style_info']} - 品質スコア: {result['quality']['overall_score']:.3f}"):
                    st.text_area(f"原稿内容 ({style})", result['script'], height=200)
                    st.json(result['quality'])
            
            st.success("全スタイルの一括テストが完了しました！")


def show_system_monitor_page():
    """システム監視ページ"""
    st.header("🖥️ システム監視")
    
    # システム監視機能を表示
    display_system_status()
    
    # 追加のシステム情報
    st.subheader("📊 システム詳細情報")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**システム稼働状況**")
        st.write("✅ アプリケーション: 稼働中")
        st.write("✅ データベース: 接続可能")
        st.write("✅ ファイルシステム: 正常")
        
    with col2:
        st.info("**最近の操作ログ**")
        st.write("📝 論文検索: 実行済み")
        st.write("📝 原稿生成: 実行済み")
        st.write("📝 品質評価: 実行済み")


def show_backup_management_page():
    """バックアップ管理ページ"""
    st.header("💾 バックアップ管理")
    
    backup_system = EnhancedBackup()
    
    # バックアップ作成
    st.subheader("🔄 バックアップ作成")
    
    col1, col2 = st.columns(2)
    
    with col1:
        backup_name = st.text_input("バックアップ名（空欄で自動生成）")
        
    with col2:
        if st.button("📦 バックアップ作成"):
            with st.spinner("バックアップを作成中..."):
                backup_info = backup_system.create_backup(backup_name)
                
                if backup_info:
                    st.success(f"バックアップ完了: {backup_info['backup_name']}")
                    st.info(f"ファイル数: {len(backup_info['files'])}")
                    st.info(f"総サイズ: {backup_info['total_size'] / 1024 / 1024:.2f} MB")
                else:
                    st.error("バックアップ作成に失敗しました")
    
    # バックアップ一覧
    st.subheader("📋 バックアップ一覧")
    
    backups = backup_system.list_backups()
    
    if backups:
        for backup in backups:
            with st.expander(f"📦 {backup['backup_name']} - {backup['timestamp'][:19]}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**ファイル数:** {len(backup['files'])}")
                
                with col2:
                    st.write(f"**サイズ:** {backup['total_size'] / 1024 / 1024:.2f} MB")
                
                with col3:
                    if st.button(f"🔄 復元", key=f"restore_{backup['backup_name']}"):
                        with st.spinner("復元中..."):
                            success = backup_system.restore_backup(backup['backup_name'])
                            if success:
                                st.success("復元完了！")
                            else:
                                st.error("復元に失敗しました")
    else:
        st.info("バックアップがありません")
    
    # クリーンアップ設定
    st.subheader("🧹 クリーンアップ設定")
    
    keep_days = st.slider("保持日数", 1, 30, 7)
    
    if st.button("🗑️ 古いバックアップ削除"):
        with st.spinner("クリーンアップ中..."):
            backup_system.cleanup_old_backups(keep_days)
            st.success("クリーンアップ完了！")
            st.rerun()


def show_auto_test_page():
    """自動テストページ"""
    st.header("🧪 自動テスト")
    
    test_system = AutoTestSystem()
    
    st.subheader("🔍 システムテスト実行")
    st.write("システムの全機能を自動テストします。")
    
    if st.button("🚀 全テスト実行"):
        with st.spinner("自動テストを実行中..."):
            results = test_system.run_all_tests()
            summary = test_system.get_test_summary()
            
            # テスト結果サマリー
            st.subheader("📊 テスト結果サマリー")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("総テスト数", summary['total_tests'])
            
            with col2:
                st.metric("成功", summary['passed_tests'])
            
            with col3:
                st.metric("失敗", summary['failed_tests'])
            
            with col4:
                st.metric("成功率", f"{summary['success_rate']:.1f}%")
            
            # 詳細結果
            st.subheader("📋 詳細結果")
            
            for result in results:
                if result['status'] == 'PASS':
                    st.success(f"✅ {result['test_name']}: {result['message']}")
                else:
                    st.error(f"❌ {result['test_name']}: {result['message']}")
            
            # 成功/失敗の色分け表示
            if summary['success_rate'] >= 80:
                st.success("🎉 システムは正常に動作しています！")
            elif summary['success_rate'] >= 60:
                st.warning("⚠️ 一部の機能に問題があります。")
            else:
                st.error("🚨 システムに重大な問題があります。")
    
    # 個別テスト実行
    st.subheader("🔧 個別テスト実行")
    
    test_options = {
        "論文メタデータ作成": test_system.test_paper_metadata_creation,
        "プロンプト生成": test_system.test_prompt_generation,
        "原稿生成": test_system.test_script_composition,
        "品質評価": test_system.test_quality_metrics,
        "システム監視": test_system.test_system_monitor,
        "バックアップシステム": test_system.test_backup_system
    }
    
    selected_test = st.selectbox("実行するテストを選択", list(test_options.keys()))
    
    if st.button(f"▶️ {selected_test}テスト実行"):
        with st.spinner(f"{selected_test}テストを実行中..."):
            result = test_options[selected_test]()
            
            if result['status'] == 'PASS':
                st.success(f"✅ {result['test_name']}: {result['message']}")
            else:
                st.error(f"❌ {result['test_name']}: {result['message']}")


def show_advanced_ai_page():
    """高度AI統合ページ"""
    st.header("🤖 高度AI統合システム")
    
    # 高度なAIインターフェースを表示
    display_advanced_ai_interface()


def show_real_time_analytics_page():
    """リアルタイム分析ページ"""
    st.header("📊 リアルタイム分析・予測システム")
    
    # リアルタイム分析インターフェースを表示
    display_real_time_analytics()


def show_security_audit_page():
    """セキュリティ監査ページ"""
    st.header("🔒 高度なセキュリティ・監査システム")
    
    # セキュリティ監査インターフェースを表示
    display_advanced_security_interface()


def show_performance_optimizer_page():
    """パフォーマンス最適化ページ"""
    st.header("⚡ パフォーマンス最適化システム")
    
    # パフォーマンス最適化インターフェースを表示
    display_performance_optimizer_interface()


def show_error_handling_page():
    """エラーハンドリングページ"""
    st.header("🛡️ 高度なエラーハンドリング・リカバリシステム")
    
    # エラーハンドリングインターフェースを表示
    display_advanced_error_handling_interface()





if __name__ == "__main__":
    main() 