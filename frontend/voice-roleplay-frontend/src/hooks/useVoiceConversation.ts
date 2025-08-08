import { useState, useCallback, useRef } from 'react';
import {
  ConversationEntry,
  ConversationSession,
  ConversationPerformance,
  ConversationStep,
  VoiceConversationState,
  VoiceConversationControls,
} from '@/types/conversation';

// バックエンドAPIの基本URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// サーバーの状態チェック
const checkServerHealth = async (): Promise<boolean> => {
  try {
    console.log('ヘルスチェック開始: API_BASE_URL =', API_BASE_URL);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      console.log('ヘルスチェックタイムアウト (5秒)');
      controller.abort();
    }, 5000); // 5秒でタイムアウト（バックエンドの初期化時間を考慮）
    
    const response = await fetch(`${API_BASE_URL}/api/health/basic`, {
      method: 'GET',
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    clearTimeout(timeoutId);
    console.log('ヘルスチェック応答:', response.status, response.ok);
    
    if (response.ok) {
      const data = await response.json();
      console.log('ヘルスチェックデータ:', data);
    }
    
    return response.ok;
  } catch (error) {
    console.error('サーバーヘルスチェック失敗:', error);
    console.error('エラー詳細:', {
      message: error instanceof Error ? error.message : 'Unknown error',
      name: error instanceof Error ? error.name : 'Unknown',
      API_BASE_URL,
      timestamp: new Date().toISOString()
    });
    return false;
  }
};

