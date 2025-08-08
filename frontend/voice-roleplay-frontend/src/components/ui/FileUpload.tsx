'use client';

import React, { useCallback } from 'react';
import { useDropzone, FileRejection } from 'react-dropzone';

interface FileUploadProps {
  onFileSelect: (files: File[]) => void;
  accept?: Record<string, string[]>;
  multiple?: boolean;
  maxSize?: number;
  className?: string;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelect,
  accept = {
    'text/*': ['.txt', '.md', '.json', '.yaml', '.xml'],
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
    'audio/*': ['.wav', '.mp3', '.m4a', '.flac', '.ogg'],
    'video/*': ['.mp4', '.avi', '.mov', '.webm', '.mkv']
  },
  multiple = false,
  maxSize = 200 * 1024 * 1024, // 200MB
  className = ''
}) => {
  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
    if (rejectedFiles.length > 0) {
      const firstError = rejectedFiles[0]?.errors?.[0];
      alert(`ファイルが拒否されました: ${firstError?.message || 'Unknown error'}`);
      return;
    }
    
    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    multiple,
    maxSize,
    onError: (error: Error) => {
      console.error('ファイルアップロードエラー:', error);
      alert('ファイルアップロードでエラーが発生しました');
    }
  });

  return (
    <div className={`file-upload ${className}`}>
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer
          transition-colors duration-200 ease-in-out
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'hover:border-gray-400 hover:bg-gray-50'}
        `}
      >
        <input {...getInputProps()} />
        
        <div className="space-y-4">
          <div className="text-6xl">📁</div>
          
          {isDragActive ? (
            <p className="text-lg text-blue-600 font-medium">
              ここにファイルをドロップしてください
            </p>
          ) : (
            <div className="space-y-2">
              <p className="text-lg text-gray-700 font-medium">
                ファイルをドラッグ&ドロップまたはクリックして選択
              </p>
              <p className="text-sm text-gray-500">
                {multiple ? '複数ファイル対応' : '単一ファイル'}・最大200MB
              </p>
            </div>
          )}
          
          <div className="text-xs text-gray-400 space-y-1">
            <p><strong>対応形式:</strong></p>
            <p>📄 文書: PDF, Word, Excel, PowerPoint, テキスト</p>
            <p>🎵 音声: WAV, MP3, M4A, FLAC, OGG</p>
            <p>🎬 動画: MP4, AVI, MOV, WebM, MKV</p>
            <p>💻 コード: Python, JavaScript, Java, C++, など</p>
          </div>
        </div>
      </div>
    </div>
  );
}; 