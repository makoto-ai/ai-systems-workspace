'use client'

import React, { useState } from 'react';
import Link from 'next/link';
import { Menu, X, Smartphone } from 'lucide-react';

export default function Home(): React.JSX.Element {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
                  🎭 Voice Roleplay System
                </h1>
              </div>
            </div>
            
            {/* Desktop Navigation */}
            <nav className="hidden md:flex space-x-8">
              <Link
                href="/"
                className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium transition-colors"
              >
                ホーム
              </Link>
              <Link
                href="/roleplay"
                className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium transition-colors"
              >
                ロールプレイ
              </Link>
              <Link
                href="/file-upload"
                className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium transition-colors"
              >
                🔄 ファイル連携
              </Link>
              <Link
                href="/analytics"
                className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium transition-colors"
              >
                分析
              </Link>
              <Link
                href="/settings"
                className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium transition-colors"
              >
                設定
              </Link>
            </nav>

            {/* Mobile menu button */}
            <div className="md:hidden">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
                aria-expanded="false"
              >
                <span className="sr-only">メインメニューを開く</span>
                {mobileMenuOpen ? (
                  <X className="block h-6 w-6" aria-hidden="true" />
                ) : (
                  <Menu className="block h-6 w-6" aria-hidden="true" />
                )}
              </button>
            </div>
          </div>

          {/* Mobile Navigation */}
          {mobileMenuOpen && (
            <div className="md:hidden">
              <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-gray-50 rounded-lg mb-4">
                <Link
                  href="/"
                  className="text-gray-700 hover:text-blue-600 block px-3 py-2 text-base font-medium transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  🏠 ホーム
                </Link>
                <Link
                  href="/roleplay"
                  className="text-gray-700 hover:text-blue-600 block px-3 py-2 text-base font-medium transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  🎭 ロールプレイ
                </Link>
                <Link
                  href="/file-upload"
                  className="text-gray-700 hover:text-blue-600 block px-3 py-2 text-base font-medium transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  🔄 ファイル連携
                </Link>
                <Link
                  href="/analytics"
                  className="text-gray-700 hover:text-blue-600 block px-3 py-2 text-base font-medium transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  📊 分析
                </Link>
                <Link
                  href="/settings"
                  className="text-gray-700 hover:text-blue-600 block px-3 py-2 text-base font-medium transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  ⚙️ 設定
                </Link>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Hero Section */}
        <div className="text-center mb-12 sm:mb-16">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-gray-900">
            営業スキルを向上させる
            <span className="text-blue-600">AIロールプレイ</span>
          </h2>
          <p className="mt-4 text-lg sm:text-xl text-gray-600 max-w-3xl mx-auto">
            リアルタイム音声認識とAI分析で、実践的な営業トレーニングを体験。
            顧客タイプに応じた最適な対応を学び、営業成績を向上させましょう。
          </p>
          
          {/* モバイル対応の説明 */}
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg max-w-2xl mx-auto">
            <div className="flex items-center justify-center space-x-2 mb-2">
              <Smartphone className="w-5 h-5 text-blue-500" />
              <span className="text-blue-700 font-medium">📱 モバイル完全対応</span>
            </div>
            <p className="text-sm text-blue-600">
              スマートフォン・タブレットでも音声録音、ファイルアップロード、AIロールプレイが利用可能！
            </p>
          </div>
          
          <div className="mt-8 flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-4">
            <Link
              href="/roleplay"
              className="inline-flex items-center justify-center px-6 sm:px-8 py-3 border border-transparent text-base font-medium 
              rounded-md text-white bg-blue-600 hover:bg-blue-700 transition-colors w-full sm:w-auto"
            >
              🎯 今すぐ始める
            </Link>
            <Link
              href="/file-upload"
              className="inline-flex items-center justify-center px-6 sm:px-8 py-3 border border-gray-300 text-base font-medium 
              rounded-md text-gray-700 bg-white hover:bg-gray-50 transition-colors w-full sm:w-auto"
            >
              🔄 ファイル連携
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8 mb-12 sm:mb-16">
          <div className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center mb-4">
              <div className="bg-blue-100 p-3 rounded-full">
                <span className="text-2xl">🎙️</span>
              </div>
              <h3 className="ml-3 text-lg font-semibold text-gray-900">
                音声認識
              </h3>
            </div>
            <p className="text-gray-600 text-sm sm:text-base">
              高精度な音声認識技術で、自然な会話をリアルタイムで分析。
              スマホでも高品質な音声入力が可能。
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center mb-4">
              <div className="bg-green-100 p-3 rounded-full">
                <span className="text-2xl">🤖</span>
              </div>
              <h3 className="ml-3 text-lg font-semibold text-gray-900">
                AI分析
              </h3>
            </div>
            <p className="text-gray-600 text-sm sm:text-base">
              営業会話を自動分析し、顧客タイプの特定、BANT資格確認、
              改善点の提案を行います。
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center mb-4">
              <div className="bg-purple-100 p-3 rounded-full">
                <span className="text-2xl">📱</span>
              </div>
              <h3 className="ml-3 text-lg font-semibold text-gray-900">
                モバイル対応
              </h3>
            </div>
            <p className="text-gray-600 text-sm sm:text-base">
              スマートフォン・タブレットで完全動作。
              外出先でも音声録音やファイルアップロードが可能。
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center mb-4">
              <div className="bg-yellow-100 p-3 rounded-full">
                <span className="text-2xl">🎭</span>
              </div>
              <h3 className="ml-3 text-lg font-semibold text-gray-900">
                多様な顧客タイプ
              </h3>
            </div>
            <p className="text-gray-600 text-sm sm:text-base">
              分析型、結果重視型、表現重視型など、
              6種類の顧客タイプに対応したトレーニング。
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center mb-4">
              <div className="bg-red-100 p-3 rounded-full">
                <span className="text-2xl">🔄</span>
              </div>
              <h3 className="ml-3 text-lg font-semibold text-gray-900">
                Obsidian連携
              </h3>
            </div>
            <p className="text-gray-600 text-sm sm:text-base">
              音声・画像・文書を自動でObsidianに保存。
              個人ナレッジとAIシステムの完全連携。
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center mb-4">
              <div className="bg-indigo-100 p-3 rounded-full">
                <span className="text-2xl">📈</span>
              </div>
              <h3 className="ml-3 text-lg font-semibold text-gray-900">
                継続的改善
              </h3>
            </div>
            <p className="text-gray-600 text-sm sm:text-base">
              セッション履歴の保存、進捗の可視化、
              個別の改善提案で着実にスキル向上。
            </p>
          </div>
        </div>

        {/* CTA Section */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-6 sm:p-8 text-center">
          <h3 className="text-xl sm:text-2xl font-bold text-white mb-4">
            営業力を次のレベルに！
          </h3>
          <p className="text-blue-100 text-base sm:text-lg mb-6">
            AIを活用した実践的トレーニングで、確実に営業スキルを向上させましょう。
            スマホでもPCでも、いつでもどこでも利用可能！
          </p>
          <div className="flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-4">
            <Link
              href="/roleplay"
              className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium 
              rounded-md text-blue-600 bg-white hover:bg-gray-50 transition-colors"
            >
              🚀 無料で始める
            </Link>
            <Link
              href="/file-upload"
              className="inline-flex items-center justify-center px-6 py-3 border border-white text-base font-medium 
              rounded-md text-white hover:bg-white hover:text-blue-600 transition-colors"
            >
              💡 ファイル連携を試す
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-6 sm:py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <p className="text-gray-400 text-sm sm:text-base">
              © 2024 Voice Roleplay System.
              営業スキル向上のためのAIトレーニングプラットフォーム
            </p>
            <div className="mt-4 flex flex-wrap justify-center space-x-4 sm:space-x-6">
              <span className="text-gray-400 text-xs sm:text-sm">
                🎯 実践的トレーニング
              </span>
              <span className="text-gray-400 text-xs sm:text-sm">🤖 AI分析</span>
              <span className="text-gray-400 text-xs sm:text-sm">📱 モバイル対応</span>
              <span className="text-gray-400 text-xs sm:text-sm">�� Obsidian連携</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
