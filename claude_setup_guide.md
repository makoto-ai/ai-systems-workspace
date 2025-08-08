# 🤖 Claude API 設定ガイド

## 🚨 **現在の状況**
Claude APIはクレジット不足のため一時的に利用不可

## ⚡ **即座に解決する方法**

### **1. 既存アカウントにクレジット追加**
```bash
# 1. Anthropic Console にアクセス
open https://console.anthropic.com/

# 2. Settings → Billing
# 3. "Add Credits" で最小$5追加
```

### **2. 新規アカウントで無料クレジット取得**
```bash
# 1. 新しいアカウント作成
open https://console.anthropic.com/signup

# 2. 新しいAPIキー生成
# 3. 環境変数更新
export CLAUDE_API_KEY="sk-ant-api03-新しいキー..."
```

### **3. 現在のAPIキー確認**
```bash
echo $CLAUDE_API_KEY | head -c 25
# 出力: sk-ant-api03-hHwGpp8k5...
```

## 🔧 **設定確認方法**

### **Claude 単体テスト**
```bash
source venv/bin/activate
python -c "
from app.services.ai_service import ClaudeAIService
import asyncio

async def test():
    claude = ClaudeAIService()
    result = await claude.chat_completion('Hello Claude!', max_tokens=10)
    print('✅ Claude復旧成功:', result['response'])

asyncio.run(test())
"
```

### **システム全体テスト**
```bash
python -m pytest tests/api/test_health.py -v
```

## 💰 **コスト最適化**

### **無料枠を最大活用**
- **Groq**: 完全無料 (Llama 3.3 70B)
- **OpenAI**: $5 無料クレジット
- **Claude**: $5 無料クレジット
- **Gemini**: 無料枠あり

### **推奨設定**
```python
# 優先順位 (コスト重視)
1. Groq (無料)
2. Gemini (無料枠)  
3. OpenAI (無料クレジット)
4. Claude (無料クレジット)
```

## ✅ **復旧確認**
Claudeが復旧すると以下が表示されます：
```
✅ Claude test successful
INFO: Primary provider: groq
INFO: Fallback providers: ['openai', 'claude', 'gemini', 'simulation']
``` 