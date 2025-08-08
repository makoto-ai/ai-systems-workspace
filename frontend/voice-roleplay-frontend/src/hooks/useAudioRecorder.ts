/**
 * 音声録音のためのカスタムフック
 * WebAudio API を使用してブラウザでの音声録音を実現
 * 無音検知による自動録音停止機能付き
 */

import { useCallback, useRef, useState } from 'react';

export interface AudioRecorderState {
  isRecording: boolean;
  isPaused: boolean;
  recordingTime: number;
  audioBlob: Blob | null;
  audioURL: string | null;
  error: string | null;
  isListening: boolean; // 音声検知状態
}

export interface AudioRecorderControls {
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  pauseRecording: () => void;
  resumeRecording: () => void;
  resetRecording: () => void;
  downloadRecording: () => void;
  setAutoStopEnabled: (enabled: boolean) => void;
}

// 無音検知設定
const SILENCE_THRESHOLD = 0.02; // 無音と判定する音量閾値（感度を上げる）
const SILENCE_DURATION = 1500; // 1.5秒無音で自動停止（反応を早くする）
const VOLUME_CHECK_INTERVAL = 50; // 音量チェック間隔（ms）を短くして反応速度向上

export function useAudioRecorder(
  onAutoStop?: (audioBlob: Blob) => void // 自動停止時のコールバック（音声ファイル付き）
): AudioRecorderState & AudioRecorderControls {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioURL, setAudioURL] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [autoStopEnabled, setAutoStopEnabled] = useState(true);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  
  // 無音検知用
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const silenceStartTimeRef = useRef<number | null>(null);
  const volumeCheckIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // 録音時間の更新
  const updateRecordingTime = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    intervalRef.current = setInterval(() => {
      setRecordingTime(prev => prev + 1);
    }, 1000);
  }, []);

  // 音量レベルをチェック
  const checkVolumeLevel = useCallback(() => {
    if (!analyserRef.current || !autoStopEnabled) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);
    
    // 平均音量を計算
    const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
    const normalizedVolume = average / 255;
    
    setIsListening(normalizedVolume > SILENCE_THRESHOLD);

    if (normalizedVolume > SILENCE_THRESHOLD) {
      // 音声検知 - 無音タイマーをリセット
      silenceStartTimeRef.current = null;
    } else {
      // 無音検知
      if (silenceStartTimeRef.current === null) {
        silenceStartTimeRef.current = Date.now();
      } else {
        const silenceDuration = Date.now() - silenceStartTimeRef.current;
                 if (silenceDuration >= SILENCE_DURATION) {
           // 2秒以上無音 - 自動停止
           console.log('Auto-stopping due to silence detection');
           
           // 音声データを保存してからコールバック実行
           if (onAutoStop && mediaRecorderRef.current && chunksRef.current.length > 0) {
             // 録音を停止してblobを作成
             mediaRecorderRef.current.addEventListener('stop', () => {
               const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
               setTimeout(() => onAutoStop(blob), 100);
             }, { once: true });
           }
           
           stopRecording();
         }
      }
    }
  }, [autoStopEnabled, onAutoStop]); // eslint-disable-line react-hooks/exhaustive-deps

  // 無音検知の開始
  const startVolumeMonitoring = useCallback((stream: MediaStream) => {
    try {
      audioContextRef.current = new AudioContext();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      
      analyserRef.current.fftSize = 256;
      analyserRef.current.smoothingTimeConstant = 0.3;
      source.connect(analyserRef.current);
      
      volumeCheckIntervalRef.current = setInterval(checkVolumeLevel, VOLUME_CHECK_INTERVAL);
    } catch (error) {
      console.warn('Failed to start volume monitoring:', error);
    }
  }, [checkVolumeLevel]);

  // 無音検知の停止
  const stopVolumeMonitoring = useCallback(() => {
    if (volumeCheckIntervalRef.current) {
      clearInterval(volumeCheckIntervalRef.current);
      volumeCheckIntervalRef.current = null;
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    analyserRef.current = null;
    silenceStartTimeRef.current = null;
    setIsListening(false);
  }, []);

  // 録音開始
  const startRecording = useCallback(async () => {
    try {
      setError(null);
      console.log('録音開始処理を開始...');

      // マイクアクセス許可を取得
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          // ノイズキャンセル設定
          echoCancellation: true,        // エコーキャンセレーション
          noiseSuppression: true,        // ノイズ抑制
          autoGainControl: true,         // 自動ゲイン制御
          
          // 追加の音声品質設定
          sampleRate: 44100,             // サンプリングレート (44.1kHz)
          channelCount: 1,               // モノラル録音（ファイルサイズ削減）
          sampleSize: 16,                // ビット深度
          
          // 高度なノイズ抑制設定（ブラウザがサポートしている場合）
          googEchoCancellation: true,    // Google Chrome用の高度なエコーキャンセル
          googAutoGainControl: true,     // Google Chrome用の高度な自動ゲイン制御
          googNoiseSuppression: true,    // Google Chrome用の高度なノイズ抑制
          googHighpassFilter: true,      // 低周波ノイズを除去
          googTypingNoiseDetection: true // タイピング音の検出と除去
        } as MediaTrackConstraints,
      });

      console.log('マイクアクセス許可取得成功');
      streamRef.current = stream;

      // MediaRecorderの設定
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus', // 高品質・低容量
        audioBitsPerSecond: 256000, // 256kbps for higher quality audio recognition
      });

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      // データ受信時の処理
      mediaRecorder.ondataavailable = event => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
          console.log('音声データチャンク受信:', event.data.size, 'bytes');
        }
      };

      // 録音停止時の処理
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        setAudioURL(URL.createObjectURL(blob));
        console.log('録音停止完了。音声ファイルサイズ:', blob.size, 'bytes');

        // ストリームの停止
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
        
        // 無音検知停止
        stopVolumeMonitoring();
      };

      // 録音開始
      mediaRecorder.start(1000); // 1秒ごとにデータチャンクを生成
      setIsRecording(true);
      setRecordingTime(0);
      updateRecordingTime();
      console.log('録音開始成功');
      
      // 無音検知開始
      if (autoStopEnabled) {
        console.log('自動停止モード有効 - 無音検知開始');
        startVolumeMonitoring(stream);
      }
    } catch (err) {
      console.error('録音開始エラー:', err);
      let errorMessage = '録音開始に失敗しました';
      
      if (err instanceof Error) {
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
          errorMessage = 'マイクへのアクセスが拒否されました。ブラウザの設定でマイクの使用を許可してください。';
        } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
          errorMessage = 'マイクが見つかりません。マイクが接続されているか確認してください。';
        } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
          errorMessage = 'マイクが他のアプリケーションで使用されています。';
        } else {
          errorMessage = `録音開始に失敗しました: ${err.message}`;
        }
      }
      
      setError(errorMessage);
    }
  }, [updateRecordingTime, autoStopEnabled, startVolumeMonitoring, stopVolumeMonitoring]);

  // 録音停止
  const stopRecording = useCallback(() => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !== 'inactive'
    ) {
      mediaRecorderRef.current.stop();
    }

    setIsRecording(false);
    setIsPaused(false);

    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    
    stopVolumeMonitoring();
  }, [stopVolumeMonitoring]);

  // 録音一時停止
  const pauseRecording = useCallback(() => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state === 'recording'
    ) {
      mediaRecorderRef.current.pause();
      setIsPaused(true);

      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      
      stopVolumeMonitoring();
    }
  }, [stopVolumeMonitoring]);

  // 録音再開
  const resumeRecording = useCallback(() => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state === 'paused'
    ) {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
      updateRecordingTime();
      
      if (autoStopEnabled && streamRef.current) {
        startVolumeMonitoring(streamRef.current);
      }
    }
  }, [updateRecordingTime, autoStopEnabled, startVolumeMonitoring]);

  // 録音リセット
  const resetRecording = useCallback(() => {
    stopRecording();
    setRecordingTime(0);
    setAudioBlob(null);

    if (audioURL) {
      URL.revokeObjectURL(audioURL);
      setAudioURL(null);
    }

    setError(null);
  }, [stopRecording, audioURL]);

  // 録音ダウンロード
  const downloadRecording = useCallback(() => {
    if (audioBlob && audioURL) {
      const link = document.createElement('a');
      link.href = audioURL;
      link.download = `recording-${new Date().toISOString()}.webm`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  }, [audioBlob, audioURL]);

  return {
    // State
    isRecording,
    isPaused,
    recordingTime,
    audioBlob,
    audioURL,
    error,
    isListening,

    // Controls
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    resetRecording,
    downloadRecording,
    setAutoStopEnabled,
  };
}

export default useAudioRecorder;
