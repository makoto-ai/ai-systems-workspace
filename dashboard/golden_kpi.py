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
            weekly_data.append({
                'date': datetime.strptime(date_str, "%Y-%m-%d").date(),
                'passed': int(passed),
                'total': int(total),
                'percentage': int(percentage)
            })
    
    except Exception as e:
        st.error(f"観測ログ読み込みエラー: {e}")
    
    return pd.DataFrame(weekly_data)

def analyze_failure_reasons(df):
    """失敗理由の分析"""
    failed_cases = df[df['passed'] == False]
    if failed_cases.empty:
        return pd.DataFrame()
    
    failure_analysis = []
    for _, case in failed_cases.iterrows():
        ref_words = set(case['reference'].split())
        pred_words = set(case['prediction'].split()) if case['prediction'] else set()
        
        missing_words = ref_words - pred_words
        extra_words = pred_words - ref_words
        
        failure_analysis.append({
            'case_id': case['id'],
            'score': case['score'],
            'missing_words': ', '.join(missing_words) if missing_words else 'なし',
            'extra_words': ', '.join(extra_words) if extra_words else 'なし',
            'missing_count': len(missing_words),
            'date': case.get('date', 'Unknown')
        })
    
    return pd.DataFrame(failure_analysis)

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
col1, col2, col3, col4 = st.columns(4)

if not df_filtered.empty:
    total_cases = len(df_filtered)
    passed_cases = len(df_filtered[df_filtered['passed'] == True])
    pass_rate = passed_cases / total_cases * 100 if total_cases > 0 else 0
    avg_score = df_filtered['score'].mean()
    
    col1.metric("総テスト数", total_cases)
    col2.metric("合格数", passed_cases)
    col3.metric("合格率", f"{pass_rate:.1f}%")
    col4.metric("平均スコア", f"{avg_score:.3f}")

# 1. 週次合格率（ラインチャート）
st.header("📈 週次合格率トレンド")

if not weekly_df.empty:
    fig_weekly = px.line(
        weekly_df, 
        x='date', 
        y='percentage',
        title='週次合格率の推移',
        labels={'percentage': '合格率 (%)', 'date': '日付'},
        markers=True
    )
    
    # しきい値ラインを追加
    fig_weekly.add_hline(y=90, line_dash="dash", line_color="green", 
                        annotation_text="目標: 90%")
    fig_weekly.add_hline(y=80, line_dash="dash", line_color="orange", 
                        annotation_text="警告: 80%")
    
    fig_weekly.update_layout(height=400)
    st.plotly_chart(fig_weekly, use_container_width=True)
else:
    st.info("週次データがありません。観測ログを確認してください。")

# 2. 失敗理由の上位（棒グラフ）
st.header("🔍 失敗理由分析")

if not df_filtered.empty:
    failure_df = analyze_failure_reasons(df_filtered)
    
    if not failure_df.empty:
        # 不足キーワードの頻度分析
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
                title='不足キーワード上位10',
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
