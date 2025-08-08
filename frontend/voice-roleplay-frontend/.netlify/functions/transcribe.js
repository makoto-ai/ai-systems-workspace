// Netlify Functions: 音声文字起こしAPI
const Groq = require('groq-sdk');

const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY,
});

exports.handler = async (event, context) => {
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({
        error: 'Method not allowed',
        message: 'このエンドポイントはPOSTメソッドのみサポートしています'
      })
    }
  }

  try {
    // Base64デコードされた音声データを処理
    const { audio_data, filename } = JSON.parse(event.body);
    
    if (!audio_data) {
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
        body: JSON.stringify({
          error: 'No audio data provided',
          message: '音声データが見つかりません'
        })
      }
    }

    // 簡単な応答（実際のGroq呼び出しはクライアント側で行う）
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({
        success: true,
        message: 'Netlify Functions で音声処理準備完了',
        timestamp: new Date().toISOString(),
        service: 'Netlify + Groq',
        note: 'クライアントサイドでGroq呼び出しを実行します'
      })
    }

  } catch (error) {
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({
        error: 'Processing failed',
        message: '音声処理に失敗しました',
        details: error.message,
      })
    }
  }
}
