#!/usr/bin/env python3
"""
Obsidian保存コマンドデモ
「〇〇をobsidianに保存して」コマンドの実例
"""

from obsidian_flexible_saver import ObsidianFlexibleSaver

def save_command_demo():
    """保存コマンドのデモ実行"""
    
    saver = ObsidianFlexibleSaver()
    
    print("🎯 「〇〇をobsidianに保存して」コマンドデモ")
    print("=" * 50)
    
    # 例1: 重要な気づき
    insight = """
今日の開発で学んだ最重要ポイント：

1. **エラーメッセージの表面に惑わされるな**
   - 「音声合成処理中にエラー」→ 実際はHTTPヘッダー問題
   - ログをしっかり読めば真の原因が分かる

2. **既存の動作するコードとの差分比較が最強**
   - 営業APIと既存APIの違いを比較
   - VoiceService()の呼び出し方の違いを発見

3. **選択肢の絞り込みが実用性を飛躍的に向上させる**
   - 99種類→10種類で営業効率化
   - 過剰な選択肢は使いにくさを生む
    """
    
    file1 = saver.save_custom_content(
        content=insight,
        title="今日の重要な気づき：開発の極意",
        category="learning-notes",
        tags=["重要発見", "開発ノウハウ", "問題解決"]
    )
    
    # 例2: コードスニペット  
    code_snippet = """
# 営業特化スピーカー自動選択の核心コード
def get_speaker_by_scenario(scenario: str, gender: str = "random"):
    if scenario not in SALES_SCENARIOS:
        return None
    
    scenario_config = SALES_SCENARIOS[scenario]
    
    if gender == "male":
        speaker_key = scenario_config["male_speaker"]
        return SALES_SPEAKERS["male_speakers"][speaker_key]
    elif gender == "female":
        speaker_key = scenario_config["female_speaker"] 
        return SALES_SPEAKERS["female_speakers"][speaker_key]
    else:
        # ランダム選択
        import random
        gender_choice = random.choice(["male", "female"])
        return get_speaker_by_scenario(scenario, gender_choice)
    """
    
    file2 = saver.save_code_snippet(
        code=code_snippet,
        description="営業シナリオ別スピーカー自動選択システム",
        language="python"
    )
    
    # 例3: プロジェクトアイデア
    idea = """
## 🚀 次世代音声AIシステムのアイデア

### 💡 コンセプト
個人の声をクローニングして、自分自身との営業ロールプレイを可能にする

### 🎯 価値提案
1. **究極のセルフトレーニング**: 自分の声で顧客役を演じる
2. **完全プライベート練習**: 他人に聞かれる心配なし
3. **リアルな自己対話**: 自分の話し方の癖を客観視

### 🔧 技術実装
- Coqui TTSでの音声クローニング
- 10-15分の音声サンプルで高品質再現
- 既存VOICEVOXシステムとの並行運用

### 📈 ビジネス価値
営業スキル向上の完全プライベート化により、
恥ずかしがり屋の営業パーソンも安心して練習可能
    """
    
    file3 = saver.save_custom_content(
        content=idea,
        title="次世代音声AI：セルフクローニングシステム",
        category="project-ideas", 
        tags=["次世代", "音声クローニング", "プライベート練習", "革新的"]
    )
    
    print(f"\n🎉 保存コマンドデモ完了！")
    print(f"📄 気づき保存: {file1.name}")
    print(f"💻 コード保存: {file2.name}")
    print(f"💡 アイデア保存: {file3.name}")
    
    print(f"\n✨ これで何でもObsidianに保存できます！")

if __name__ == "__main__":
    save_command_demo()