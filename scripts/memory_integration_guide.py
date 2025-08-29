#!/usr/bin/env python3
"""
🔧 記憶システム統合ガイド - AIアシスタント連携用
このスクリプトは、AIアシスタントが最初の応答で呼び出すためのガイドです
"""

from auto_memory_loader import auto_load_memory, should_auto_load, get_memory_context


def integrate_memory_with_response(user_query: str) -> tuple[str, str]:
    """
    ユーザーの質問と記憶システムを統合

    Returns:
        tuple: (memory_context, integrated_response_prefix)
    """

    # 新セッションの場合は完全な記憶復元
    if should_auto_load():
        memory_context = auto_load_memory()
        integrated_prefix = f"""
{memory_context}

---

**🎯 ご質問への回答**: 上記の文脈を踏まえて、「{user_query}」についてお答えいたします。

"""
        return memory_context, integrated_prefix

    # 既存セッションの場合は軽量な文脈表示
    else:
        memory_summary = get_memory_context()
        if memory_summary:
            integrated_prefix = f"""
{memory_summary}

**🎯 ご質問への回答**: 「{user_query}」についてお答えいたします。

"""
            return memory_summary, integrated_prefix
        else:
            return "", ""


def generate_usage_instructions():
    """使用方法の指示を生成"""

    return """
# 🧠 自動記憶復元システム使用方法

## AIアシスタント側の実装

```python
# 1. 最初の応答で必ず実行
from scripts.memory_integration_guide import integrate_memory_with_response

def respond_to_user(user_query: str):
    # 記憶システムと統合
    memory_context, response_prefix = integrate_memory_with_response(user_query)
    
    # 通常の応答処理
    normal_response = process_user_query(user_query)
    
    # 統合された応答
    final_response = response_prefix + normal_response
    
    return final_response
```

## 動作例

### ユーザー: "今日の天気は？"
### AI応答:
```
🧠 **記憶システム自動復元完了**

[前回の文脈情報が自動表示]

---
✅ **自動復元システム動作**: この文脈情報を踏まえて、ご質問にお答えいたします。

**🎯 ご質問への回答**: 「今日の天気は？」についてお答えいたします。

申し訳ございませんが、私はリアルタイムの天気情報にアクセスできません...
```

## 利点
- ユーザーがどんな質問をしても自動で記憶復元
- 関係のない質問でも前回の作業文脈が継続
- 完全に透明で自然な動作
"""


if __name__ == "__main__":
    print(generate_usage_instructions())
