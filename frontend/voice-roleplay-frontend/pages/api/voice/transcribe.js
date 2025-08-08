// Vercel Functions: 音声文字起こしAPI（Groq Whisper使用）
import Groq from 'groq-sdk';
import formidable from 'formidable';
import fs from 'fs';

export const config = {
  api: {
    bodyParser: false,
  },
};

const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY,
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
    const audioFile = Array.isArray(files.audio) ? files.audio[0] : files.audio;

    if (!audioFile) {
      return res.status(400).json({ 
        error: 'No audio file provided',
        message: '音声ファイルが見つかりません'
      });
    }

    // Groq Whisperで文字起こし
    const transcription = await groq.audio.transcriptions.create({
      file: fs.createReadStream(audioFile.filepath),
      model: 'whisper-large-v3',
      language: 'ja',
      response_format: 'json',
    });

    // 一時ファイル削除
    fs.unlinkSync(audioFile.filepath);

    res.status(200).json({
      success: true,
      transcription: transcription.text,
      timestamp: new Date().toISOString(),
      service: 'Groq Whisper',
    });

  } catch (error) {
    console.error('Transcription error:', error);
    res.status(500).json({
      error: 'Transcription failed',
      message: '音声文字起こしに失敗しました',
      details: error.message,
    });
  }
}
