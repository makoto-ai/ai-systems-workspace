'use client';

import React, { useState, useEffect } from 'react';

interface PromptTemplate {
  name: string;
  description: string;
  category: string;
  system_prompt: string;
  user_prompt_template: string;
  quality_settings: {
    max_tokens?: number;
    temperature?: number;
  };
}

interface PromptManagerProps {
  onPromptSelect?: (templateId: string) => void;
  className?: string;
}

export const PromptManager: React.FC<PromptManagerProps> = ({
  onPromptSelect,
  className = ''
}) => {
  const [templates, setTemplates] = useState<Record<string, PromptTemplate>>({});
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [testInput, setTestInput] = useState('');
  const [testResult, setTestResult] = useState<any>(null); // eslint-disable-line @typescript-eslint/no-explicit-any
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'templates' | 'test' | 'create'>('templates');

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/custom-prompt/templates');
      const data = await response.json();
      setTemplates(data.templates || {});
    } catch (error) {
      console.error('テンプレート読み込みエラー:', error);
    }
  };

  const testPrompt = async () => {
    if (!selectedTemplate || !testInput) return;

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('template_id', selectedTemplate);
      formData.append('test_input', testInput);
      formData.append('customer_type', 'analytical');
      formData.append('industry', 'IT');

      const response = await fetch('http://localhost:8000/api/custom-prompt/test', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      setTestResult(result);
    } catch (error) {
      console.error('プロンプトテストエラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getQualityColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'sales': return '💼';
      case 'customer_service': return '🤝';
      case 'training': return '📚';
      default: return '⚙️';
    }
  };

  return (
    <div className={`prompt-manager ${className}`}>
      <div className="bg-white rounded-lg shadow-lg p-6">
        {/* タブナビゲーション */}
        <div className="flex border-b border-gray-200 mb-6">
          <button
            className={`px-4 py-2 font-medium ${
              activeTab === 'templates'
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('templates')}
          >
            📋 テンプレート
          </button>
          <button
            className={`px-4 py-2 font-medium ml-4 ${
              activeTab === 'test'
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('test')}
          >
            🧪 テスト
          </button>
          <button
            className={`px-4 py-2 font-medium ml-4 ${
              activeTab === 'create'
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('create')}
          >
            ➕ 作成
          </button>
        </div>

        {/* テンプレート一覧 */}
        {activeTab === 'templates' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">
              🎯 営業プロンプトテンプレート
            </h3>
            <div className="grid gap-4">
              {Object.entries(templates).map(([id, template]) => (
                <div
                  key={id}
                  className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                    selectedTemplate === id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => {
                    setSelectedTemplate(id);
                    onPromptSelect?.(id);
                  }}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex items-center space-x-2">
                      <span className="text-2xl">{getCategoryIcon(template.category)}</span>
                      <div>
                        <h4 className="font-medium text-gray-800">{template.name}</h4>
                        <p className="text-sm text-gray-600">{template.description}</p>
                      </div>
                    </div>
                    <span className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded">
                      {template.category}
                    </span>
                  </div>
                  
                  <div className="mt-3 text-xs text-gray-500">
                    <div className="grid grid-cols-2 gap-2">
                      <span>トークン: {template.quality_settings?.max_tokens || 150}</span>
                      <span>温度: {template.quality_settings?.temperature || 0.7}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* プロンプトテスト */}
        {activeTab === 'test' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">
              🧪 プロンプト品質テスト
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  テンプレート選択
                </label>
                <select
                  value={selectedTemplate}
                  onChange={(e) => setSelectedTemplate(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="">テンプレートを選択...</option>
                  {Object.entries(templates).map(([id, template]) => (
                    <option key={id} value={id}>
                      {getCategoryIcon(template.category)} {template.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  テスト入力（顧客の発言）
                </label>
                <textarea
                  value={testInput}
                  onChange={(e) => setTestInput(e.target.value)}
                  placeholder="例: 御社のサービスの料金について教えてください"
                  className="w-full p-3 border border-gray-300 rounded-md h-20"
                />
              </div>

              <button
                onClick={testPrompt}
                disabled={!selectedTemplate || !testInput || isLoading}
                className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {isLoading ? '🔄 テスト中...' : '🚀 プロンプトテスト実行'}
              </button>
            </div>

            {testResult && (
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-gray-800 mb-3">📊 テスト結果</h4>
                
                <div className="space-y-3">
                  <div className="bg-white p-3 rounded border">
                    <p className="text-sm font-medium text-gray-700">生成された応答:</p>
                    <p className="text-gray-800 mt-1">{testResult.generated_response}</p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white p-3 rounded border">
                      <p className="text-sm font-medium text-gray-700">品質スコア</p>
                      <p className={`text-2xl font-bold ${getQualityColor(testResult.quality_score)}`}>
                        {(testResult.quality_score * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div className="bg-white p-3 rounded border">
                      <p className="text-sm font-medium text-gray-700">応答長</p>
                      <p className="text-lg font-semibold text-gray-800">
                        {testResult.response_length}文字
                      </p>
                    </div>
                  </div>

                  <div className="bg-white p-3 rounded border">
                    <p className="text-sm font-medium text-gray-700 mb-2">品質指標</p>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>適切な長さ:</span>
                        <span className={testResult.quality_metrics.length_appropriate ? 'text-green-600' : 'text-red-600'}>
                          {testResult.quality_metrics.length_appropriate ? '✅' : '❌'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>丁寧語使用:</span>
                        <span className={testResult.quality_metrics.politeness_detected ? 'text-green-600' : 'text-red-600'}>
                          {testResult.quality_metrics.politeness_detected ? '✅' : '❌'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>質問含有:</span>
                        <span className={testResult.quality_metrics.question_included ? 'text-green-600' : 'text-red-600'}>
                          {testResult.quality_metrics.question_included ? '✅' : '❌'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>業界関連性:</span>
                        <span className={testResult.quality_metrics.industry_relevant ? 'text-green-600' : 'text-red-600'}>
                          {testResult.quality_metrics.industry_relevant ? '✅' : '❌'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* プロンプト作成 */}
        {activeTab === 'create' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">
              ➕ カスタムプロンプト作成
            </h3>
            <div className="text-center py-8 text-gray-500">
              <p>🚧 カスタムプロンプト作成機能は開発中です</p>
              <p className="text-sm mt-2">近日中に高度なプロンプトエディターを追加予定</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}; 