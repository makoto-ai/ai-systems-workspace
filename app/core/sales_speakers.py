# 営業ロールプレイ特化スピーカー設定
# 99種類から厳選した営業シーンに最適な10名

SALES_SPEAKERS = {
    # 男性営業相手役
    "male_speakers": {
        "decision_maker": {
            "id": 1,
            "name": "玄野武宏 (ノーマル)",
            "character": "中年決裁者",
            "scenario": "最終決定権を持つ落ち着いた判断者",
            "best_use": "重要な商談、最終プレゼン",
        },
        "young_manager": {
            "id": 2,
            "name": "青山龍星 (ノーマル)",
            "character": "若手マネージャー",
            "scenario": "エネルギッシュで質問が多い担当者",
            "best_use": "新規開拓、詳細説明が必要な商談",
        },
        "cautious_staff": {
            "id": 3,
            "name": "白上虎太郎 (ふつう)",
            "character": "慎重な担当者",
            "scenario": "リスクを重視し慎重に検討する",
            "best_use": "リスク説明、安全性アピール",
        },
        "difficult_customer": {
            "id": 82,
            "name": "青山龍星 (不機嫌)",
            "character": "厳しい顧客",
            "scenario": "批判的で要求の高い相手",
            "best_use": "反対意見処理、プレッシャー下での対応練習",
        },
        "positive_decision_maker": {
            "id": 39,
            "name": "玄野武宏 (喜び)",
            "character": "好意的な決裁者",
            "scenario": "前向きで決断が早い決裁者",
            "best_use": "クロージング練習、成功パターン体験",
        },
    },
    # 女性営業相手役
    "female_speakers": {
        "professional_woman": {
            "id": 7,
            "name": "春日部つむぎ (ノーマル)",
            "character": "プロフェッショナル女性",
            "scenario": "知的でロジカルな判断をする女性管理職",
            "best_use": "データ重視の提案、論理的説明",
        },
        "gentle_staff": {
            "id": 0,
            "name": "四国めたん (あまあま)",
            "character": "優しい担当者",
            "scenario": "親しみやすく話しやすい女性担当者",
            "best_use": "アイスブレイク、関係構築練習",
        },
        "senior_manager": {
            "id": 16,
            "name": "九州そら (ノーマル)",
            "character": "中堅女性管理職",
            "scenario": "経験豊富で的確な質問をする",
            "best_use": "複雑な商談、多角的な提案",
        },
        "careful_customer": {
            "id": 36,
            "name": "四国めたん (ささやき)",
            "character": "慎重な女性顧客",
            "scenario": "小声で不安や懸念を相談する",
            "best_use": "不安解消、信頼関係構築",
        },
        "skeptical_decision_maker": {
            "id": 18,
            "name": "九州そら (ツンツン)",
            "character": "警戒心の強い女性決裁者",
            "scenario": "簡単には納得しない厳しい決裁者",
            "best_use": "説得力強化、粘り強い対応練習",
        },
    },
}

# 営業シナリオ別推奨ペアリング
SALES_SCENARIOS = {
    "new_business": {
        "name": "新規開拓",
        "male_speaker": "decision_maker",
        "female_speaker": "professional_woman",
        "difficulty": "medium",
        "focus": "初回提案、関係構築",
    },
    "existing_customer": {
        "name": "既存顧客",
        "male_speaker": "young_manager",
        "female_speaker": "gentle_staff",
        "difficulty": "easy",
        "focus": "追加提案、アップセル",
    },
    "difficult_negotiation": {
        "name": "厳しい商談",
        "male_speaker": "difficult_customer",
        "female_speaker": "skeptical_decision_maker",
        "difficulty": "hard",
        "focus": "反対意見処理、プレッシャー対応",
    },
    "closing": {
        "name": "クロージング",
        "male_speaker": "positive_decision_maker",
        "female_speaker": "senior_manager",
        "difficulty": "medium",
        "focus": "最終決断促進、条件調整",
    },
    "consultation": {
        "name": "慎重な検討",
        "male_speaker": "cautious_staff",
        "female_speaker": "careful_customer",
        "difficulty": "medium",
        "focus": "不安解消、信頼構築",
    },
}


def get_sales_speaker_list():
    """営業特化スピーカー一覧を取得"""
    speakers = []

    for category in SALES_SPEAKERS.values():
        for speaker_data in category.values():
            speakers.append(
                {
                    "id": speaker_data["id"],
                    "name": speaker_data["name"],
                    "character": speaker_data["character"],
                    "scenario": speaker_data["scenario"],
                    "best_use": speaker_data["best_use"],
                }
            )

    return speakers


def get_speaker_by_scenario(scenario_name: str, gender: str = "random"):
    """シナリオ別推奨スピーカーを取得"""
    if scenario_name not in SALES_SCENARIOS:
        return None

    scenario = SALES_SCENARIOS[scenario_name]

    if gender == "male":
        speaker_key = scenario["male_speaker"]
        return SALES_SPEAKERS["male_speakers"][speaker_key]
    elif gender == "female":
        speaker_key = scenario["female_speaker"]
        return SALES_SPEAKERS["female_speakers"][speaker_key]
    else:
        # ランダムに男女選択
        import random

        gender_choice = random.choice(["male", "female"])
        if gender_choice == "male":
            speaker_key = scenario["male_speaker"]
            return SALES_SPEAKERS["male_speakers"][speaker_key]
        else:
            speaker_key = scenario["female_speaker"]
            return SALES_SPEAKERS["female_speakers"][speaker_key]


def get_all_scenarios():
    """利用可能な営業シナリオ一覧を取得"""
    return SALES_SCENARIOS
