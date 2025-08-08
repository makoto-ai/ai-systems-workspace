'use client';

import React, { useState, useEffect } from 'react';

interface QualityPrediction {
  predicted_quality: number;
  quality_confidence: number;
  predicted_engagement: number;
  feature_importance: Record<string, number>;
  improvement_suggestions: string[];
  prediction_timestamp: string;
  model_version: string;
}

interface MLQualityDashboardProps {
  className?: string;
}

export const MLQualityDashboard: React.FC<MLQualityDashboardProps> = ({
  className = ''
}) => {
  const [modelStatus, setModelStatus] = useState<any>(null); // eslint-disable-line @typescript-eslint/no-explicit-any
  const [prediction, setPrediction] = useState<QualityPrediction | null>(null);
  const [testInput, setTestInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [analytics, setAnalytics] = useState<any>(null); // eslint-disable-line @typescript-eslint/no-explicit-any

  useEffect(() => {
    loadModelStatus();
    loadAnalytics();
  }, []);

  const loadModelStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ml-quality/model-status');
      const data = await response.json();
      setModelStatus(data.model_status);
    } catch (error) {
      console.error('モデル状態取得エラー:', error);
    }
  };

  const loadAnalytics = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ml-quality/analytics');
      const data = await response.json();
      setAnalytics(data.analytics);
    } catch (error) {
      console.error('分析データ取得エラー:', error);
    }
  };

  const testQualityPrediction = async () => {
    if (!testInput.trim()) return;

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('response_text', testInput);
      formData.append('customer_type', 'analytical');
      formData.append('industry', 'IT');
      formData.append('sales_stage', 'needs_assessment');

      const response = await fetch('http://localhost:8000/api/ml-quality/quick-test', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      setPrediction(result.prediction);
    } catch (error) {
      console.error('品質予測エラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const generateSampleData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ml-quality/generate-sample-data', {
        method: 'POST',
      });
      const result = await response.json();
      alert(`${result.generated_samples}件のサンプルデータを生成しました`);
      loadModelStatus();
    } catch (error) {
      console.error('サンプルデータ生成エラー:', error);
    }
  };

  const retrainModel = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/ml-quality/retrain', {
        method: 'POST',
      });
      const result = await response.json();
      
      if (result.success) {
        alert(`モデル学習完了\n品質R²スコア: ${result.quality_r2_score.toFixed(3)}\nエンゲージメントR²スコア: ${result.engagement_r2_score.toFixed(3)}`);
        loadModelStatus();
      }
    } catch (error) {
      console.error('モデル学習エラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getQualityColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getQualityLabel = (score: number) => {
    if (score >= 0.9) return '優秀';
    if (score >= 0.8) return '良好';
    if (score >= 0.7) return '普通';
    if (score >= 0.6) return '要改善';
    return '不良';
  };

  return (
    <div className={`ml-quality-dashboard ${className}`}>
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">
          🤖 ML品質予測ダッシュボード
        </h2>

        {/* モデル状態 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-700 mb-3">
              📊 モデル状態
            </h3>
            {modelStatus && (
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>品質予測モデル:</span>
                  <span className={modelStatus.quality_model_loaded ? 'text-green-600' : 'text-red-600'}>
                    {modelStatus.quality_model_loaded ? '✅ 学習済み' : '❌ 未学習'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>エンゲージメントモデル:</span>
                  <span className={modelStatus.engagement_model_loaded ? 'text-green-600' : 'text-red-600'}>
                    {modelStatus.engagement_model_loaded ? '✅ 学習済み' : '❌ 未学習'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>学習データ:</span>
                  <span className="text-blue-600">{modelStatus.training_data_count}件</span>
                </div>
              </div>
            )}
          </div>

          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-700 mb-3">
              📈 分析統計
            </h3>
            {analytics ? (
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>総予測回数:</span>
                  <span className="text-blue-600">{analytics.total_predictions || 0}回</span>
                </div>
                <div className="flex justify-between">
                  <span>平均品質:</span>
                  <span className="text-green-600">
                    {((analytics.recent_average_quality || 0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>予測信頼度:</span>
                  <span className="text-purple-600">
                    {((analytics.recent_average_confidence || 0) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-gray-500">分析データなし</p>
            )}
          </div>
        </div>

        {/* 管理操作 */}
        <div className="bg-blue-50 p-4 rounded-lg mb-6">
          <h3 className="text-lg font-semibold text-gray-700 mb-3">
            ⚙️ モデル管理
          </h3>
          <div className="flex space-x-4">
            <button
              onClick={generateSampleData}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              📊 サンプルデータ生成
            </button>
            <button
              onClick={retrainModel}
              disabled={isLoading}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
            >
              {isLoading ? '🔄 学習中...' : '🧠 モデル再学習'}
            </button>
          </div>
        </div>

        {/* 品質テスト */}
        <div className="bg-gray-50 p-4 rounded-lg mb-6">
          <h3 className="text-lg font-semibold text-gray-700 mb-3">
            🧪 品質予測テスト
          </h3>
          <div className="space-y-4">
            <textarea
              value={testInput}
              onChange={(e) => setTestInput(e.target.value)}
              placeholder="営業応答テキストを入力してください..."
              className="w-full p-3 border border-gray-300 rounded-lg h-20"
            />
            <button
              onClick={testQualityPrediction}
              disabled={!testInput.trim() || isLoading}
              className="w-full py-2 px-4 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
            >
              {isLoading ? '🔄 予測中...' : '🚀 品質予測実行'}
            </button>
          </div>
        </div>

        {/* 予測結果 */}
        {prediction && (
          <div className="bg-green-50 p-4 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-700 mb-3">
              📊 予測結果
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="bg-white p-3 rounded border text-center">
                <p className="text-sm text-gray-600">品質スコア</p>
                <p className={`text-2xl font-bold ${getQualityColor(prediction.predicted_quality)}`}>
                  {(prediction.predicted_quality * 100).toFixed(1)}%
                </p>
                <p className="text-sm text-gray-500">
                  {getQualityLabel(prediction.predicted_quality)}
                </p>
              </div>
              
              <div className="bg-white p-3 rounded border text-center">
                <p className="text-sm text-gray-600">エンゲージメント</p>
                <p className={`text-2xl font-bold ${getQualityColor(prediction.predicted_engagement)}`}>
                  {(prediction.predicted_engagement * 100).toFixed(1)}%
                </p>
              </div>
              
              <div className="bg-white p-3 rounded border text-center">
                <p className="text-sm text-gray-600">予測信頼度</p>
                <p className="text-2xl font-bold text-blue-600">
                  {(prediction.quality_confidence * 100).toFixed(1)}%
                </p>
              </div>
            </div>

            {/* 特徴量重要度（上位5位） */}
            {Object.keys(prediction.feature_importance).length > 0 && (
              <div className="bg-white p-3 rounded border mb-4">
                <p className="text-sm font-medium text-gray-700 mb-2">
                  🔍 重要な特徴量（上位5位）
                </p>
                <div className="space-y-1">
                  {Object.entries(prediction.feature_importance)
                    .sort(([,a], [,b]) => (b as number) - (a as number))
                    .slice(0, 5)
                    .map(([feature, importance]) => (
                      <div key={feature} className="flex justify-between text-sm">
                        <span className="text-gray-600">{feature}:</span>
                        <span className="text-blue-600">
                          {((importance as number) * 100).toFixed(1)}%
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* 改善提案 */}
            {prediction.improvement_suggestions.length > 0 && (
              <div className="bg-white p-3 rounded border">
                <p className="text-sm font-medium text-gray-700 mb-2">
                  💡 改善提案
                </p>
                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                  {prediction.improvement_suggestions.map((suggestion, index) => (
                    <li key={index}>{suggestion}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="mt-3 text-xs text-gray-500">
              予測時刻: {new Date(prediction.prediction_timestamp).toLocaleString()}
              | モデルバージョン: {prediction.model_version}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}; 