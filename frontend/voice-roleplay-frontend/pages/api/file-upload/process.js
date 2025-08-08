// Vercel Functions: ファイルアップロード・処理API
import Groq from 'groq-sdk';
import formidable from 'formidable';
import fs from 'fs';
import OpenAI from 'openai';

export const config = {
  api: {
    bodyParser: false,
  },
};

const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY,
});

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', ['POST']);
    return res.status(405).end(`Method ${req.method} Not Allowed`);
  }

  try {
    const form = formidable({
      maxFileSize: 25 * 1024 * 1024, // 25MB
      keepExtensions: true,
    });

    const [fields, files] = await form.parse(req);
    const uploadedFile = Array.isArray(files.file) ? files.file[0] : files.file;

    if (!uploadedFile) {
      return res.status(400).json({ 
        error: 'No file provided',
        message: 'ファイルが見つかりません'
      });
    }

    const fileName = uploadedFile.originalFilename || 'unknown';
    const fileExtension = fileName.split('.').pop()?.toLowerCase();
    
    let processedContent = '';
    let analysisResult = null;

    // ファイルタイプ別処理
    if (['wav', 'mp3', 'm4a', 'webm', 'flac'].includes(fileExtension)) {
      // 音声ファイル: Whisperで文字起こし
      const transcription = await groq.audio.transcriptions.create({
        file: fs.createReadStream(uploadedFile.filepath),
        model: 'whisper-large-v3',
        language: 'ja',
        response_format: 'json',
      });
      
      processedContent = transcription.text;
      
      // AI分析
      const analysisResponse = await groq.chat.completions.create({
        messages: [
          {
            role: 'system',
            content: '音声の内容を分析し、重要なポイント、感情、トーン、改善提案をMarkdown形式で整理してください。'
          },
          {
            role: 'user',
            content: `以下の音声内容を分析してください：\n\n${processedContent}`
          }
        ],
        model: 'llama-3.1-70b-versatile',
        temperature: 0.3,
        max_tokens: 1000,
      });
      
      analysisResult = analysisResponse.choices[0]?.message?.content || '';
      
    } else if (['jpg', 'jpeg', 'png', 'gif', 'bmp'].includes(fileExtension)) {
      // 画像ファイル: GPT-4 Visionで分析
      const imageBase64 = fs.readFileSync(uploadedFile.filepath, { encoding: 'base64' });
      
      const visionResponse = await openai.chat.completions.create({
        model: 'gpt-4-vision-preview',
        messages: [
          {
            role: 'user',
            content: [
              {
                type: 'text',
                text: 'この画像を詳細に分析し、内容、重要な要素、ビジネス的な観点での活用方法をMarkdown形式で説明してください。'
              },
              {
                type: 'image_url',
                image_url: {
                  url: `data:image/${fileExtension};base64,${imageBase64}`
                }
              }
            ]
          }
        ],
        max_tokens: 1000,
      });
      
      processedContent = visionResponse.choices[0]?.message?.content || '画像の内容を分析しました。';
      analysisResult = processedContent;
      
    } else {
      // その他のファイル（テキスト系）
      const fileContent = fs.readFileSync(uploadedFile.filepath, 'utf-8');
      processedContent = fileContent.substring(0, 5000); // 最初の5000文字
      
      // AI要約
      const summaryResponse = await groq.chat.completions.create({
        messages: [
          {
            role: 'system',
            content: 'テキストを要約し、重要なポイントを抽出してMarkdown形式で整理してください。'
          },
          {
            role: 'user',
            content: `以下のテキストを要約してください：\n\n${processedContent}`
          }
        ],
        model: 'llama-3.1-70b-versatile',
        temperature: 0.3,
        max_tokens: 1000,
      });
      
      analysisResult = summaryResponse.choices[0]?.message?.content || '';
    }

    // 一時ファイル削除
    fs.unlinkSync(uploadedFile.filepath);

    // Obsidian用Markdownファイル作成
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const obsidianFileName = `${fileName.split('.')[0]}-${timestamp}.md`;
    
    const markdownContent = `# ${fileName}

## ファイル情報
- **ファイル名**: ${fileName}
- **タイプ**: ${fileExtension?.toUpperCase()}
- **処理日時**: ${new Date().toLocaleString('ja-JP')}
- **サイズ**: ${(uploadedFile.size / 1024).toFixed(2)} KB

## 処理結果

${processedContent}

## AI分析

${analysisResult}

---
*Voice Roleplay System により自動処理*
`;

    res.status(200).json({
      success: true,
      message: 'ファイル処理が完了しました',
      fileName: obsidianFileName,
      content: processedContent,
      analysis: analysisResult,
      markdownContent: markdownContent,
      timestamp: new Date().toISOString(),
      fileType: fileExtension,
    });

  } catch (error) {
    console.error('File processing error:', error);
    res.status(500).json({
      error: 'File processing failed',
      message: 'ファイル処理に失敗しました',
      details: error.message,
    });
  }
}
