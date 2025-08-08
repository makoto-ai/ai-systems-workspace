'use client';

import React, { useState, useEffect } from 'react';

interface ABTestResult {
  test_id: string;
  template_a: string;
  template_b: string;
  sample_size_a: number;
  sample_size_b: number;
  avg_quality_a: number;
  avg_quality_b: number;
  p_value_quality: number;
  winner: string | null;
  effect_size: number;
  status: string;
}

interface ComparisonResult {
  template_a: {
    id: string;
    avg_quality: number;
    std_quality: number;
    sample_count: number;
  };
  template_b: {
    id: string;
    avg_quality: number;
    std_quality: number;
    sample_count: number;
  };
  statistical_analysis: {
    t_statistic: number;
    p_value: number;
    cohens_d: number;
    is_significant: boolean;
    improvement_rate: number;
    confidence_level: number;
  };
  winner: string;
}

interface ABTestDashboardProps {
  className?: string;
}

export const ABTestDashboard: React.FC<ABTestDashboardProps> = ({
  className = ''
}) => {
  const [activeTests, setActiveTests] = useState<ABTestResult[]>([]);
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'running' | 'create' | 'compare'>('running');

  // テスト作成フォーム
  const [testName, setTestName] = useState('');
  const [templateA, setTemplateA] = useState('premium_sales_expert');
  const [templateB, setTemplateB] = useState('consultative_advisor');
  const [description, setDescription] = useState('');
  const [targetSampleSize, setTargetSampleSize] = useState(100);

  // クイック比較フォーム
  const [quickTemplateA, setQuickTemplateA] = useState('premium_sales_expert');
  const [quickTemplateB, setQuickTemplateB] = useState('consultative_advisor');
  const [testInput, setTestInput] = useState('');
  const [sampleCount, setSampleCount] = useState(20);

  useEffect(() => {
    loadActiveTests();
  }, []);

  const loadActiveTests = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ab-test/list');
      const data = await response.json();
      setActiveTests(data.active_tests || []);
    } catch (error) {
      console.error('アクティブテスト取得エラー:', error);
    }
  };

  const createABTest = async () => {
    if (!testName.trim()) {
      alert('テスト名を入力してください');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/ab-test/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          test_name: testName,
          template_a_id: templateA,
          template_b_id: templateB,
          description: description,
          target_sample_size: targetSampleSize
        }),
      });

      const result = await response.json();
      
      if (result.success) {
        alert(`A/Bテストが作成されました: ${result.test_id}`);
        setTestName('');
        setDescription('');
        loadActiveTests();
        setActiveTab('running');
      }
    } catch (error) {
      console.error('A/Bテスト作成エラー:', error);
      alert('テスト作成に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const runQuickComparison = async () => {
    if (!testInput.trim()) {
      alert('テスト入力を入力してください');
      return;
    }

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('template_a_id', quickTemplateA);
      formData.append('template_b_id', quickTemplateB);
      formData.append('test_input', testInput);
      formData.append('sample_count', sampleCount.toString());

      const response = await fetch('http://localhost:8000/api/ab-test/quick-comparison', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      
      if (result.success) {
        setComparisonResult(result.comparison_results);
      }
    } catch (error) {
      console.error('クイック比較エラー:', error);
      alert('比較実行に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const stopTest = async (testId: string) => {
    if (!confirm('テストを停止しますか？')) return;

    try {
      const response = await fetch(`http://localhost:8000/api/ab-test/stop/${testId}`, {
        method: 'POST',
      });

      const result = await response.json();
      
      if (result.success) {
        alert('テストが停止されました');
        loadActiveTests();
      }
    } catch (error) {
      console.error('テスト停止エラー:', error);
    }
  };

  const getSignificanceColor = (pValue: number) => {
    if (pValue < 0.01) return 'text-green-600';
    if (pValue < 0.05) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getEffectSizeLabel = (effectSize: number) => {
    const abs = Math.abs(effectSize);
    if (abs > 0.8) return '大';
    if (abs > 0.5) return '中';
    if (abs > 0.2) return '小';
    return '微小';
  };

  return (
    <div className={`ab-test-dashboard ${className}`}>
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">
          ⚖️ A/Bテストダッシュボード
        </h2>

        {/* タブナビゲーション */}
        <div className="flex border-b border-gray-200 mb-6">
          <button
            className={`px-4 py-2 font-medium ${
              activeTab === 'running'
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('running')}
          >
            🏃 実行中テスト
          </button>
          <button
            className={`px-4 py-2 font-medium ml-4 ${
              activeTab === 'create'
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('create')}
          >
            ➕ テスト作成
          </button>
          <button
            className={`px-4 py-2 font-medium ml-4 ${
              activeTab === 'compare'
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('compare')}
          >
            ⚡ クイック比較
          </button>
        </div>

        {/* 実行中テスト */}
        {activeTab === 'running' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">
              📊 実行中のA/Bテスト
            </h3>
            
            {activeTests.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>実行中のテストはありません</p>
                <button
                  onClick={() => setActiveTab('create')}
                  className="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  新しいテストを作成
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {activeTests.map((test) => (
                  <div key={test.test_id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h4 className="font-medium text-gray-800">
                          {test.template_a} vs {test.template_b}
                        </h4>
                        <p className="text-sm text-gray-600">ID: {test.test_id}</p>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs ${
                        test.status === 'running' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {test.status}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                      <div className="text-center">
                        <p className="text-sm text-gray-600">サンプルA</p>
                        <p className="text-lg font-semibold">{test.sample_size_a}</p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm text-gray-600">サンプルB</p>
                        <p className="text-lg font-semibold">{test.sample_size_b}</p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm text-gray-600">p値</p>
                        <p className={`text-lg font-semibold ${getSignificanceColor(test.p_value_quality)}`}>
                          {test.p_value_quality.toFixed(3)}
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm text-gray-600">勝者</p>
                        <p className="text-lg font-semibold text-blue-600">
                          {test.winner || '判定中'}
                        </p>
                      </div>
                    </div>

                    <div className="flex justify-end">
                      <button
                        onClick={() => stopTest(test.test_id)}
                        className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
                      >
                        テスト停止
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* テスト作成 */}
        {activeTab === 'create' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">
              ➕ 新しいA/Bテスト作成
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  テスト名
                </label>
                <input
                  type="text"
                  value={testName}
                  onChange={(e) => setTestName(e.target.value)}
                  placeholder="例: プレミアム vs コンサル型プロンプト比較"
                  className="w-full p-2 border border-gray-300 rounded-md"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    テンプレートA
                  </label>
                  <select
                    value={templateA}
                    onChange={(e) => setTemplateA(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  >
                    <option value="premium_sales_expert">プレミアム営業エキスパート</option>
                    <option value="consultative_advisor">コンサルタティブアドバイザー</option>
                    <option value="empathetic_supporter">共感型サポーター</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    テンプレートB
                  </label>
                  <select
                    value={templateB}
                    onChange={(e) => setTemplateB(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  >
                    <option value="consultative_advisor">コンサルタティブアドバイザー</option>
                    <option value="premium_sales_expert">プレミアム営業エキスパート</option>
                    <option value="empathetic_supporter">共感型サポーター</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  説明（オプション）
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="テストの目的や仮説を記載..."
                  className="w-full p-2 border border-gray-300 rounded-md h-20"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  目標サンプルサイズ
                </label>
                <input
                  type="number"
                  value={targetSampleSize}
                  onChange={(e) => setTargetSampleSize(parseInt(e.target.value))}
                  min="50"
                  max="1000"
                  className="w-full p-2 border border-gray-300 rounded-md"
                />
              </div>

              <button
                onClick={createABTest}
                disabled={isLoading || !testName.trim()}
                className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {isLoading ? '🔄 作成中...' : '🚀 A/Bテスト開始'}
              </button>
            </div>
          </div>
        )}

        {/* クイック比較 */}
        {activeTab === 'compare' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">
              ⚡ クイックプロンプト比較
            </h3>
            
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    比較テンプレートA
                  </label>
                  <select
                    value={quickTemplateA}
                    onChange={(e) => setQuickTemplateA(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  >
                    <option value="premium_sales_expert">プレミアム営業エキスパート</option>
                    <option value="consultative_advisor">コンサルタティブアドバイザー</option>
                    <option value="empathetic_supporter">共感型サポーター</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    比較テンプレートB
                  </label>
                  <select
                    value={quickTemplateB}
                    onChange={(e) => setQuickTemplateB(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  >
                    <option value="consultative_advisor">コンサルタティブアドバイザー</option>
                    <option value="premium_sales_expert">プレミアム営業エキスパート</option>
                    <option value="empathetic_supporter">共感型サポーター</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  テスト入力
                </label>
                <textarea
                  value={testInput}
                  onChange={(e) => setTestInput(e.target.value)}
                  placeholder="例: 御社のサービスについて詳しく教えてください"
                  className="w-full p-2 border border-gray-300 rounded-md h-20"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  サンプル数: {sampleCount}
                </label>
                <input
                  type="range"
                  min="10"
                  max="50"
                  value={sampleCount}
                  onChange={(e) => setSampleCount(parseInt(e.target.value))}
                  className="w-full"
                />
              </div>

              <button
                onClick={runQuickComparison}
                disabled={isLoading || !testInput.trim()}
                className="w-full py-2 px-4 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50"
              >
                {isLoading ? '🔄 比較中...' : '⚡ クイック比較実行'}
              </button>
            </div>

            {/* 比較結果 */}
            {comparisonResult && (
              <div className="mt-6 bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-800 mb-3">📊 比較結果</h4>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div className="bg-white p-3 rounded border">
                    <h5 className="font-medium text-blue-600 mb-2">
                      テンプレートA: {comparisonResult.template_a.id}
                    </h5>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>平均品質:</span>
                        <span className="font-semibold">
                          {(comparisonResult.template_a.avg_quality * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>標準偏差:</span>
                        <span>{(comparisonResult.template_a.std_quality * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>サンプル数:</span>
                        <span>{comparisonResult.template_a.sample_count}</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white p-3 rounded border">
                    <h5 className="font-medium text-green-600 mb-2">
                      テンプレートB: {comparisonResult.template_b.id}
                    </h5>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>平均品質:</span>
                        <span className="font-semibold">
                          {(comparisonResult.template_b.avg_quality * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>標準偏差:</span>
                        <span>{(comparisonResult.template_b.std_quality * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>サンプル数:</span>
                        <span>{comparisonResult.template_b.sample_count}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-3 rounded border">
                  <h5 className="font-medium text-gray-700 mb-2">📈 統計分析</h5>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div className="text-center">
                      <p className="text-gray-600">p値</p>
                      <p className={`font-semibold ${getSignificanceColor(comparisonResult.statistical_analysis.p_value)}`}>
                        {comparisonResult.statistical_analysis.p_value.toFixed(3)}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-gray-600">効果サイズ</p>
                      <p className="font-semibold">
                        {getEffectSizeLabel(comparisonResult.statistical_analysis.cohens_d)} 
                        ({comparisonResult.statistical_analysis.cohens_d.toFixed(2)})
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-gray-600">改善率</p>
                      <p className="font-semibold text-blue-600">
                        {comparisonResult.statistical_analysis.improvement_rate.toFixed(1)}%
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-gray-600">有意性</p>
                      <p className={`font-semibold ${comparisonResult.statistical_analysis.is_significant ? 'text-green-600' : 'text-red-600'}`}>
                        {comparisonResult.statistical_analysis.is_significant ? '✅ 有意' : '❌ 非有意'}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="mt-3 p-3 bg-blue-50 rounded border">
                  <p className="text-sm">
                    <strong>勝者:</strong> {comparisonResult.winner} 
                    {comparisonResult.statistical_analysis.is_significant 
                      ? ' (統計的に有意な差があります)' 
                      : ' (統計的有意差なし)'}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}; 