export function useVoiceConversation(): VoiceConversationState &
  VoiceConversationControls {
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState<ConversationStep>('idle');
  const [history, setHistory] = useState<ConversationEntry[]>([]);
  const [currentSession, setCurrentSession] =
    useState<ConversationSession | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [performance, setPerformance] = useState<ConversationPerformance>({
    totalConversations: 0,
    averageResponseTime: 0,
    successRate: 0,
  });

  const audioRef = useRef<HTMLAudioElement | null>(null);

  // 音声応答を再生
  const playAudioResponse = useCallback((audioURL: string) => {
    try {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }

      const audio = new Audio(audioURL);
      audioRef.current = audio;

      audio.onloadeddata = () => {
        audio.play().catch(err => {
          console.warn('音声再生エラー:', err);
        });
      };

      audio.onerror = err => {
        console.error('音声ファイルエラー:', err);
      };
    } catch (err) {
      console.error('音声再生エラー:', err);
    }
  }, []);

  // 音声入力を処理
  const processVoiceInput = useCallback(
    async (audioBlob: Blob) => {
      if (!currentSession) {
        setError('セッションが開始されていません');
        return;
      }

      setIsProcessing(true);
      setError(null);
      setCurrentStep('transcribing');

      const startTime = Date.now();
      let transcriptionTime = 0;
      let analysisTime = 0;
      let synthesisTime = 0;

      try {
        // サーバーの状態をチェック
        const isServerHealthy = await checkServerHealth();
        if (!isServerHealthy) {
          throw new Error('バックエンドサーバーが起動していません。サーバーを起動してください。');
        }

        // 音声データをFormDataに変換
        const formData = new FormData();
        
        // WebMファイルのMIME typeを明示的に設定
        console.log('🎵 Audio Debug:', audioBlob.type, audioBlob.size + 'bytes');
        const mimeType = audioBlob.type.startsWith('audio/') ? audioBlob.type : 'audio/webm';
        const audioFile = new File([audioBlob], 'recording.webm', { type: mimeType });
        console.log('- Sending file type:', mimeType);
        
        formData.append('file', audioFile);
        formData.append('user_id', currentSession.customerType); // セッション管理用

        // 統合音声会話エンドポイントを使用
        const conversationController = new AbortController();
        const conversationTimeoutId = setTimeout(() => conversationController.abort(), 30000); // 30秒でタイムアウト（高速化）
        
        const conversationResponse = await fetch(
          `${API_BASE_URL}/api/voice/conversation`,
          {
            method: 'POST',
            body: formData,
            signal: conversationController.signal,
          }
        );
        
        clearTimeout(conversationTimeoutId);

        if (!conversationResponse.ok) {
          throw new Error(`音声会話エラー: ${conversationResponse.status}`);
        }

        const conversationData = await conversationResponse.json();
        
        // レスポンスから必要なデータを抽出
        const transcriptionData = conversationData.input || {};
        const analysisData = conversationData.dify_analysis || {};
        
        transcriptionTime = conversationData.performance?.transcription_time || 0;
        analysisTime = conversationData.performance?.analysis_time || 0;
        synthesisTime = conversationData.performance?.synthesis_time || 0;

        // 音声データがBase64で返された場合の処理
        let audioURL = null;
        if (conversationData.output?.audio_data) {
          try {
            // Base64データをBlobに変換
            const audioBytes = atob(conversationData.output.audio_data);
            const audioArray = new Uint8Array(audioBytes.length);
            for (let i = 0; i < audioBytes.length; i++) {
              audioArray[i] = audioBytes.charCodeAt(i);
            }
            const audioBlob = new Blob([audioArray], { type: 'audio/wav' });
            audioURL = URL.createObjectURL(audioBlob);
          } catch (error) {
            console.warn('音声データの変換に失敗:', error);
          }
        }

        const totalTime = Date.now() - startTime;

        // 会話履歴に追加
        const newEntry: ConversationEntry = {
          id: `conversation_${Date.now()}`,
          timestamp: new Date(),
          userInput: {
            text: transcriptionData.text || '',
            audioURL: URL.createObjectURL(audioBlob),
          },
          aiResponse: {
            text: conversationData.output?.text || '',
            ...(audioURL && { audioURL }),
          },
                      analysis: {
              intent: analysisData.intent || 'unknown',
              sentiment: analysisData.sentiment || 'neutral',
              buyingSignals: analysisData.buying_signals || [],
            },
          performance: {
            totalTime,
            transcriptionTime,
            analysisTime,
            synthesisTime,
          },
        };

        setHistory(prev => [...prev, newEntry]);

        // パフォーマンス統計を更新
        setPerformance(prev => ({
          totalConversations: prev.totalConversations + 1,
          averageResponseTime:
            prev.totalConversations === 0
              ? totalTime
              : (prev.averageResponseTime * prev.totalConversations +
                  totalTime) /
                (prev.totalConversations + 1),
          successRate: prev.successRate, // 成功率の計算は後で実装
        }));

        // 音声を自動再生
        if (audioURL) {
          playAudioResponse(audioURL);
        }

        setCurrentStep('complete');
      } catch (err) {
        console.error('音声処理エラー:', err);
        setError(
          err instanceof Error
            ? err.message
            : '音声処理中にエラーが発生しました'
        );
        setCurrentStep('error');
      } finally {
        setIsProcessing(false);
      }
    },
    [currentSession, playAudioResponse]
  );

  // 会話セッションを開始
  const startSession = useCallback(async (customerType: string) => {
    try {
      setError(null);
      
      // サーバーの状態をチェック
      const isServerHealthy = await checkServerHealth();
      if (!isServerHealthy) {
        setError('バックエンドサーバーが起動していません。サーバーを起動してください。');
        return;
      }

      const sessionId = `session_${Date.now()}`;
      const session: ConversationSession = {
        id: sessionId,
        customerType,
        startTime: new Date(),
        isActive: true,
      };

      setCurrentSession(session);
      setHistory([]);
      setPerformance({
        totalConversations: 0,
        averageResponseTime: 0,
        successRate: 0,
      });
    } catch (err) {
      console.error('セッション開始エラー:', err);
      setError('セッションの開始に失敗しました');
    }
  }, []);

  // 会話セッションを終了
  const endSession = useCallback(() => {
    if (currentSession) {
      setCurrentSession(null);
      setCurrentStep('idle');
    }
  }, [currentSession]);

  // 会話履歴をクリア
  const clearHistory = useCallback(() => {
    setHistory([]);
    setPerformance({
      totalConversations: 0,
      averageResponseTime: 0,
      successRate: 0,
    });
  }, []);

  // セッション終了後の分析レポート取得
  const getSessionAnalysisReport = useCallback(
    async (sessionId: string, userId: string) => {
      try {
        setIsProcessing(true);
        setCurrentStep('analyzing');

        const formData = new FormData();
        formData.append('session_id', sessionId);
        formData.append('user_id', userId);

        const response = await fetch(`${API_BASE_URL}/api/conversation/end-session-analysis`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`分析失敗: ${response.status}`);
        }

        const result = await response.json();

        if (!result.success) {
          throw new Error(result.error || '分析に失敗しました');
        }

        return result.analysis_report;
      } catch (error) {
        console.error('Session analysis error:', error);
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        setError(`分析エラー: ${errorMessage}`);
        throw error;
      } finally {
        setIsProcessing(false);
        setCurrentStep('idle');
      }
    },
    []
  );

  return {
    // State
    isProcessing,
    currentStep,
    history,
    currentSession,
    error,
    performance,

    // Controls
    processVoiceInput,
    startSession,
    endSession,
    clearHistory,
    playAudioResponse,
    getSessionAnalysisReport,  // 新しく追加
  };
}

export default useVoiceConversation;
