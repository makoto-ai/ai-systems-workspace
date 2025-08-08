#!/usr/bin/env python3
"""
Real-time Analytics and Prediction System
リアルタイム分析・予測システム
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from typing import Dict, Any, List, Optional
import json
import logging
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os

class RealTimeAnalytics:
    """リアルタイム分析システム"""
    
    def __init__(self):
        self.setup_logging()
        self.data_stream = []
        self.predictions = []
        self.models = {}
        self.scalers = {}
        
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('real_time_analytics.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def add_data_point(self, data: Dict[str, Any]):
        """データポイント追加"""
        data['timestamp'] = datetime.now()
        self.data_stream.append(data)
        
        # データストリームを1000件に制限
        if len(self.data_stream) > 1000:
            self.data_stream.pop(0)
        
        self.logger.info(f"データポイント追加: {data}")
    
    def get_recent_data(self, hours: int = 24) -> List[Dict[str, Any]]:
        """最近のデータ取得"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [d for d in self.data_stream if d['timestamp'] >= cutoff_time]
    
    def calculate_metrics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """メトリクス計算"""
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        
        metrics = {
            'total_operations': len(data),
            'avg_quality_score': df.get('quality_score', pd.Series([0])).mean(),
            'avg_generation_time': df.get('generation_time', pd.Series([0])).mean(),
            'success_rate': (df.get('success', pd.Series([True])).sum() / len(data)) * 100,
            'popular_styles': df.get('style', pd.Series(['unknown'])).value_counts().to_dict(),
            'avg_content_length': df.get('content_length', pd.Series([0])).mean()
        }
        
        return metrics
    
    def generate_predictions(self, target_metric: str = 'quality_score', hours_ahead: int = 6) -> Dict[str, Any]:
        """予測生成"""
        if len(self.data_stream) < 10:
            return {"error": "データが不足しています"}
        
        # データ準備
        df = pd.DataFrame(self.data_stream)
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # 特徴量作成
        features = ['hour', 'day_of_week']
        if 'quality_score' in df.columns:
            features.append('quality_score')
        if 'generation_time' in df.columns:
            features.append('generation_time')
        
        X = df[features].fillna(0)
        y = df.get(target_metric, pd.Series([0]))
        
        # モデル訓練
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # 将来の時間ポイントで予測
        future_hours = []
        current_time = datetime.now()
        for i in range(hours_ahead):
            future_time = current_time + timedelta(hours=i+1)
            future_hours.append({
                'hour': future_time.hour,
                'day_of_week': future_time.weekday()
            })
        
        future_df = pd.DataFrame(future_hours)
        predictions = model.predict(future_df[features])
        
        return {
            'predictions': predictions.tolist(),
            'future_hours': [h['hour'] for h in future_hours],
            'model_accuracy': model.score(X, y),
            'feature_importance': dict(zip(features, model.feature_importances_))
        }
    
    def create_realtime_dashboard(self) -> Dict[str, Any]:
        """リアルタイムダッシュボード作成"""
        recent_data = self.get_recent_data(24)
        metrics = self.calculate_metrics(recent_data)
        predictions = self.generate_predictions()
        
        return {
            'metrics': metrics,
            'predictions': predictions,
            'data_points': len(recent_data),
            'last_update': datetime.now().isoformat()
        }
    
    def create_visualizations(self) -> Dict[str, go.Figure]:
        """可視化作成"""
        if not self.data_stream:
            return {}
        
        df = pd.DataFrame(self.data_stream)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        figures = {}
        
        # 時系列品質スコア
        if 'quality_score' in df.columns:
            fig_quality = go.Figure()
            fig_quality.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['quality_score'],
                mode='lines+markers',
                name='品質スコア',
                line=dict(color='blue')
            ))
            fig_quality.update_layout(
                title='リアルタイム品質スコア推移',
                xaxis_title='時間',
                yaxis_title='品質スコア',
                height=400
            )
            figures['quality_trend'] = fig_quality
        
        # 生成時間分布
        if 'generation_time' in df.columns:
            fig_time = go.Figure()
            fig_time.add_trace(go.Histogram(
                x=df['generation_time'],
                nbinsx=20,
                name='生成時間分布'
            ))
            fig_time.update_layout(
                title='生成時間分布',
                xaxis_title='生成時間（秒）',
                yaxis_title='頻度',
                height=400
            )
            figures['generation_time_dist'] = fig_time
        
        # スタイル別使用頻度
        if 'style' in df.columns:
            style_counts = df['style'].value_counts()
            fig_style = go.Figure(data=[go.Pie(
                labels=style_counts.index,
                values=style_counts.values,
                hole=0.3
            )])
            fig_style.update_layout(
                title='スタイル別使用頻度',
                height=400
            )
            figures['style_usage'] = fig_style
        
        return figures
    
    def detect_anomalies(self, threshold: float = 2.0) -> List[Dict[str, Any]]:
        """異常検知"""
        if len(self.data_stream) < 10:
            return []
        
        df = pd.DataFrame(self.data_stream)
        anomalies = []
        
        if 'quality_score' in df.columns:
            mean_score = df['quality_score'].mean()
            std_score = df['quality_score'].std()
            
            for idx, row in df.iterrows():
                z_score = abs((row['quality_score'] - mean_score) / std_score)
                if z_score > threshold:
                    anomalies.append({
                        'timestamp': row['timestamp'],
                        'metric': 'quality_score',
                        'value': row['quality_score'],
                        'z_score': z_score,
                        'severity': 'high' if z_score > 3 else 'medium'
                    })
        
        return anomalies
    
    def get_performance_insights(self) -> Dict[str, Any]:
        """性能インサイト取得"""
        if not self.data_stream:
            return {}
        
        df = pd.DataFrame(self.data_stream)
        
        insights = {
            'total_operations': len(df),
            'avg_quality': df.get('quality_score', pd.Series([0])).mean(),
            'best_performing_style': df.get('style', pd.Series(['unknown'])).mode().iloc[0] if len(df) > 0 else 'unknown',
            'peak_usage_hour': df['timestamp'].dt.hour.mode().iloc[0] if len(df) > 0 else 0,
            'recent_trend': 'improving' if len(df) >= 2 and df['quality_score'].iloc[-1] > df['quality_score'].iloc[-2] else 'declining',
            'anomaly_count': len(self.detect_anomalies())
        }
        
        return insights

