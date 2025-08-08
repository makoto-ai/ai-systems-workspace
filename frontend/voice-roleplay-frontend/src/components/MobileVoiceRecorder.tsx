"use client"

import React, { useState, useRef, useEffect } from 'react'
import { Mic, MicOff, Square, Play, Pause } from 'lucide-react'

interface MobileVoiceRecorderProps {
  onRecordingComplete?: (audioBlob: Blob) => void
  onError?: (error: string) => void
}

const MobileVoiceRecorder: React.FC<MobileVoiceRecorderProps> = ({ 
  onRecordingComplete, 
  onError 
}) => {
  const [isRecording, setIsRecording] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // モバイル用のメディア制約
  const getMediaConstraints = () => ({
    audio: {
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
      sampleRate: 44100,
      channelCount: 1,
      // モバイル対応の追加設定
      latency: 0.2,
      googEchoCancellation: true,
      googAutoGainControl: true,
      googNoiseSuppression: true,
      googHighpassFilter: true,
      googTypingNoiseDetection: true,
    } as MediaTrackConstraints
  })

  const startRecording = async () => {
    try {
      // モバイルブラウザでの権限要求
      const stream = await navigator.mediaDevices.getUserMedia(getMediaConstraints())
      streamRef.current = stream

      // MediaRecorderの作成（モバイル対応形式）
      const options: MediaRecorderOptions = {}
      
      // モバイル対応のMIMEタイプ選択
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        options.mimeType = 'audio/webm;codecs=opus'
      } else if (MediaRecorder.isTypeSupported('audio/webm')) {
        options.mimeType = 'audio/webm'
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        options.mimeType = 'audio/mp4'
      } else if (MediaRecorder.isTypeSupported('audio/wav')) {
        options.mimeType = 'audio/wav'
      }

      mediaRecorderRef.current = new MediaRecorder(stream, options)
      chunksRef.current = []

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { 
          type: mediaRecorderRef.current?.mimeType || 'audio/webm' 
        })
        
        // 音声URLの作成
        const url = URL.createObjectURL(audioBlob)
        setAudioUrl(url)
        
        // コールバック実行
        onRecordingComplete?.(audioBlob)
        
        // ストリームのクリーンアップ
        streamRef.current?.getTracks().forEach(track => track.stop())
      }

      // 録音開始
      mediaRecorderRef.current.start(100) // 100msごとにデータ収集
      setIsRecording(true)
      setRecordingTime(0)

      // タイマー開始
      intervalRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'マイクアクセスに失敗しました'
      onError?.(errorMessage)
      console.error('Recording error:', err)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }

  const playRecording = () => {
    if (audioUrl && audioRef.current) {
      audioRef.current.src = audioUrl
      audioRef.current.play()
      setIsPlaying(true)
    }
  }

  const pausePlayback = () => {
    if (audioRef.current) {
      audioRef.current.pause()
      setIsPlaying(false)
    }
  }

  // コンポーネントアンマウント時のクリーンアップ
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="flex flex-col items-center space-y-4 p-6 bg-white rounded-lg shadow-lg">
      {/* 録音時間表示 */}
      <div className="text-2xl font-mono text-gray-700">
        {formatTime(recordingTime)}
      </div>

      {/* 録音ボタン */}
      <div className="flex items-center space-x-4">
        {!isRecording ? (
          <button
            onClick={startRecording}
            className="flex items-center justify-center w-16 h-16 bg-red-500 hover:bg-red-600 text-white rounded-full shadow-lg active:scale-95 transition-all duration-200"
            aria-label="録音開始"
          >
            <Mic className="w-8 h-8" />
          </button>
        ) : (
          <button
            onClick={stopRecording}
            className="flex items-center justify-center w-16 h-16 bg-gray-500 hover:bg-gray-600 text-white rounded-full shadow-lg active:scale-95 transition-all duration-200"
            aria-label="録音停止"
          >
            <Square className="w-8 h-8" />
          </button>
        )}
      </div>

      {/* 録音状態表示 */}
      {isRecording && (
        <div className="flex items-center space-x-2 text-red-500">
          <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
          <span className="text-sm font-medium">録音中...</span>
        </div>
      )}

      {/* 再生コントロール */}
      {audioUrl && !isRecording && (
        <div className="flex items-center space-x-2">
          <button
            onClick={isPlaying ? pausePlayback : playRecording}
            className="flex items-center justify-center w-10 h-10 bg-blue-500 hover:bg-blue-600 text-white rounded-full active:scale-95 transition-all duration-200"
            aria-label={isPlaying ? "再生停止" : "再生"}
          >
            {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
          </button>
          <span className="text-sm text-gray-600">録音を再生</span>
        </div>
      )}

      {/* 隠し音声要素 */}
      <audio
        ref={audioRef}
        onEnded={() => setIsPlaying(false)}
        className="hidden"
      />

      {/* モバイル用の説明 */}
      <div className="text-xs text-gray-500 text-center max-w-sm">
        マイクアクセスを許可してください。録音ボタンをタップして開始できます。
      </div>
    </div>
  )
}

export default MobileVoiceRecorder
