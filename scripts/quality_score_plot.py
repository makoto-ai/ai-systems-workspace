"""
BLEU/ROUGEスコアをStreamlit上でマットプロット表示するスクリプト
"""

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Dict, Any, List
import sys
import os

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quality_metrics import get_quality_metrics


class QualityScorePlotter:
    """品質スコアの可視化を行うクラス"""
    
    def __init__(self):
        self.metrics = get_quality_metrics()
    
    def plot_single_comparison(self, reference: str, candidate: str) -> plt.Figure:
        """
        単一比較のプロットを生成
        
        Args:
            reference: 参照テキスト
            candidate: 候補テキスト
        
        Returns:
            matplotlibのFigureオブジェクト
        """
        results = self.metrics.calculate_all_metrics(reference, candidate)
        
        # プロットデータを準備
        metrics_names = ['BLEU', 'ROUGE-1', 'ROUGE-2', 'ROUGE-L', '総合スコア']
        scores = [
            results['bleu_score'],
            results['rouge_scores']['rouge1'],
            results['rouge_scores']['rouge2'],
            results['rouge_scores']['rougeL'],
            results['overall_score']
        ]
        
        # プロットを生成
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 棒グラフ
        bars = ax1.bar(metrics_names, scores, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'])
        ax1.set_title('品質メトリクス比較', fontsize=14, fontweight='bold')
        ax1.set_ylabel('スコア', fontsize=12)
        ax1.set_ylim(0, 1)
        
        # スコア値を棒グラフ上に表示
        for bar, score in zip(bars, scores):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{score:.3f}', ha='center', va='bottom', fontweight='bold')
        
        # レーダーチャート
        angles = np.linspace(0, 2 * np.pi, len(metrics_names), endpoint=False).tolist()
        scores_radar = scores + scores[:1]  # 最初の値を最後にも追加
        angles_radar = angles + angles[:1]
        
        ax2.plot(angles_radar, scores_radar, 'o-', linewidth=2, color='#FF6B6B')
        ax2.fill(angles_radar, scores_radar, alpha=0.25, color='#FF6B6B')
        ax2.set_xticks(angles[:-1])
        ax2.set_xticklabels(metrics_names)
        ax2.set_ylim(0, 1)
        ax2.set_title('レーダーチャート', fontsize=14, fontweight='bold')
        ax2.grid(True)
        
        plt.tight_layout()
        return fig
    
    def plot_multiple_comparisons(self, reference: str, candidates: List[str], candidate_names: List[str] = None) -> plt.Figure:
        """
        複数比較のプロットを生成
        
        Args:
            reference: 参照テキスト
            candidates: 候補テキストのリスト
            candidate_names: 候補テキストの名前リスト
        
        Returns:
            matplotlibのFigureオブジェクト
        """
        if candidate_names is None:
            candidate_names = [f'候補{i+1}' for i in range(len(candidates))]
        
        # 全候補のメトリクスを計算
        all_results = self.metrics.compare_multiple_candidates(reference, candidates)
        
        # プロットデータを準備
        metrics_names = ['BLEU', 'ROUGE-1', 'ROUGE-2', 'ROUGE-L', '総合スコア']
        
        # 各候補のスコアを収集
        scores_data = []
        for result in all_results:
            scores = [
                result['bleu_score'],
                result['rouge_scores']['rouge1'],
                result['rouge_scores']['rouge2'],
                result['rouge_scores']['rougeL'],
                result['overall_score']
            ]
            scores_data.append(scores)
        
        # プロットを生成
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # 棒グラフ（複数候補）
        x = np.arange(len(metrics_names))
        width = 0.8 / len(candidates)
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        
        for i, (scores, name) in enumerate(zip(scores_data, candidate_names)):
            bars = ax1.bar(x + i * width, scores, width, label=name, color=colors[i % len(colors)])
            
            # スコア値を表示
            for bar, score in zip(bars, scores):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        f'{score:.3f}', ha='center', va='bottom', fontsize=8)
        
        ax1.set_xlabel('メトリクス', fontsize=12)
        ax1.set_ylabel('スコア', fontsize=12)
        ax1.set_title('複数候補の品質比較', fontsize=14, fontweight='bold')
        ax1.set_xticks(x + width * (len(candidates) - 1) / 2)
        ax1.set_xticklabels(metrics_names)
        ax1.set_ylim(0, 1)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 総合スコアの比較
        overall_scores = [result['overall_score'] for result in all_results]
        bars = ax2.bar(candidate_names, overall_scores, color=colors[:len(candidates)])
        ax2.set_title('総合スコア比較', fontsize=14, fontweight='bold')
        ax2.set_ylabel('総合スコア', fontsize=12)
        ax2.set_ylim(0, 1)
        
        # スコア値を表示
        for bar, score in zip(bars, overall_scores):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{score:.3f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def plot_trend_analysis(self, reference: str, candidates: List[str], candidate_names: List[str] = None) -> plt.Figure:
        """
        トレンド分析のプロットを生成
        
        Args:
            reference: 参照テキスト
            candidates: 候補テキストのリスト
            candidate_names: 候補テキストの名前リスト
        
        Returns:
            matplotlibのFigureオブジェクト
        """
        if candidate_names is None:
            candidate_names = [f'候補{i+1}' for i in range(len(candidates))]
        
        # 全候補のメトリクスを計算
        all_results = self.metrics.compare_multiple_candidates(reference, candidates)
        
        # プロットデータを準備
        metrics_names = ['BLEU', 'ROUGE-1', 'ROUGE-2', 'ROUGE-L', '総合スコア']
        
        # 各候補のスコアを収集
        scores_matrix = []
        for result in all_results:
            scores = [
                result['bleu_score'],
                result['rouge_scores']['rouge1'],
                result['rouge_scores']['rouge2'],
                result['rouge_scores']['rougeL'],
                result['overall_score']
            ]
            scores_matrix.append(scores)
        
        # プロットを生成
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # ヒートマップ
        scores_array = np.array(scores_matrix).T
        im = ax.imshow(scores_array, cmap='RdYlBu_r', aspect='auto')
        
        # 軸ラベルを設定
        ax.set_xticks(range(len(candidate_names)))
        ax.set_xticklabels(candidate_names, rotation=45)
        ax.set_yticks(range(len(metrics_names)))
        ax.set_yticklabels(metrics_names)
        
        # カラーバーを追加
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('スコア', rotation=270, labelpad=15)
        
        # セルに値を表示
        for i in range(len(metrics_names)):
            for j in range(len(candidate_names)):
                text = ax.text(j, i, f'{scores_array[i, j]:.3f}',
                             ha="center", va="center", color="black", fontweight='bold')
        
        ax.set_title('品質メトリクス ヒートマップ', fontsize=14, fontweight='bold')
        plt.tight_layout()
        return fig


def create_streamlit_plot_interface():
    """Streamlit用のプロットインターフェースを作成"""
    st.title("📊 品質メトリクス可視化")
    
    plotter = QualityScorePlotter()
    
    # サイドバーでプロットタイプを選択
    plot_type = st.sidebar.selectbox(
        "プロットタイプを選択",
        ["単一比較", "複数比較", "トレンド分析"]
    )
    
    if plot_type == "単一比較":
        st.header("単一比較")
        
        reference = st.text_area("参照テキスト", height=150)
        candidate = st.text_area("候補テキスト", height=150)
        
        if st.button("プロット生成") and reference and candidate:
            fig = plotter.plot_single_comparison(reference, candidate)
            st.pyplot(fig)
            
            # 詳細分析も表示
            analysis = plotter.metrics.get_detailed_analysis(reference, candidate)
            st.subheader("詳細分析")
            st.json(analysis)
    
    elif plot_type == "複数比較":
        st.header("複数比較")
        
        reference = st.text_area("参照テキスト", height=100)
        
        num_candidates = st.sidebar.slider("候補数", 2, 5, 3)
        
        candidates = []
        candidate_names = []
        
        for i in range(num_candidates):
            col1, col2 = st.columns(2)
            with col1:
                candidate = st.text_area(f"候補{i+1}", height=100, key=f"candidate_{i}")
                candidates.append(candidate)
            with col2:
                name = st.text_input(f"候補{i+1}の名前", value=f"候補{i+1}", key=f"name_{i}")
                candidate_names.append(name)
        
        if st.button("プロット生成") and reference and all(candidates):
            fig = plotter.plot_multiple_comparisons(reference, candidates, candidate_names)
            st.pyplot(fig)
    
    elif plot_type == "トレンド分析":
        st.header("トレンド分析")
        
        reference = st.text_area("参照テキスト", height=100)
        
        num_candidates = st.sidebar.slider("候補数", 3, 6, 4)
        
        candidates = []
        candidate_names = []
        
        for i in range(num_candidates):
            col1, col2 = st.columns(2)
            with col1:
                candidate = st.text_area(f"候補{i+1}", height=100, key=f"trend_candidate_{i}")
                candidates.append(candidate)
            with col2:
                name = st.text_input(f"候補{i+1}の名前", value=f"候補{i+1}", key=f"trend_name_{i}")
                candidate_names.append(name)
        
        if st.button("ヒートマップ生成") and reference and all(candidates):
            fig = plotter.plot_trend_analysis(reference, candidates, candidate_names)
            st.pyplot(fig)


if __name__ == "__main__":
    # テスト用のサンプルデータ
    reference_text = """
    本研究では、機械学習技術を用いて営業活動の効率化を図る手法を提案する。
    顧客データの分析により、成約率を30%向上させることに成功した。
    特に、顧客の購買行動パターンを分析することで、最適なアプローチタイミングを
    特定できることが明らかになった。
    """
    
    candidate_texts = [
        """
        機械学習を使った営業効率化の研究について説明します。
        顧客データを分析して、成約率を30%上げることに成功しました。
        顧客の購買パターンを分析して、最適なアプローチのタイミングを
        見つけることができるようになりました。
        """,
        """
        営業効率化のための機械学習研究を紹介します。
        データ分析により成約率が30%向上しました。
        購買パターン分析でアプローチタイミングを最適化できます。
        """,
        """
        本研究は営業効率化のための機械学習手法を提案します。
        顧客データ分析で成約率30%向上を実現しました。
        購買行動パターン分析により最適アプローチタイミングを特定しました。
        """
    ]
    
    candidate_names = ["詳細版", "簡潔版", "学術版"]
    
    # プロットテスト
    plotter = QualityScorePlotter()
    
    print("単一比較プロット:")
    fig1 = plotter.plot_single_comparison(reference_text, candidate_texts[0])
    plt.show()
    
    print("複数比較プロット:")
    fig2 = plotter.plot_multiple_comparisons(reference_text, candidate_texts, candidate_names)
    plt.show()
    
    print("トレンド分析プロット:")
    fig3 = plotter.plot_trend_analysis(reference_text, candidate_texts, candidate_names)
    plt.show() 