"""
StreamlitメインUI
アップロード→原稿生成→評価→スコア出力 まで一貫で処理
"""

import streamlit as st
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.prompt_generator import PaperMetadata, create_prompt_from_metadata
from modules.composer import compose_script, compose_from_json
from quality_metrics import get_quality_metrics
from scripts.quality_score_plot import QualityScorePlotter


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


def main():
    """メインアプリケーション"""
    st.set_page_config(
        page_title="論文→YouTube原稿生成システム",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 論文→YouTube原稿生成システム")
    st.markdown("---")
    
    # サイドバーで機能を選択
    page = st.sidebar.selectbox(
        "機能を選択",
        ["原稿生成", "品質評価", "可視化", "サンプル実行"]
    )
    
    if page == "原稿生成":
        show_script_generation_page()
    elif page == "品質評価":
        show_quality_evaluation_page()
    elif page == "可視化":
        show_visualization_page()
    elif page == "サンプル実行":
        show_sample_execution_page()


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
    style = st.selectbox(
        "原稿スタイル",
        ["popular", "academic", "business", "educational"],
        format_func=lambda x: {
            "popular": "一般向け",
            "academic": "学術的",
            "business": "ビジネス向け",
            "educational": "教育的"
        }[x]
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
        script = compose_script(metadata, abstract, style)
        
        st.subheader("生成された原稿")
        st.text_area("原稿内容", script, height=400)
        
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
            
            style = st.selectbox(
                "原稿スタイル",
                ["popular", "academic", "business", "educational"],
                format_func=lambda x: {
                    "popular": "一般向け",
                    "academic": "学術的",
                    "business": "ビジネス向け",
                    "educational": "教育的"
                }[x]
            )
            
            if st.button("原稿生成") and abstract:
                script = compose_from_json(uploaded_file.name, abstract, style)
                
                st.subheader("生成された原稿")
                st.text_area("原稿内容", script, height=400)
                
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
    
    style = st.selectbox(
        "原稿スタイル",
        ["popular", "academic", "business", "educational"],
        format_func=lambda x: {
            "popular": "一般向け",
            "academic": "学術的",
            "business": "ビジネス向け",
            "educational": "教育的"
        }[x]
    )
    
    if st.button("サンプル原稿生成"):
        script = compose_script(metadata, metadata.abstract, style)
        
        st.subheader("生成された原稿")
        st.text_area("原稿内容", script, height=400)
        
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
    
    if st.button("サンプル実行開始"):
        with st.spinner("サンプル実行中..."):
            # サンプルデータを読み込み
            metadata = load_sample_metadata()
            
            # 原稿生成
            script = compose_script(metadata, metadata.abstract, "popular")
            
            # 品質評価
            metrics = get_quality_metrics()
            results = metrics.calculate_all_metrics(metadata.abstract, script)
            
            # 結果表示
            st.subheader("生成された原稿")
            st.text_area("原稿", script, height=300)
            
            st.subheader("品質評価結果")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("BLEUスコア", f"{results['bleu_score']:.3f}")
            
            with col2:
                st.metric("総合スコア", f"{results['overall_score']:.3f}")
            
            with col3:
                st.metric("評価", results['assessment'])
            
            st.success("サンプル実行が完了しました！")


if __name__ == "__main__":
    main() 