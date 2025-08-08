/** @type {import('next').NextConfig} */
const nextConfig = {
  // Vercel最適化設定
  output: 'standalone',
  poweredByHeader: false,
  compress: true,
  
  // React 18 + Next.js 14用の最適化設定
  swcMinify: true,
  
  // 画像最適化（Vercel CDN対応）
  images: {
    domains: ['localhost', 'voice-roleplay-system.vercel.app'],
    formats: ['image/webp', 'image/avif'],
  },
  
  // webpack設定の最適化
  webpack: (config, { isServer }) => {
    // クライアントサイドのポリフィル設定
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false,
      };
    }
    
    // 音声処理の最適化
    config.module.rules.push({
      test: /\.(mp3|wav|ogg|m4a|webm)$/,
      type: 'asset/resource',
    });
    
    return config;
  },
  
  // 開発時の最適化
  experimental: {
    optimizePackageImports: ['lucide-react'],
    turbo: {
      rules: {
        '*.svg': {
          loaders: ['@svgr/webpack'],
          as: '*.js',
        },
      },
    },
  },
  
  // 環境変数の公開設定
  env: {
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  
  // Vercel Functions対応
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: '/api/:path*',
      },
    ];
  },
  
  // セキュリティヘッダー
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
