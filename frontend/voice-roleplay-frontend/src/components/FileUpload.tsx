"use client"

import React, { useState, useCallback } from 'react'
import { Upload, FileAudio, FileImage, FileText, Check, AlertCircle, Loader2, Smartphone, Download } from 'lucide-react'
import MobileVoiceRecorder from './MobileVoiceRecorder'

interface FileUploadProps {
  onUploadComplete?: (result: any) => void
}

interface UploadResult {
  status: 'success' | 'error'
  message: string
  fileName?: string
  content?: string
  analysis?: string
  markdownContent?: string
  fileType?: string
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadComplete }) => {
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadResults, setUploadResults] = useState<UploadResult[]>([])
  const [showMobileRecorder, setShowMobileRecorder] = useState(false)

  // モバイル判定
  const isMobile = typeof window !== 'undefined' && /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)

  const getFileIcon = (filename: string) => {
    const ext = filename.toLowerCase().split('.').pop()
    
    if (['wav', 'mp3', 'm4a', 'flac', 'webm'].includes(ext || '')) {
      return <FileAudio className="w-6 h-6 text-blue-500" />
    }
    if (['jpg', 'jpeg', 'png', 'gif', 'bmp'].includes(ext || '')) {
      return <FileImage className="w-6 h-6 text-green-500" />
    }
    if (['pdf', 'docx', 'txt'].includes(ext || '')) {
      return <FileText className="w-6 h-6 text-purple-500" />
    }
    return <FileText className="w-6 h-6 text-gray-500" />
  }

  const uploadFile = async (file: File): Promise<UploadResult> => {
    try {
      const formData = new FormData()
      formData.append('file', file)

      // Vercel Functions APIエンドポイント使用
      const response = await fetch('/api/file-upload/process', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      
      if (result.success) {
        return {
          status: 'success',
          message: `✅ ${file.name} の処理が完了しました`,
          fileName: result.fileName,
          content: result.content,
          analysis: result.analysis,
          markdownContent: result.markdownContent,
          fileType: result.fileType
        }
      } else {
        throw new Error(result.message || '処理に失敗しました')
      }
      
    } catch (error) {
      return {
        status: 'error',
        message: `❌ ${file.name}: ${error instanceof Error ? error.message : String(error)}`
      }
    }
  }

  const uploadAudioBlob = async (audioBlob: Blob): Promise<UploadResult> => {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const file = new File([audioBlob], `voice-recording-${timestamp}.webm`, { 
      type: audioBlob.type || 'audio/webm' 
    })
    
    return await uploadFile(file)
  }

  const handleFiles = async (files: FileList) => {
    setUploading(true)
    setUploadResults([])

    const results: UploadResult[] = []

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      const result = await uploadFile(file)
      results.push(result)
      
      // リアルタイムで結果を表示
      setUploadResults([...results])
    }

    setUploading(false)
    onUploadComplete?.(results)
  }

  const handleMobileRecording = async (audioBlob: Blob) => {
    setUploading(true)
    const result = await uploadAudioBlob(audioBlob)
    setUploadResults([result])
    setUploading(false)
    onUploadComplete?.([result])
  }

  const downloadMarkdown = (result: UploadResult) => {
    if (!result.markdownContent || !result.fileName) return
    
    const blob = new Blob([result.markdownContent], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = result.fileName
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    if (e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files)
    }
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files)
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6">
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
          🌐 クラウド対応 ファイル処理システム
        </h1>
        <p className="text-sm sm:text-base text-gray-600">
          音声・画像・文書ファイルをクラウドで処理し、AI分析結果をダウンロードできます
        </p>
        
        {/* モバイル検出表示 */}
        {isMobile && (
          <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-center space-x-2">
            <Smartphone className="w-5 h-5 text-blue-500 flex-shrink-0" />
            <span className="text-sm text-blue-700">
              📱 モバイル端末対応！音声録音機能が利用可能です
            </span>
          </div>
        )}
      </div>

      {/* モバイル音声録音 */}
      {isMobile && (
        <div className="mb-6">
          <button
            onClick={() => setShowMobileRecorder(!showMobileRecorder)}
            className="w-full sm:w-auto flex items-center justify-center space-x-2 px-6 py-3 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors duration-200"
          >
            <FileAudio className="w-5 h-5" />
            <span>{showMobileRecorder ? '音声録音を閉じる' : '🎤 音声録音を開始'}</span>
          </button>
          
          {showMobileRecorder && (
            <div className="mt-4">
              <MobileVoiceRecorder 
                onRecordingComplete={handleMobileRecording}
                onError={(error) => {
                  setUploadResults([{
                    status: 'error',
                    message: `録音エラー: ${error}`
                  }])
                }}
              />
            </div>
          )}
        </div>
      )}

      {/* ドロップゾーン */}
      <div
        className={`
          border-2 border-dashed rounded-xl p-8 sm:p-12 text-center transition-all duration-200
          ${isDragging 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400'
          }
          ${uploading ? 'opacity-50 pointer-events-none' : ''}
        `}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        <div className="flex flex-col items-center space-y-4">
          {uploading ? (
            <Loader2 className="w-10 h-10 sm:w-12 sm:h-12 text-blue-500 animate-spin" />
          ) : (
            <Upload className="w-10 h-10 sm:w-12 sm:h-12 text-gray-400" />
          )}
          
          <div>
            <p className="text-lg sm:text-xl font-medium text-gray-700 mb-2">
              {uploading ? 'クラウド処理中...' : 'ファイルをドロップするか、クリックして選択'}
            </p>
            <p className="text-xs sm:text-sm text-gray-500">
              対応形式: 音声(.wav, .mp3, .m4a, .webm), 画像(.jpg, .png), 文書(.pdf, .docx, .txt)
            </p>
          </div>

          <input
            type="file"
            multiple
            accept=".wav,.mp3,.m4a,.flac,.webm,.jpg,.jpeg,.png,.gif,.bmp,.pdf,.docx,.txt"
            onChange={handleFileInput}
            className="hidden"
            id="file-input"
            disabled={uploading}
          />
          
          <label
            htmlFor="file-input"
            className={`
              px-4 py-2 sm:px-6 sm:py-3 bg-blue-500 text-white rounded-lg font-medium cursor-pointer text-sm sm:text-base
              hover:bg-blue-600 transition-colors duration-200
              ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
            `}
          >
            ファイルを選択
          </label>
        </div>
      </div>

      {/* 結果表示 */}
      {uploadResults.length > 0 && (
        <div className="mt-6 sm:mt-8">
          <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-4">
            処理結果
          </h2>
          
          <div className="space-y-4">
            {uploadResults.map((result, index) => (
              <div
                key={index}
                className={`
                  p-4 rounded-lg border
                  ${result.status === 'success' 
                    ? 'bg-green-50 border-green-200' 
                    : 'bg-red-50 border-red-200'
                  }
                `}
              >
                <div className="flex items-start space-x-3">
                  {result.status === 'success' ? (
                    <Check className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                  )}
                  
                  <div className="flex-1 min-w-0">
                    <p className={`font-medium text-sm sm:text-base ${
                      result.status === 'success' ? 'text-green-800' : 'text-red-800'
                    }`}>
                      {result.message}
                    </p>
                    
                    {result.status === 'success' && result.markdownContent && (
                      <div className="mt-3 flex items-center space-x-2">
                        <button
                          onClick={() => downloadMarkdown(result)}
                          className="flex items-center space-x-1 px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition-colors"
                        >
                          <Download className="w-3 h-3" />
                          <span>Markdownダウンロード</span>
                        </button>
                        <span className="text-xs text-gray-500">
                          {result.fileName}
                        </span>
                      </div>
                    )}
                    
                    {result.content && (
                      <div className="mt-2 p-3 bg-white rounded border">
                        <p className="text-xs sm:text-sm font-medium text-gray-700 mb-1">処理結果:</p>
                        <p className="text-xs sm:text-sm text-gray-600 line-clamp-3">{result.content}</p>
                      </div>
                    )}
                    
                    {result.analysis && (
                      <div className="mt-2 p-3 bg-white rounded border">
                        <p className="text-xs sm:text-sm font-medium text-gray-700 mb-1">AI分析:</p>
                        <p className="text-xs sm:text-sm text-gray-600 line-clamp-3">{result.analysis}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* サポートファイル形式の説明 */}
      <div className="mt-8 sm:mt-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        <div className="text-center p-4 sm:p-6 bg-blue-50 rounded-lg">
          <FileAudio className="w-10 h-10 sm:w-12 sm:h-12 text-blue-500 mx-auto mb-3" />
          <h3 className="font-semibold text-gray-900 mb-2 text-sm sm:text-base">音声ファイル</h3>
          <p className="text-xs sm:text-sm text-gray-600">
            WAV, MP3, M4A, WebM<br/>
            → Groq Whisper文字起こし<br/>
            → AI分析・構造化<br/>
            → Markdownダウンロード
          </p>
        </div>
        
        <div className="text-center p-4 sm:p-6 bg-green-50 rounded-lg">
          <FileImage className="w-10 h-10 sm:w-12 sm:h-12 text-green-500 mx-auto mb-3" />
          <h3 className="font-semibold text-gray-900 mb-2 text-sm sm:text-base">画像ファイル</h3>
          <p className="text-xs sm:text-sm text-gray-600">
            JPG, PNG, GIF, BMP<br/>
            → GPT-4 Vision分析<br/>
            → 内容説明生成<br/>
            → Markdownダウンロード
          </p>
        </div>
        
        <div className="text-center p-4 sm:p-6 bg-purple-50 rounded-lg">
          <FileText className="w-10 h-10 sm:w-12 sm:h-12 text-purple-500 mx-auto mb-3" />
          <h3 className="font-semibold text-gray-900 mb-2 text-sm sm:text-base">文書ファイル</h3>
          <p className="text-xs sm:text-sm text-gray-600">
            PDF, DOCX, TXT<br/>
            → テキスト抽出<br/>
            → AI要約・分析<br/>
            → Markdownダウンロード
          </p>
        </div>
      </div>
      
      <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="flex items-center space-x-2 mb-2">
          <span className="text-yellow-600 font-medium">🌐 クラウド対応完了！</span>
        </div>
        <p className="text-sm text-yellow-700">
          このシステムは完全にクラウドで動作します。どこからでもアクセス可能で、Obsidian連携も利用できます！
        </p>
      </div>
    </div>
  )
}

export default FileUpload
