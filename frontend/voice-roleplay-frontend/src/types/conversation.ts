export interface ConversationEntry {
  id: string;
  timestamp: Date;
  userInput: {
    text: string;
    audioURL?: string;
  };
  aiResponse: {
    text: string;
    audioURL?: string;
  };
  analysis: {
    intent: string;
    sentiment: string;
    buyingSignals: string[];
  };
  performance: {
    totalTime: number;
    transcriptionTime: number;
    analysisTime: number;
    synthesisTime: number;
  };
}

export interface ConversationSession {
  id: string;
  customerType: string;
  startTime: Date;
  endTime?: Date;
  isActive: boolean;
}

export interface ConversationPerformance {
  totalConversations: number;
  averageResponseTime: number;
  successRate: number;
}

export type ConversationStep =
  | 'idle'
  | 'transcribing'
  | 'analyzing'
  | 'synthesizing'
  | 'complete'
  | 'error';

export interface VoiceConversationState {
  isProcessing: boolean;
  currentStep: ConversationStep;
  history: ConversationEntry[];
  currentSession: ConversationSession | null;
  error: string | null;
  performance: ConversationPerformance;
}

export interface VoiceConversationControls {
  processVoiceInput: (audioBlob: Blob) => Promise<void>;
  startSession: (customerType: string) => void;
  endSession: () => void;
  clearHistory: () => void;
  playAudioResponse: (audioURL: string) => void;
  getSessionAnalysisReport: (sessionId: string, userId: string) => Promise<unknown>;
}
