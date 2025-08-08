/**
 * Privacy-Aware Context Dashboard
 * プライバシー保護文脈理解システムのダッシュボード
 */

import React, { useState, useEffect } from 'react';
import { Shield, Eye, Trash2, RefreshCw, AlertCircle, CheckCircle, Lock } from 'lucide-react';

// UI Components
const Card: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <div className={`bg-white shadow-lg rounded-lg ${className}`}>{children}</div>
);

const CardHeader: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="px-6 py-4 border-b border-gray-200">{children}</div>
);

const CardTitle: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <h3 className={`text-lg font-semibold text-gray-900 ${className}`}>{children}</h3>
);

const CardContent: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="px-6 py-4">{children}</div>
);

const Button: React.FC<{
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: 'default' | 'destructive' | 'outline';
  size?: 'default' | 'sm';
  className?: string;
}> = ({ children, onClick, disabled = false, variant = 'default', size = 'default', className = '' }) => {
  const baseStyles = 'inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
  const variants = {
    default: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    destructive: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
    outline: 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 focus:ring-blue-500'
  };
  const sizes = {
    default: 'px-4 py-2 text-sm',
    sm: 'px-3 py-1.5 text-xs'
  };
  
  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};

const Badge: React.FC<{
  children: React.ReactNode;
  variant?: 'default' | 'secondary' | 'outline';
  className?: string;
}> = ({ children, variant = 'default', className = '' }) => {
  const variants = {
    default: 'bg-blue-100 text-blue-800',
    secondary: 'bg-gray-100 text-gray-800',
    outline: 'border border-gray-300 text-gray-700'
  };
  
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${variants[variant]} ${className}`}>
      {children}
    </span>
  );
};

interface PrivacyMode {
  mode: 'strict' | 'standard' | 'research';
  description: string;
  features: string[];
}

interface SessionContext {
  session_id: string;
  duration_minutes: number;
  total_turns: number;
  main_topics: string[];
  current_topic: string;
  sales_momentum: string;
  average_engagement: number;
  identified_patterns: string[];
  next_best_actions: string[];
}

interface ContextSuggestion {
  suggestions: string[];
  current_topic: string;
  sales_momentum: string;
  confidence: number;
  context_available: boolean;
}

const PrivacyContextDashboard: React.FC = () => {
  const [sessionId, setSessionId] = useState<string>('');
  const [privacyMode, setPrivacyMode] = useState<'strict' | 'standard' | 'research'>('strict');
  const [sessionContext, setSessionContext] = useState<SessionContext | null>(null);
  const [suggestions, setSuggestions] = useState<ContextSuggestion | null>(null);
  const [currentInput, setCurrentInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [serviceInfo, setServiceInfo] = useState<any>(null); // eslint-disable-line @typescript-eslint/no-explicit-any

  const privacyModes: PrivacyMode[] = [
    {
      mode: 'strict',
      description: '最高レベルのプライバシー保護',
      features: [
        '個人情報完全除外',
        '音声データ非保存',
        '即座の匿名化',
        'セッション限定記憶'
      ]
    },
    {
      mode: 'standard',
      description: '標準的なプライバシー保護',
      features: [
        '匿名化された文脈情報',
        '2時間セッション保持',
        'パターン学習あり',
        '個人情報は非保存'
      ]
    },
    {
      mode: 'research',
      description: '研究目的（明示的同意）',
      features: [
        '高度なパターン学習',
        '4時間セッション保持',
        '完全匿名化維持',
        '個人情報は非保存'
      ]
    }
  ];

  useEffect(() => {
    fetchServiceInfo();
  }, []);

  const fetchServiceInfo = async () => {
    try {
      const response = await fetch('/api/context/service-info');
      const data = await response.json();
      if (data.success) {
        setServiceInfo(data.service_info);
      }
    } catch (error) {
      console.error('サービス情報取得エラー:', error);
    }
  };

  const initializeSession = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const formData = new FormData();
      formData.append('privacy_mode', privacyMode);
      
      const response = await fetch('/api/context/initialize-session', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      if (data.success) {
        setSessionId(data.session_id);
        setError('');
      } else {
        setError(data.detail || 'セッション初期化に失敗しました');
      }
    } catch (error) {
      setError('セッション初期化エラー: ' + error);
    } finally {
      setIsLoading(false);
    }
  };

  const getSessionSummary = async () => {
    if (!sessionId) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(`/api/context/session/${sessionId}/summary`);
      const data = await response.json();
      
      if (data.success && data.summary.success) {
        setSessionContext(data.summary.summary);
      } else {
        setError('セッションが見つかりません');
      }
    } catch (error) {
      setError('セッション情報取得エラー: ' + error);
    } finally {
      setIsLoading(false);
    }
  };

  const getContextualSuggestions = async () => {
    if (!sessionId || !currentInput) return;
    
    setIsLoading(true);
    try {
      const response = await fetch('/api/context/suggestions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          current_input: currentInput
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setSuggestions(data.suggestions);
      } else {
        setError('提案生成に失敗しました');
      }
    } catch (error) {
      setError('提案取得エラー: ' + error);
    } finally {
      setIsLoading(false);
    }
  };

  const cleanupSession = async () => {
    if (!sessionId) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(`/api/context/session/${sessionId}`, {
        method: 'DELETE'
      });
      
      const data = await response.json();
      
      if (data.success) {
        setSessionId('');
        setSessionContext(null);
        setSuggestions(null);
        setCurrentInput('');
      } else {
        setError('セッション削除に失敗しました');
      }
    } catch (error) {
      setError('セッション削除エラー: ' + error);
    } finally {
      setIsLoading(false);
    }
  };

  const getMomentumColor = (momentum: string) => {
    switch (momentum) {
      case 'accelerating': return 'bg-green-500';
      case 'positive': return 'bg-blue-500';
      case 'neutral': return 'bg-gray-500';
      case 'challenging': return 'bg-yellow-500';
      case 'declining': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getEngagementColor = (engagement: number) => {
    if (engagement > 0.7) return 'text-green-600';
    if (engagement > 0.5) return 'text-blue-600';
    if (engagement > 0.3) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Shield className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              プライバシー保護文脈理解システム
            </h1>
            <p className="text-gray-600">
              個人情報を保存せずに会話文脈を理解・強化
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Lock className="h-5 w-5 text-green-600" />
          <span className="text-sm text-green-600 font-medium">
            GDPR準拠・プライバシー保護
          </span>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center space-x-2">
          <AlertCircle className="h-5 w-5 text-red-500" />
          <span className="text-red-700">{error}</span>
        </div>
      )}

      {/* プライバシーモード選択 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Shield className="h-5 w-5" />
            <span>プライバシー保護レベル</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {privacyModes.map((mode) => (
              <div
                key={mode.mode}
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  privacyMode === mode.mode
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setPrivacyMode(mode.mode)}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold capitalize">{mode.mode}</h3>
                  {privacyMode === mode.mode && (
                    <CheckCircle className="h-5 w-5 text-blue-500" />
                  )}
                </div>
                <p className="text-sm text-gray-600 mb-3">{mode.description}</p>
                <ul className="text-xs text-gray-500 space-y-1">
                  {mode.features.map((feature, index) => (
                    <li key={index} className="flex items-center space-x-1">
                      <span className="w-1 h-1 bg-gray-400 rounded-full"></span>
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          
          <div className="mt-4 flex space-x-3">
            <Button
              onClick={initializeSession}
              disabled={isLoading}
              className="flex items-center space-x-2"
            >
              {isLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Shield className="h-4 w-4" />}
              <span>プライバシー保護セッション開始</span>
            </Button>
            
            {sessionId && (
              <Button
                variant="destructive"
                onClick={cleanupSession}
                disabled={isLoading}
                className="flex items-center space-x-2"
              >
                <Trash2 className="h-4 w-4" />
                <span>セッション削除</span>
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* セッション情報 */}
      {sessionId && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* セッション概要 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>セッション概要</span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={getSessionSummary}
                  disabled={isLoading}
                >
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">セッションID:</span>
                  <span className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">
                    {sessionId.slice(0, 8)}...
                  </span>
                </div>
                
                {sessionContext && (
                  <>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">継続時間:</span>
                      <span className="text-sm">{Math.round(sessionContext.duration_minutes)}分</span>
                    </div>
                    
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">会話ターン:</span>
                      <span className="text-sm">{sessionContext.total_turns}回</span>
                    </div>
                    
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">営業モメンタム:</span>
                      <Badge className={getMomentumColor(sessionContext.sales_momentum)}>
                        {sessionContext.sales_momentum}
                      </Badge>
                    </div>
                    
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">エンゲージメント:</span>
                      <span className={`text-sm font-medium ${getEngagementColor(sessionContext.average_engagement)}`}>
                        {Math.round(sessionContext.average_engagement * 100)}%
                      </span>
                    </div>
                    
                    {sessionContext.main_topics.length > 0 && (
                      <div>
                        <span className="text-sm text-gray-600">主要トピック:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {sessionContext.main_topics.map((topic, index) => (
                            <Badge key={index} variant="secondary" className="text-xs">
                              {topic}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 文脈提案 */}
          <Card>
            <CardHeader>
              <CardTitle>文脈ベース提案</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    placeholder="現在の入力内容を入力..."
                    value={currentInput}
                    onChange={(e) => setCurrentInput(e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <Button
                    size="sm"
                    onClick={getContextualSuggestions}
                    disabled={isLoading || !currentInput}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                </div>
                
                {suggestions && (
                  <div className="space-y-3">
                    {suggestions.current_topic && (
                      <div>
                        <span className="text-sm text-gray-600">現在のトピック:</span>
                        <Badge variant="outline" className="ml-2">
                          {suggestions.current_topic}
                        </Badge>
                      </div>
                    )}
                    
                    <div>
                      <span className="text-sm text-gray-600 block mb-2">提案されたアクション:</span>
                      <ul className="space-y-1">
                        {suggestions.suggestions.map((suggestion, index) => (
                          <li key={index} className="text-sm bg-blue-50 px-3 py-2 rounded border-l-4 border-blue-500">
                            {suggestion}
                          </li>
                        ))}
                      </ul>
                    </div>
                    
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>信頼度: {Math.round(suggestions.confidence * 100)}%</span>
                      <span>文脈利用可能: {suggestions.context_available ? 'はい' : 'いいえ'}</span>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* パターン分析と次のアクション */}
      {sessionContext && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>識別されたパターン</CardTitle>
            </CardHeader>
            <CardContent>
              {sessionContext.identified_patterns.length > 0 ? (
                <div className="space-y-2">
                  {sessionContext.identified_patterns.map((pattern, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span className="text-sm">{pattern}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">まだパターンが検出されていません</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>推奨される次のアクション</CardTitle>
            </CardHeader>
            <CardContent>
              {sessionContext.next_best_actions.length > 0 ? (
                <div className="space-y-2">
                  {sessionContext.next_best_actions.map((action, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span className="text-sm">{action}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">推奨アクションを分析中...</p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* プライバシー保証 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Lock className="h-5 w-5 text-green-600" />
            <span>プライバシー保証</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
              <p className="text-sm font-medium">個人情報非保存</p>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
              <p className="text-sm font-medium">音声データ非保存</p>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
              <p className="text-sm font-medium">自動匿名化</p>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
              <p className="text-sm font-medium">自動削除</p>
            </div>
          </div>
          
          {serviceInfo && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>サービス情報:</strong> アクティブセッション: {serviceInfo.active_sessions}、
                学習パターン: {serviceInfo.learned_patterns}、
                プライバシーモード: {serviceInfo.privacy_mode}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default PrivacyContextDashboard; 