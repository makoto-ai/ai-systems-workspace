'use client';

import React, { useState, useCallback } from 'react';
import Link from 'next/link';
import useAudioRecorder from '@/hooks/useAudioRecorder';
import useVoiceConversation from '@/hooks/useVoiceConversation';
import { ConversationEntry } from '@/types/conversation';
import { FileUpload } from '@/components/ui/FileUpload';
import { FileAnalysisResult } from '@/components/ui/FileAnalysisResult';

export default function RoleplayPage(): React.JSX.Element {
  const [customerType, setCustomerType] = useState<string>('ANALYTICAL');
  const [autoModeEnabled, setAutoModeEnabled] = useState<boolean>(false); // 自動録音ループを無効化（手動制御）
  const [noiseSuppressionEnabled, setNoiseSuppressionEnabled] = useState<boolean>(true);

  // Voice conversation hook
  const {
    isProcessing,
    currentStep,
    history,
    currentSession,
    error: conversationError,
    performance,
    processVoiceInput,
    startSession,
    endSession,
    clearHistory,
    playAudioResponse,
  } = useVoiceConversation();

  // 自動録音停止後の処理
  const handleAutoStop = useCallback(async (audioBlob: Blob) => {
    console.log('Auto-stop detected, processing voice input...');
    if (autoModeEnabled && audioBlob) {
      await processVoiceInput(audioBlob);
    }
  }, [processVoiceInput, autoModeEnabled]);

  // Audio recording hook with auto-stop callback
  const {
    isRecording,
    isPaused,
    recordingTime,
    audioBlob,
    error: recordingError,
    isListening,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    resetRecording,
    setAutoStopEnabled,
  } = useAudioRecorder(handleAutoStop);

  // ファイルアップロード関連の状態
  const [uploadResults, setUploadResults] = useState<Array<{
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
    };
  }>>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // ファイルアップロード処理
  const handleFileSelect = useCallback(async (files: File[]) => {
    setIsAnalyzing(true);
    
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    try {
      const results = [];
      
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('document_type', 'sales_document');
        formData.append('analysis_type', 'comprehensive');
        
        const response = await fetch(`${API_BASE_URL}/api/text/upload/analyze`, {
          method: 'POST',
          body: formData,
        });
        
        if (!response.ok) {
          throw new Error(`ファイル分析失敗: ${response.status}`);
        }
        
        const result = await response.json();
        results.push({
          filename: file.name,
          size: (file.size / (1024 * 1024)).toFixed(2) + 'MB',
          type: file.type,
          result
        });
      }
      
      setUploadResults(results);
    } catch (error) {
      console.error('ファイルアップロードエラー:', error);
      // エラーメッセージは画面に表示
      alert('ファイルアップロードに失敗しました');
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  const customerTypes = {
    ANALYTICAL: '分析重視型',
    DRIVER: '結果重視型',
    EXPRESSIVE: '表現重視型',
    AMIABLE: '協調重視型',
    COLLABORATIVE: '協力重視型',
    SKEPTICAL: '懐疑的型',
  };

  // セッション管理
  const handleStartSession = async () => {
    try {
      console.log('セッション開始を試みています...');
      await startSession(customerType);
      console.log('セッション開始成功');
    } catch (error) {
      console.error('セッション開始エラー:', error);
      alert('セッションの開始に失敗しました。バックエンドサーバーが起動していることを確認してください。');
    }
  };

  const handleEndSession = () => {
    endSession();
    resetRecording();
  };

  // 手動での音声処理
  const handleProcessRecording = async () => {
    if (audioBlob) {
      await processVoiceInput(audioBlob);
      resetRecording();
    }
  };

  // 自動モード切り替え
  const toggleAutoMode = () => {
    const newAutoMode = !autoModeEnabled;
    setAutoModeEnabled(newAutoMode);
    setAutoStopEnabled(newAutoMode);
  };

  // 録音時間のフォーマット
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // ステップ表示
  const getStepMessage = () => {
    switch (currentStep) {
      case 'transcribing':
        return '🎤 音声を認識中...';
      case 'analyzing':
        return '🧠 AI分析中...';
      case 'synthesizing':
        return '🔊 音声を生成中...';
      case 'complete':
        return '✅ 処理完了';
      case 'error':
        return '❌ エラーが発生しました';
      default:
        return '';
    }
  };

  // 音声レベルインジケーター
  const getVoiceIndicator = () => {
    if (!isRecording) return '🎤';
    if (isListening) return '🔴'; // 音声検知中
    return '⚪'; // 無音状態
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <Link href="/" className="text-blue-600 hover:text-blue-800">
                <span className="text-2xl font-bold">🎭 Voice Roleplay</span>
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                セッション: {currentSession ? '🟢 アクティブ' : '⚫ 未開始'}
              </span>
              {currentSession && (
                <span className="text-sm text-gray-500">
                  {customerTypes[customerType as keyof typeof customerTypes]}
                </span>
              )}
              <Link
                href="/"
                className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium"
              >
                ホームに戻る
              </Link>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* ファイルアップロードセクションを最上部に移動 */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg shadow-lg p-6 mb-8 border border-blue-200">
          <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
            <span className="text-2xl mr-2">📁</span>
            ナレッジファイルアップロード
          </h3>
          
          <p className="text-sm text-gray-600 mb-4">
            商品資料や営業マニュアルをアップロードすることで、AIがより詳細な商品知識を持って応答します。
          </p>
          
          <FileUpload
            onFileSelect={handleFileSelect}
            multiple={true}
            className="mb-4"
          />
          
          {isAnalyzing && (
            <div className="text-center py-4">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              <p className="text-gray-600 mt-2">ファイルを分析中...</p>
            </div>
          )}
          
          {uploadResults.length > 0 && (
            <div className="mt-4 space-y-4">
              <h4 className="font-medium text-gray-800 flex items-center">
                <span className="text-lg mr-2">📊</span>
                分析結果
              </h4>
              <div className="max-h-60 overflow-y-auto space-y-2">
                {uploadResults.map((result, index) => (
                  <FileAnalysisResult key={index} result={result} />
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 左側: 設定パネル */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              🎯 ロールプレイ設定
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  顧客タイプ
                </label>
                <select
                  value={customerType}
                  onChange={e => setCustomerType(e.target.value)}
                  disabled={!!currentSession}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                >
                  {Object.entries(customerTypes).map(([key, value]) => (
                    <option key={key} value={key}>
                      {value}
                    </option>
                  ))}
                </select>
              </div>

              {/* 自動モード切り替え */}
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="autoMode"
                  checked={autoModeEnabled}
                  onChange={toggleAutoMode}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="autoMode" className="text-sm font-medium text-gray-700">
                  🤖 自動会話モード (2秒無音で自動応答)
                </label>
              </div>

              {/* ノイズキャンセル切り替え */}
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="noiseSuppression"
                  checked={noiseSuppressionEnabled}
                  onChange={(e) => setNoiseSuppressionEnabled(e.target.checked)}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="noiseSuppression" className="text-sm font-medium text-gray-700">
                  🔇 ノイズキャンセル機能 (背景音を除去)
                </label>
              </div>

              <div className="pt-4">
                {!currentSession ? (
                  <button
                    onClick={handleStartSession}
                    className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors cursor-pointer"
                  >
                    🚀 セッション開始
                  </button>
                ) : (
                  <button
                    onClick={handleEndSession}
                    className="w-full bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 transition-colors cursor-pointer"
                  >
                    🛑 セッション終了
                  </button>
                )}
              </div>

              {/* パフォーマンス統計 */}
              {currentSession && performance.totalConversations > 0 && (
                <div className="pt-4 border-t border-gray-200">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">
                    📊 統計
                  </h3>
                  <div className="text-sm text-gray-600 space-y-1">
                    <div>会話回数: {performance.totalConversations}回</div>
                    <div>
                      平均応答時間:{' '}
                      {Math.round(performance.averageResponseTime / 1000)}秒
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 右側: 音声コントロール */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              🎤 音声コントロール
            </h2>

            <div className="space-y-4">
              <div className="flex flex-col items-center space-y-4">
                {/* 録音ビジュアライザー */}
                <div className="w-32 h-32 bg-gray-100 rounded-full flex items-center justify-center relative">
                  {isRecording ? (
                    <div className={`w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300 ${
                      isListening 
                        ? 'bg-green-500 animate-pulse scale-110' 
                        : 'bg-red-500 animate-pulse'
                    }`}>
                      <span className="text-white text-2xl">{getVoiceIndicator()}</span>
                    </div>
                  ) : isProcessing ? (
                    <div className="w-16 h-16 bg-blue-500 rounded-full animate-spin flex items-center justify-center">
                      <span className="text-white text-2xl">⚙️</span>
                    </div>
                  ) : (
                    <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center hover:bg-blue-600 transition-colors cursor-pointer">
                      <span className="text-white text-2xl">🎤</span>
                    </div>
                  )}
                  
                  {/* 自動モード表示 */}
                  {autoModeEnabled && (
                    <div className="absolute top-0 right-0 bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">
                      AUTO
                    </div>
                  )}
                </div>

                {/* 録音時間と状態 */}
                {isRecording && (
                  <div className="text-center">
                    <div className="text-lg font-mono text-gray-700">
                      {formatTime(recordingTime)}
                    </div>
                    <div className="text-sm text-gray-500">
                      {autoModeEnabled ? '話し終わったら2秒待機してください' : '手動で停止してください'}
                    </div>
                    {isListening && (
                      <div className="text-xs text-green-600 font-medium">
                        🎵 音声検知中
                      </div>
                    )}
                  </div>
                )}

                {/* 処理ステップ表示 */}
                {isProcessing && (
                  <div className="text-sm text-blue-600 font-medium">
                    {getStepMessage()}
                  </div>
                )}

                {/* 録音コントロール */}
                <div className="flex space-x-2">
                  {!isRecording ? (
                    <button
                      onClick={startRecording}
                      disabled={!currentSession || isProcessing}
                      className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-400 cursor-pointer disabled:cursor-not-allowed"
                    >
                      🎙️ 録音開始
                    </button>
                  ) : (
                    <>
                      {!isPaused ? (
                        <button
                          onClick={pauseRecording}
                          className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 transition-colors cursor-pointer"
                        >
                          ⏸️ 一時停止
                        </button>
                      ) : (
                        <button
                          onClick={resumeRecording}
                          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors cursor-pointer"
                        >
                          ▶️ 再開
                        </button>
                      )}
                      <button
                        onClick={stopRecording}
                        className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors cursor-pointer"
                      >
                        ⏹️ 停止
                      </button>
                    </>
                  )}
                </div>

                {/* 録音後の操作（手動モードのみ） */}
                {audioBlob && !isRecording && !autoModeEnabled && (
                  <div className="flex space-x-2">
                    <button
                      onClick={handleProcessRecording}
                      disabled={isProcessing}
                      className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:bg-gray-400 cursor-pointer disabled:cursor-not-allowed"
                    >
                      🚀 AI分析開始
                    </button>
                    <button
                      onClick={resetRecording}
                      disabled={isProcessing}
                      className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors disabled:bg-gray-400 cursor-pointer disabled:cursor-not-allowed"
                    >
                      🔄 リセット
                    </button>
                  </div>
                )}
              </div>

              {/* エラー表示 */}
              {(recordingError || conversationError) && (
                <div className="bg-red-50 border border-red-200 rounded-md p-3">
                  <p className="text-red-800 text-sm">
                    {recordingError || conversationError}
                  </p>
                </div>
              )}

              {/* セッション未開始の警告 */}
              {!currentSession && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                  <p className="text-yellow-800 text-sm">
                    セッションを開始してください
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 会話履歴 */}
        {history.length > 0 && (
          <div className="mt-8 bg-white rounded-lg shadow-sm p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                💬 会話履歴
              </h3>
              <button
                onClick={clearHistory}
                className="text-sm text-gray-500 hover:text-red-600 transition-colors"
              >
                履歴をクリア
              </button>
            </div>

            <div className="space-y-4 max-h-96 overflow-y-auto">
              {history.map((entry: ConversationEntry, index: number) => (
                <div
                  key={entry.id}
                  className="border border-gray-200 rounded-md p-4"
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-sm text-gray-500">
                      会話 #{index + 1} - {entry.timestamp.toLocaleTimeString()}
                    </span>
                    <div className="flex space-x-2 text-xs text-gray-400">
                      <span>🎯 {entry.analysis.intent}</span>
                      <span>😊 {entry.analysis.sentiment}</span>
                      <span>
                        ⚡ {Math.round(entry.performance.totalTime)}ms
                      </span>
                    </div>
                  </div>

                  {/* ユーザー入力 */}
                  <div className="bg-blue-50 rounded-md p-3 mb-2">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="text-sm font-medium text-blue-800">
                          👤 あなた:
                        </span>
                        <p className="text-blue-700 mt-1">
                          {entry.userInput.text}
                        </p>
                      </div>
                      {entry.userInput.audioURL && (
                        <button
                          onClick={() =>
                            playAudioResponse(entry.userInput.audioURL!)
                          }
                          className="text-blue-600 hover:text-blue-800 ml-2"
                        >
                          🔊
                        </button>
                      )}
                    </div>
                  </div>

                  {/* AI応答 */}
                  <div className="bg-green-50 rounded-md p-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="text-sm font-medium text-green-800">
                          🤖 AI顧客:
                        </span>
                        <p className="text-green-700 mt-1">
                          {entry.aiResponse.text}
                        </p>
                      </div>
                      {entry.aiResponse.audioURL && (
                        <button
                          onClick={() =>
                            playAudioResponse(entry.aiResponse.audioURL!)
                          }
                          className="text-green-600 hover:text-green-800 ml-2"
                        >
                          🔊
                        </button>
                      )}
                    </div>
                  </div>

                  {/* 分析結果 */}
                  {entry.analysis.buyingSignals.length > 0 && (
                    <div className="mt-2 text-xs text-gray-600">
                      <span className="font-medium">購買シグナル:</span>{' '}
                      {entry.analysis.buyingSignals.join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 使用方法 */}
        <div className="mt-8 bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            📝 使用方法
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-800 mb-2">🤖 自動会話モード（推奨）</h4>
              <ol className="text-sm text-gray-600 space-y-1">
                <li>1. 顧客タイプを選択</li>
                <li>2. 「セッション開始」をクリック</li>
                <li>3. 「録音開始」をクリック</li>
                <li>4. 営業トークを話す</li>
                <li>5. 話し終わったら2秒待機</li>
                <li>6. 自動でAI応答が返ってくる</li>
                <li>7. 続けて会話する</li>
              </ol>
            </div>
            <div>
              <h4 className="font-medium text-gray-800 mb-2">✋ 手動モード</h4>
              <ol className="text-sm text-gray-600 space-y-1">
                <li>1. 自動会話モードのチェックを外す</li>
                <li>2. 顧客タイプを選択してセッション開始</li>
                <li>3. 「録音開始」で営業トークを録音</li>
                <li>4. 「停止」をクリック</li>
                <li>5. 「AI分析開始」をクリック</li>
                <li>6. AI応答を確認して次の録音へ</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
