#!/usr/bin/env python3
"""
Golden Test KPI Dashboard
Streamlit-based visualization for Golden Test metrics
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timedelta
import re

# ページ設定
st.set_page_config(
    page_title="Golden Test KPI Dashboard",
    page_icon="🎯",
    layout="wide"
)

def load_golden_logs():
    """Golden Testのログを読み込み"""
    logs_dir = Path("tests/golden/logs")
    if not logs_dir.exists():
        return pd.DataFrame()
    
    all_data = []
    for log_file in logs_dir.glob("*.jsonl"):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        # ファイル名から日時を抽出
                        date_str = log_file.stem  # 20250829_211416
                        try:
                            date_obj = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                            data['timestamp'] = date_obj
                            data['date'] = date_obj.date()
                            all_data.append(data)
                        except ValueError:
                            continue
        except Exception as e:
            st.error(f"ログファイル読み込みエラー: {log_file}: {e}")
            continue
    
    return pd.DataFrame(all_data)

def load_observation_log():
    """観測ログから週次データを抽出"""
    log_file = Path("tests/golden/observation_log.md")
    if not log_file.exists():
        return pd.DataFrame()
    
    weekly_data = []
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 週次観測セクションを抽出
        pattern = r'## (\d{4}-\d{2}-\d{2}) - 週次観測.*?合格率.*?(\d+)/(\d+) \((\d+)%\)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for match in matches:
            date_str, passed, total, percentage = match
            
            # 該当セクションからfreshness情報を抽出
            section_pattern = rf'## {re.escape(date_str)} - 週次観測(.*?)(?=## |\Z)'
            section_match = re.search(section_pattern, content, re.DOTALL)
            
            new_failures = 0
            total_failures = 0
            
            if section_match:
                section_content = section_match.group(1)
                # 失敗分析セクションを検索
                failure_matches = re.findall(r'- \*\*([^*]+)\*\*: `root_cause:([^`]+)`(?:\s*\|\s*`freshness:([^`]+)`)?', section_content)
                for case_id, root_cause, freshness in failure_matches:
                    total_failures += 1
                    if freshness == "NEW":
                        new_failures += 1
            
            new_fail_ratio = new_failures / max(total_failures, 1) if total_failures > 0 else 0.0
            
            weekly_data.append({
                'date': datetime.strptime(date_str, "%Y-%m-%d").date(),
                'passed': int(passed),
                'total': int(total),
                'pass_rate': int(percentage),
                'total_failures': total_failures,
                'new_failures': new_failures,
                'new_fail_ratio': new_fail_ratio
            })
    
    except Exception as e:
        st.error(f"観測ログ読み込みエラー: {e}")
    
    return pd.DataFrame(weekly_data)

def analyze_failure_reasons(df):
    """失敗理由の分析（Root Cause分析含む）"""
    failed_cases = df[df['passed'] == False]
    if failed_cases.empty:
        return pd.DataFrame()
    
    failure_analysis = []
    for _, case in failed_cases.iterrows():
        ref_words = set(case['reference'].split())
        pred_words = set(case['prediction'].split()) if case['prediction'] else set()
        
        missing_words = ref_words - pred_words
        extra_words = pred_words - ref_words
        
        # Root Cause分析（簡易版）
        root_cause = analyze_root_cause(case['score'], missing_words, pred_words)
        
        failure_analysis.append({
            'case_id': case['id'],
            'score': case['score'],
            'missing_words': ', '.join(missing_words) if missing_words else 'なし',
            'extra_words': ', '.join(extra_words) if extra_words else 'なし',
            'missing_count': len(missing_words),
            'root_cause': root_cause,
            'date': case.get('date', 'Unknown')
        })
    
    return pd.DataFrame(failure_analysis)

def analyze_root_cause(score, missing_words, pred_words):
    """Root Cause簡易分析"""
    if not pred_words:
        return "INFRA"
    elif score == 0:
        return "MODEL"
    elif score < 0.3 and missing_words:
        return "NORMALIZE"
    elif score < 0.7:
        return "TOKENIZE"
    else:
        return "FLAKY"

def calculate_flaky_rate(df):
    """Flaky率の計算"""
    if df.empty:
        return 0.0
    
    failed_cases = df[df['passed'] == False]
    if failed_cases.empty:
        return 0.0
    
    # スコア0.7以上の失敗をFlakyと判定
    flaky_cases = failed_cases[failed_cases['score'] >= 0.7]
    return len(flaky_cases) / len(failed_cases) * 100

def load_shadow_evaluation():
    """Shadow Evaluation結果を読み込み（段階昇格対応）"""
    
    # 段階昇格用グリッドファイルを最優先
    grid_file = Path("out/shadow_grid.json") 
    if grid_file.exists():
        try:
            with open(grid_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            multi_eval = data.get("multi_shadow_evaluation", {})
            thresholds = multi_eval.get("thresholds", {})
            staged_promotion = multi_eval.get("staged_promotion", {})
            
            # グリッド評価結果を取得
            grid_data = {}
            for threshold_str, threshold_data in thresholds.items():
                threshold = float(threshold_str)
                pass_rate = threshold_data.get("weighted_pass_rate", threshold_data.get("shadow_pass_rate", 0))
                grid_data[threshold_str] = pass_rate
            
            return {
                "0.7": grid_data.get("0.7", grid_data.get("0.70", 0)),
                "0.85": grid_data.get("0.85", 0),
                "grid": grid_data,
                "staged_promotion": staged_promotion,
                "weighted": any(thresholds[t].get("weighted_pass_rate") is not None for t in thresholds),
                "multi": True,
                "grid_enabled": True
            }
        except Exception as e:
            st.error(f"Grid evaluation読み込みエラー: {e}")
    
    # マルチシャドー評価ファイルを次に確認
    multi_shadow_file = Path("out/shadow_multi.json")
    if multi_shadow_file.exists():
        try:
            with open(multi_shadow_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            multi_eval = data.get("multi_shadow_evaluation", {})
            thresholds = multi_eval.get("thresholds", {})
            
            # 0.7と0.85の結果を取得（重み付き優先）
            threshold_0_7 = thresholds.get("0.7", {})
            threshold_0_85 = thresholds.get("0.85", {})
            
            shadow_0_7 = threshold_0_7.get("weighted_pass_rate", threshold_0_7.get("shadow_pass_rate", 0))
            shadow_0_85 = threshold_0_85.get("weighted_pass_rate", threshold_0_85.get("shadow_pass_rate", 0))
            
            return {
                "0.7": shadow_0_7,
                "0.85": shadow_0_85,
                "weighted": threshold_0_85.get("weighted_pass_rate") is not None,
                "multi": True,
                "grid_enabled": False
            }
        except Exception as e:
            st.error(f"Multi-shadow evaluation読み込みエラー: {e}")
    
    # 従来の0.7単体ファイルをフォールバック
    shadow_file = Path("out/shadow_0_7.json")
    if shadow_file.exists():
        try:
            with open(shadow_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            shadow_0_7 = data["shadow_evaluation"]["shadow_pass_rate"]
            return {
                "0.7": shadow_0_7,
                "0.85": 0.0,  # データなし
                "weighted": False,
                "multi": False,
                "grid_enabled": False
            }
        except Exception as e:
            st.error(f"Shadow evaluation読み込みエラー: {e}")
    
    return {
        "0.7": 0.0,
        "0.85": 0.0,
        "weighted": False,
        "multi": False,
        "grid_enabled": False
    }

def load_canary_window_status():
    """Canary 7-Day Window評価結果を読み込み"""
    canary_file = Path("out/canary_window.json")
    if canary_file.exists():
        try:
            with open(canary_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            decision = data.get("decision", "unknown")
            avg_pass_rate = data.get("metrics", {}).get("avg_pass_rate", 0)
            
            if decision == "promote":
                status = "✅ 本採用"
                decision_text = "自動昇格"
            elif decision == "continue_canary":
                status = f"🐤 継続 ({avg_pass_rate:.1f}%)"
                decision_text = "改善要求"
            else:
                status = "❓ データ不足"
                decision_text = "手動確認"
            
            return status, decision_text
            
        except Exception as e:
            st.error(f"Canary window読み込みエラー: {e}")
            return "❌ エラー", "読み込み失敗"
    else:
        return "⏳ 評価待ち", "未実行"

def calculate_model_efficiency(df):
    """モデル別効率性の計算（合格1件あたりの試行回数）"""
    # 現在のデータ構造では試行回数の情報がないため、
    # 合格率から推定効率を計算
    model_stats = []
    
    for date in df['date'].unique():
        day_data = df[df['date'] == date]
        if day_data.empty:
            continue
            
        total_cases = len(day_data)
        passed_cases = len(day_data[day_data['passed'] == True])
        pass_rate = passed_cases / total_cases if total_cases > 0 else 0
        
        # 効率性の推定（合格1件あたりの想定試行回数）
        efficiency = 1 / pass_rate if pass_rate > 0 else float('inf')
        
        model_stats.append({
            'date': date,
            'model': 'Groq (llama-3.3-70b)',  # 現在固定
            'total_cases': total_cases,
            'passed_cases': passed_cases,
            'pass_rate': pass_rate,
            'trials_per_success': efficiency
        })
    
    return pd.DataFrame(model_stats)

# メイン画面
st.title("🎯 Golden Test KPI Dashboard")
st.markdown("AIモデル出力品質の継続監視ダッシュボード")

# データ読み込み
with st.spinner("データ読み込み中..."):
    df = load_golden_logs()
    weekly_df = load_observation_log()

if df.empty and weekly_df.empty:
    st.warning("表示するデータがありません。Golden Testを実行してください。")
    st.stop()

# サイドバー
st.sidebar.header("📊 フィルター")
if not df.empty:
    date_range = st.sidebar.date_input(
        "期間選択",
        value=(df['date'].min(), df['date'].max()),
        min_value=df['date'].min(),
        max_value=df['date'].max()
    )
    
    # 期間でフィルタリング
    if len(date_range) == 2:
        start_date, end_date = date_range
        df_filtered = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    else:
        df_filtered = df
else:
    df_filtered = df

# メトリクス表示
col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    
    # Canary 7-Day Window評価（メトリクス表示前に取得）
    canary_status, canary_decision = load_canary_window_status()

    if not df_filtered.empty:
        total_cases = len(df_filtered)
        passed_cases = len(df_filtered[df_filtered['passed'] == True])
        pass_rate = passed_cases / total_cases * 100 if total_cases > 0 else 0
        avg_score = df_filtered['score'].mean()
        flaky_rate = calculate_flaky_rate(df_filtered)
        
        # New Fail Ratio計算（週次データから）
        if not weekly_df.empty and 'new_fail_ratio' in weekly_df.columns:
            latest_new_fail_ratio = weekly_df.iloc[-1]['new_fail_ratio'] * 100
        else:
            latest_new_fail_ratio = 0.0
        
        # Shadow Evaluation結果読み込み（複数しきい値対応）
        shadow_data = load_shadow_evaluation()
        
        col1.metric("総テスト数", total_cases)
        col2.metric("合格数", passed_cases)
        col3.metric("合格率", f"{pass_rate:.1f}%")
        col4.metric("平均スコア", f"{avg_score:.3f}")
        col5.metric("Flaky率", f"{flaky_rate:.1f}%")
        col6.metric("新規失敗率", f"{latest_new_fail_ratio:.1f}%")
        col7.metric("Predicted@0.7", f"{shadow_data['0.7']:.1f}%")
        
        # Phase4 Gap計算
        phase4_gap = max(0, 85.0 - shadow_data['0.85']) if shadow_data['0.85'] > 0 else 85.0
        gap_status = "✅ 準備完了" if phase4_gap <= 0 else f"🔄 Gap: {phase4_gap:.1f}pp"
        
        col8.metric("Predicted@0.85", f"{shadow_data['0.85']:.1f}%", 
                   delta=gap_status)
    
    # Canary 7-Day Window表示（メトリクス行の下）
    st.subheader("🐤 Canary 7-Day Window Status")
    col_canary1, col_canary2 = st.columns(2)
    col_canary1.metric("Status", canary_status)
    col_canary2.metric("Decision", canary_decision)
    
    # 重み付き評価の表示
    if shadow_data.get('weighted', False):
        st.info("🎯 **重み付き評価**: 頻出失敗・重要ケースを1.5x重みで評価中")

# 1. 週次合格率（ラインチャート）
st.header("📈 週次合格率トレンド")

if not weekly_df.empty:
    fig_weekly = px.line(
        weekly_df, 
        x='date', 
        y='pass_rate',
        title='週次合格率の推移',
        labels={'pass_rate': '合格率 (%)', 'date': '日付'},
        markers=True
    )
    
    # しきい値ラインを追加
    fig_weekly.add_hline(y=90, line_dash="dash", line_color="green", 
                        annotation_text="目標: 90%")
    fig_weekly.add_hline(y=80, line_dash="dash", line_color="orange", 
                        annotation_text="警告: 80%")
    
    fig_weekly.update_layout(height=400)
    st.plotly_chart(fig_weekly, use_container_width=True)
    
    # 新規失敗率トレンド
    if 'new_fail_ratio' in weekly_df.columns:
        st.subheader("📊 新規失敗率トレンド")
        fig_new_fail = px.line(
            weekly_df,
            x='date',
            y='new_fail_ratio',
            title='週次新規失敗率の推移',
            labels={'new_fail_ratio': '新規失敗率', 'date': '日付'},
            markers=True
        )
        fig_new_fail.update_traces(line_color='red')
        fig_new_fail.update_layout(
            height=300,
            yaxis=dict(tickformat=".1%")
        )
        st.plotly_chart(fig_new_fail, use_container_width=True)

    # 段階昇格グリッド可視化
st.subheader("🚀 段階昇格グリッド")

shadow_data = load_shadow_evaluation()

# 段階昇格情報表示
if shadow_data.get('grid_enabled') and 'staged_promotion' in shadow_data:
    staged_promotion = shadow_data['staged_promotion']
    
    # Next Recommended Threshold表示
    st.subheader("🎯 Next Recommended Threshold")
    next_col1, next_col2, next_col3 = st.columns(3)
    
    with next_col1:
        current_threshold = staged_promotion.get('current_threshold', 0.5)
        st.metric("Current Threshold", f"{current_threshold:.2f}")
    
    with next_col2:
        next_recommended = staged_promotion.get('next_recommended', 0.5)
        promotion_step = staged_promotion.get('promotion_step', 0)
        st.metric("Next Recommended", f"{next_recommended:.2f}", 
                 delta=f"+{promotion_step:.2f}" if promotion_step > 0 else "待機中")
    
    with next_col3:
        promotion_ready = staged_promotion.get('promotion_ready', False)
        status_text = "✅ 昇格可能" if promotion_ready else "🟡 条件待ち"
        st.metric("昇格ステータス", status_text)
    
    # グリッド可視化
    if 'grid' in shadow_data and shadow_data['grid']:
        st.subheader("📊 しきい値グリッド分析")
        
        grid_data = shadow_data['grid']
        
        # データフレーム作成
        thresholds = sorted([float(t) for t in grid_data.keys()])
        pass_rates = [grid_data[str(t)] for t in thresholds]
        
        # ステータス判定
        statuses = []
        for rate in pass_rates:
            if rate >= 80:
                statuses.append('✅ 昇格可能')
            elif rate >= 70:
                statuses.append('🔄 改善中')
            else:
                statuses.append('❌ 要改善')
        
        grid_df = pd.DataFrame({
            'Threshold': [f"{t:.2f}" for t in thresholds],
            'Pass Rate': pass_rates,
            'Status': statuses
        })
        
        # 棒グラフで可視化
        fig_grid = px.bar(
            grid_df,
            x='Threshold',
            y='Pass Rate',
            title='段階昇格グリッド: しきい値別予測合格率',
            labels={'Pass Rate': '予測合格率 (%)', 'Threshold': 'しきい値'},
            color='Pass Rate',
            color_continuous_scale='RdYlGn',
            text='Status'
        )
        
        # 基準線追加
        fig_grid.add_hline(y=85, line_dash="dash", line_color="red", 
                          annotation_text="Phase 4基準: 85%")
        fig_grid.add_hline(y=80, line_dash="dash", line_color="green", 
                          annotation_text="昇格基準: 80%")
        fig_grid.add_hline(y=70, line_dash="dash", line_color="orange", 
                          annotation_text="Phase 3基準: 70%")
        
        # Next Recommendedをハイライト
        if promotion_ready:
            next_idx = thresholds.index(next_recommended) if next_recommended in thresholds else -1
            if next_idx >= 0:
                fig_grid.add_shape(
                    type="rect",
                    x0=next_idx - 0.4,
                    x1=next_idx + 0.4,
                    y0=0,
                    y1=pass_rates[next_idx] + 5,
                    line=dict(color="gold", width=3),
                    fillcolor="gold",
                    opacity=0.2
                )
        
        fig_grid.update_traces(textposition='outside')
        fig_grid.update_layout(height=500, showlegend=False)
        
        st.plotly_chart(fig_grid, use_container_width=True)
        
        # グリッドテーブル表示
        st.subheader("📋 グリッド詳細")
        st.dataframe(grid_df, use_container_width=True)

# 従来のShadow Evaluation比較（グリッドがない場合）
elif shadow_data['multi'] and shadow_data['0.85'] > 0:
    st.subheader("🔮 Shadow Evaluation 比較")
    # 0.7と0.85の比較チャート
    shadow_comparison_data = {
        'Threshold': ['0.7 (Current)', '0.85 (Phase 4)'],
        'Pass Rate': [shadow_data['0.7'], shadow_data['0.85']],
        'Status': ['✅ 運用中' if shadow_data['0.7'] >= 70 else '⚠️ 要改善', 
                  '✅ 準備完了' if shadow_data['0.85'] >= 85 else '🔄 準備中']
    }
    
    fig_shadow = px.bar(
        shadow_comparison_data,
        x='Threshold',
        y='Pass Rate',
        title='Shadow Evaluation: しきい値別予測合格率',
        labels={'Pass Rate': '予測合格率 (%)', 'Threshold': 'しきい値'},
        color='Pass Rate',
        color_continuous_scale='RdYlGn',
        text='Status'
    )
    
    # 基準線追加
    fig_shadow.add_hline(y=85, line_dash="dash", line_color="red", 
                        annotation_text="Phase 4基準: 85%")
    fig_shadow.add_hline(y=70, line_dash="dash", line_color="orange", 
                        annotation_text="Phase 3基準: 70%")
    
    fig_shadow.update_traces(textposition='outside')
    fig_shadow.update_layout(height=400, showlegend=False)
    
    st.plotly_chart(fig_shadow, use_container_width=True)
    
    # Phase 4昇格条件表示（強化版）
    phase4_gap = max(0, 85.0 - shadow_data['0.85']) if shadow_data['0.85'] > 0 else 85.0
    latest_new_fail_ratio = latest_new_fail_ratio if not weekly_df.empty else 0.0
    new_fail_ok = latest_new_fail_ratio <= 70.0
    
    st.info(f"""
    **Phase 4 昇格条件**:
    - Predicted@0.85 ≥ 85% (現在: {shadow_data['0.85']:.1f}%, Gap: {phase4_gap:.1f}pp)
    - 2週連続で条件達成
    - new_fail_ratio ≤ 70% (現在: {latest_new_fail_ratio:.1f}% {'✅' if new_fail_ok else '❌'})
    
    **現在の状況**: {'✅ 条件達成' if shadow_data['0.85'] >= 85 and new_fail_ok else '🔄 改善継続中'}
    
    **残り改善項目**:
    {f'- Predicted@0.85を{phase4_gap:.1f}pp向上' if phase4_gap > 0 else ''}
    {f'- 新規失敗率を{latest_new_fail_ratio - 70:.1f}pp削減' if not new_fail_ok else ''}
    """)
    
    # Phase4 Gapカード表示
    st.subheader("📊 Phase 4 Gap Analysis")
    gap_col1, gap_col2, gap_col3 = st.columns(3)
    
    with gap_col1:
        st.metric("Phase 4 Gap", f"{phase4_gap:.1f}pp", 
                 delta=f"目標まで{phase4_gap:.1f}pp" if phase4_gap > 0 else "目標達成")
    
    with gap_col2:
        # Flaky率とNew失敗率のサブ指標
        st.metric("Flaky率", f"{flaky_rate:.1f}%", 
                 delta="要改善" if flaky_rate > 15 else "良好")
    
    with gap_col3:
        st.metric("新規失敗率", f"{latest_new_fail_ratio:.1f}%",
                 delta="良好" if new_fail_ok else "要改善")
else:
    st.info("📊 Phase 4 Shadow Evaluation データを取得中...")
    st.code("python tests/golden/runner.py --threshold-shadow '0.7,0.85' --report out/shadow_multi.json")
else:
    st.info("週次データがありません。観測ログを確認してください。")

# 2. 失敗理由の上位（棒グラフ）
st.header("🔍 失敗理由分析")

if not df_filtered.empty:
    failure_df = analyze_failure_reasons(df_filtered)
    
    if not failure_df.empty:
        # Root Cause Top3の表示
        st.subheader("📊 Root Cause Top3")
        root_cause_counts = failure_df['root_cause'].value_counts().head(3)
        
        if not root_cause_counts.empty:
            col1, col2, col3 = st.columns(3)
            
            for i, (cause, count) in enumerate(root_cause_counts.items()):
                percentage = (count / len(failure_df)) * 100
                with [col1, col2, col3][i]:
                    st.metric(
                        f"#{i+1} {cause}",
                        f"{count}件",
                        f"{percentage:.1f}%"
                    )
        
        # 不足キーワードの頻度分析
        st.subheader("🔤 不足キーワード上位10")
        missing_words_flat = []
        for words_str in failure_df['missing_words']:
            if words_str != 'なし':
                missing_words_flat.extend(words_str.split(', '))
        
        if missing_words_flat:
            missing_freq = pd.Series(missing_words_flat).value_counts().head(10)
            
            fig_failures = px.bar(
                x=missing_freq.values,
                y=missing_freq.index,
                orientation='h',
                title='不足キーワード頻度',
                labels={'x': '出現回数', 'y': 'キーワード'}
            )
            fig_failures.update_layout(height=400)
            st.plotly_chart(fig_failures, use_container_width=True)
        else:
            st.success("分析期間中に失敗ケースはありません！")
    else:
        st.success("分析期間中に失敗ケースはありません！")
else:
    st.info("分析するデータがありません。")

# 3. モデル別効率性（表形式）
st.header("⚡ モデル効率性")

if not df_filtered.empty:
    efficiency_df = calculate_model_efficiency(df_filtered)
    
    if not efficiency_df.empty:
        # 効率性テーブル
        st.subheader("合格1件あたりの推定試行回数")
        
        display_df = efficiency_df[['date', 'model', 'total_cases', 'passed_cases', 'pass_rate', 'trials_per_success']].copy()
        display_df['pass_rate'] = display_df['pass_rate'].apply(lambda x: f"{x*100:.1f}%")
        display_df['trials_per_success'] = display_df['trials_per_success'].apply(
            lambda x: f"{x:.2f}" if x != float('inf') else "∞"
        )
        
        display_df.columns = ['日付', 'モデル', '総ケース数', '合格数', '合格率', '試行回数/合格']
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("効率性データがありません。")

# 詳細データ表示
with st.expander("📋 詳細データ"):
    if not df_filtered.empty:
        st.subheader("テストケース詳細")
        detail_df = df_filtered[['id', 'date', 'score', 'passed', 'reference', 'prediction']].copy()
        detail_df = detail_df.sort_values('date', ascending=False)
        st.dataframe(detail_df, use_container_width=True)
    
    if not weekly_df.empty:
        st.subheader("週次観測データ")
        st.dataframe(weekly_df, use_container_width=True)

# フッター
st.markdown("---")
st.markdown("🎯 **Golden Test Dashboard** - AIモデル品質の継続的監視")
st.markdown(f"最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
