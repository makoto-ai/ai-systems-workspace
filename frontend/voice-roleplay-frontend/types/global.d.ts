/// <reference types="next" />
/// <reference types="next/image-types/global" />

// React 19 + Next.js 15 型定義
declare module 'react' {
  interface HTMLAttributes<T> extends AriaAttributes, DOMAttributes<T> {
    suppressHydrationWarning?: boolean;
  }
}

// Next.js環境変数
declare namespace NodeJS {
  interface ProcessEnv {
    NEXT_PUBLIC_API_URL?: string;
    NODE_ENV: 'development' | 'production' | 'test';
  }
}

// JSX型定義の拡張
declare global {
  namespace JSX {
    interface IntrinsicElements {
      [elemName: string]: any;
    }
  }
}

export {}; 