'use client';

import React from 'react';

interface FileAnalysisProps {
  result: {
    filename: string;
    size: string;
    type: string;
    result: {
      file_info?: {
        document_type?: string;
        text_length?: number;
      };
      processing_mode?: string;
      summary?: string | { summary?: string };
      document_analysis?: {
        lines?: number;
        word_count?: number;
        character_count?: number;
        document_type?: string;
        encoding?: string;
      };
      ai_analysis?: {
        key_insights?: string[];
        training_data?: {
          structured_knowledge?: Record<string, unknown>;
          qa_pairs?: Array<{
            question: string;
            answer: string;
          }>;
        };
        quality_metrics?: {
          coverage?: number;
          average_importance?: number;
          key_insight_density?: number;
        };
      };
    };
  };
}

export const FileAnalysisResult: React.FC<FileAnalysisProps> = ({ result }) => {
  const { filename, size, type, result: analysisResult } = result;

  const getFileIcon = (fileType: string) => {
    if (fileType.includes('pdf')) return '📄';
    if (fileType.includes('word') || fileType.includes('document')) return '📝';
    if (fileType.includes('excel') || fileType.includes('spreadsheet')) return '📊';
    if (fileType.includes('powerpoint') || fileType.includes('presentation')) return '📋';
    if (fileType.includes('json')) return '🔧';
    if (fileType.includes('csv')) return '📈';
    if (fileType.includes('audio')) return '🎵';
    if (fileType.includes('video')) return '🎬';
    if (fileType.includes('text')) return '📄';
    return '📁';
  };

  const formatNumber = (num?: number) => {
    return num?.toLocaleString() || 'N/A';
  };

  return (
    <div className="border rounded-lg p-4 bg-gray-50 space-y-4">
      {/* ファイル基本情報 */}
      <div className="flex justify-between items-start">
        <div className="flex items-center space-x-2">
          <span className="text-2xl">{getFileIcon(type)}</span>
          <div>
            <p className="font-medium text-gray-800">{filename}</p>
            <p className="text-sm text-gray-600">{size} • {type}</p>
          </div>
        </div>
        <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
          ✅ 分析完了
        </span>
      </div>

      {/* 文書分析情報 */}
      {analysisResult.document_analysis && (
        <div className="bg-blue-50 p-3 rounded">
          <h4 className="font-medium text-blue-800 mb-2">📋 文書分析結果</h4>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-blue-700 font-medium">文書タイプ:</span>
              <span className="ml-1 text-blue-600">
                {analysisResult.document_analysis.document_type || 'unknown'}
              </span>
            </div>
            <div>
              <span className="text-blue-700 font-medium">文字エンコーディング:</span>
              <span className="ml-1 text-blue-600">
                {analysisResult.document_analysis.encoding || 'unknown'}
              </span>
            </div>
            <div>
              <span className="text-blue-700 font-medium">行数:</span>
              <span className="ml-1 text-blue-600">
                {formatNumber(analysisResult.document_analysis.lines)}
              </span>
            </div>
            <div>
              <span className="text-blue-700 font-medium">単語数:</span>
              <span className="ml-1 text-blue-600">
                {formatNumber(analysisResult.document_analysis.word_count)}
              </span>
            </div>
            <div className="col-span-2">
              <span className="text-blue-700 font-medium">文字数:</span>
              <span className="ml-1 text-blue-600">
                {formatNumber(analysisResult.document_analysis.character_count)}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* AI分析情報 */}
      {analysisResult.ai_analysis && (
        <div className="bg-purple-50 p-3 rounded">
          <h4 className="font-medium text-purple-800 mb-2">🤖 AI分析結果</h4>
          
          {/* 品質メトリクス */}
          {analysisResult.ai_analysis.quality_metrics && (
            <div className="mb-3">
              <div className="text-sm text-purple-700 space-y-1">
                                 <div className="flex justify-between">
                   <span>カバレッジ:</span>
                   <span className="font-mono">
                     {((analysisResult.ai_analysis.quality_metrics.coverage || 0) * 100).toFixed(1)}%
                   </span>
                 </div>
                 <div className="flex justify-between">
                   <span>重要度:</span>
                   <span className="font-mono">
                     {((analysisResult.ai_analysis.quality_metrics.average_importance || 0) * 100).toFixed(1)}%
                   </span>
                 </div>
                <div className="flex justify-between">
                  <span>洞察密度:</span>
                  <span className="font-mono">
                    {analysisResult.ai_analysis.quality_metrics.key_insight_density?.toFixed(1)}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* キーインサイト */}
          {analysisResult.ai_analysis.key_insights && analysisResult.ai_analysis.key_insights.length > 0 && (
            <div className="mb-3">
              <p className="text-sm font-medium text-purple-700 mb-1">🔍 キーインサイト:</p>
              <ul className="text-sm text-purple-600 space-y-1">
                {analysisResult.ai_analysis.key_insights.map((insight, index) => (
                  <li key={index} className="flex items-start">
                    <span className="text-purple-400 mr-1">•</span>
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Q&Aペア */}
          {analysisResult.ai_analysis.training_data?.qa_pairs && 
           analysisResult.ai_analysis.training_data.qa_pairs.length > 0 && (
            <div>
              <p className="text-sm font-medium text-purple-700 mb-2">❓ 生成されたQ&A:</p>
              <div className="space-y-2">
                {analysisResult.ai_analysis.training_data.qa_pairs.slice(0, 3).map((qa, index) => (
                  <div key={index} className="text-xs text-purple-600 bg-purple-100 p-2 rounded">
                    <p className="font-medium">Q: {qa.question}</p>
                    <p className="mt-1">A: {qa.answer}</p>
                  </div>
                ))}
                {analysisResult.ai_analysis.training_data.qa_pairs.length > 3 && (
                  <p className="text-xs text-purple-500">
                    +{analysisResult.ai_analysis.training_data.qa_pairs.length - 3}件のQ&Aペアが生成されました
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 処理モード */}
      <div className="flex justify-between text-xs text-gray-500">
        <span>処理モード: {analysisResult.processing_mode || 'standard'}</span>
        <span>ファイルサイズ: {size}</span>
      </div>
    </div>
  );
}; 