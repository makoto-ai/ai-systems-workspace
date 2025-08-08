// Vercel Functions: AIチャットAPI（Groq使用）
import Groq from 'groq-sdk';

const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY,
});

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', ['POST']);
    return res.status(405).end(`Method ${req.method} Not Allowed`);
  }

  try {
    const { 
      messages, 
      customerType = 'ANALYTICAL',
      sessionType = 'roleplay',
      temperature = 0.7 
    } = req.body;

    if (!messages || !Array.isArray(messages)) {
      return res.status(400).json({ 
        error: 'Invalid messages format',
        message: 'メッセージ形式が正しくありません'
      });
    }

    // 顧客タイプ別のシステムプロンプト
    const customerTypePrompts = {
      ANALYTICAL: "あなたは分析型の顧客です。詳細な情報、データ、根拠を重視します。論理的で慎重な判断を行います。",
      DRIVER: "あなたは結果重視型の顧客です。迅速な決断、効率性、ROIを重視します。時間を無駄にすることを嫌います。",
      EXPRESSIVE: "あなたは表現豊かな顧客です。人間関係、感情、体験を重視します。エネルギッシュで社交的です。",
      AMIABLE: "あなたは協調型の顧客です。安定性、関係性、信頼を重視します。慎重で人当たりが良いです。",
      SKEPTICAL: "あなたは懐疑的な顧客です。警戒心が強く、証明を求めます。簡単には信用しません。",
      ENTHUSIASTIC: "あなたは熱心な顧客です。新しいアイデアに興味を持ち、積極的に質問します。"
    };

    const systemPrompt = sessionType === 'roleplay' 
      ? `${customerTypePrompts[customerType]} 営業担当者との対話において、このキャラクターを一貫して演じてください。日本語で自然に応答してください。`
      : "あなたは営業コーチです。建設的なフィードバックと改善提案を提供してください。";

    const completion = await groq.chat.completions.create({
      messages: [
        { role: 'system', content: systemPrompt },
        ...messages
      ],
      model: 'llama-3.1-70b-versatile',
      temperature: temperature,
      max_tokens: 1000,
      top_p: 1,
      stream: false,
    });

    res.status(200).json({
      success: true,
      message: completion.choices[0]?.message?.content || '',
      customerType,
      sessionType,
      timestamp: new Date().toISOString(),
      service: 'Groq LLaMA',
    });

  } catch (error) {
    console.error('Chat completion error:', error);
    res.status(500).json({
      error: 'Chat completion failed',
      message: 'AI応答の生成に失敗しました',
      details: error.message,
    });
  }
}