class PredictiveAnalytics:
    """予測分析システム"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.prediction_history = []
        
    def train_prediction_model(self, data: List[Dict[str, Any]], target: str):
        """予測モデル訓練"""
        if len(data) < 20:
            return False
        
        df = pd.DataFrame(data)
        
        # 特徴量エンジニアリング
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['month'] = df['timestamp'].dt.month
        
        features = ['hour', 'day_of_week', 'month']
        if 'quality_score' in df.columns:
            features.append('quality_score')
        if 'generation_time' in df.columns:
            features.append('generation_time')
        
        X = df[features].fillna(0)
        y = df[target].fillna(0)
        
        # スケーリング
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # モデル訓練
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_scaled, y)
        
        # モデル保存
        self.models[target] = model
        self.scalers[target] = scaler
        
        return True
    
    def predict_future_values(self, target: str, hours_ahead: int = 24) -> List[float]:
        """将来値予測"""
        if target not in self.models:
            return []
        
        model = self.models[target]
        scaler = self.scalers[target]
        
        # 将来の時間ポイント
        future_times = []
        current_time = datetime.now()
        
        for i in range(hours_ahead):
            future_time = current_time + timedelta(hours=i+1)
            future_times.append({
                'hour': future_time.hour,
                'day_of_week': future_time.weekday(),
                'month': future_time.month
            })
        
        future_df = pd.DataFrame(future_times)
        X_future = scaler.transform(future_df)
        predictions = model.predict(X_future)
        
        return predictions.tolist()

def display_real_time_analytics():
    """リアルタイム分析インターフェース表示"""
    st.header("📊 リアルタイム分析・予測システム")
    
    analytics = RealTimeAnalytics()
    predictive = PredictiveAnalytics()
    
    # サイドバー設定
    st.sidebar.subheader("⚙️ 分析設定")
    analysis_hours = st.sidebar.slider("分析期間（時間）", 1, 168, 24)
    prediction_hours = st.sidebar.slider("予測期間（時間）", 1, 72, 6)
    
    # メインコンテンツ
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 リアルタイムメトリクス")
        
        # サンプルデータ生成
        if st.button("🔄 データ更新"):
            # サンプルデータを追加
            sample_data = {
                'quality_score': np.random.normal(0.8, 0.1),
                'generation_time': np.random.exponential(2.0),
                'style': np.random.choice(['popular', 'academic', 'business']),
                'content_length': np.random.randint(500, 2000),
                'success': True
            }
            analytics.add_data_point(sample_data)
            st.success("データ更新完了！")
        
        # ダッシュボード表示
        dashboard = analytics.create_realtime_dashboard()
        
        if dashboard:
            metrics = dashboard['metrics']
            
            st.metric("総操作数", metrics.get('total_operations', 0))
            st.metric("平均品質スコア", f"{metrics.get('avg_quality_score', 0):.3f}")
            st.metric("平均生成時間", f"{metrics.get('avg_generation_time', 0):.2f}秒")
            st.metric("成功率", f"{metrics.get('success_rate', 0):.1f}%")
    
    with col2:
        st.subheader("🔮 予測分析")
        
        if st.button("🎯 予測実行"):
            predictions = analytics.generate_predictions(hours_ahead=prediction_hours)
            
            if 'predictions' in predictions:
                st.write("**品質スコア予測:**")
                for i, pred in enumerate(predictions['predictions']):
                    st.write(f"時間 {i+1}: {pred:.3f}")
                
                if 'model_accuracy' in predictions:
                    st.metric("モデル精度", f"{predictions['model_accuracy']:.3f}")
    
    # 可視化
    st.subheader("📊 可視化")
    
    figures = analytics.create_visualizations()
    
    if figures:
        for name, fig in figures.items():
            st.plotly_chart(fig, use_container_width=True)
    
    # 異常検知
    st.subheader("🚨 異常検知")
    
    anomalies = analytics.detect_anomalies()
    
    if anomalies:
        st.warning(f"異常検知: {len(anomalies)}件")
        for anomaly in anomalies[:5]:  # 最新5件を表示
            st.write(f"- {anomaly['timestamp']}: {anomaly['metric']} = {anomaly['value']:.3f} (Z-score: {anomaly['z_score']:.2f})")
    else:
        st.success("異常は検知されていません")
    
    # 性能インサイト
    st.subheader("💡 性能インサイト")
    
    insights = analytics.get_performance_insights()
    
    if insights:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("総操作数", insights['total_operations'])
            st.metric("平均品質", f"{insights['avg_quality']:.3f}")
        
        with col2:
            st.metric("最適スタイル", insights['best_performing_style'])
            st.metric("ピーク時間", f"{insights['peak_usage_hour']}時")
        
        with col3:
            st.metric("トレンド", insights['recent_trend'])
            st.metric("異常数", insights['anomaly_count'])

if __name__ == "__main__":
    display_real_time_analytics() 