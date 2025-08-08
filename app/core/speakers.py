from typing import Dict, Any

# 話者ID定数
MALE_MANAGER = 1
MALE_SALES = 2
MALE_CONSULTANT = 3
MALE_STAFF = 4
FEMALE_MANAGER = 5
FEMALE_SALES = 6
FEMALE_SUPPORT = 7
FEMALE_STAFF = 8

# 話者情報の定義
SPEAKER_INFO = {
    MALE_MANAGER: ("シニアマネージャー", "落ち着いた声のベテラン管理職"),
    MALE_SALES: ("営業担当", "爽やかな声の営業マン"),
    MALE_CONSULTANT: ("コンサルタント", "知的な印象のビジネスコンサルタント"),
    MALE_STAFF: ("若手社員", "元気で真面目な若手社員"),
    FEMALE_MANAGER: ("女性マネージャー", "知的で落ち着いた女性管理職"),
    FEMALE_SALES: ("女性営業", "明るく親しみやすい女性営業"),
    FEMALE_SUPPORT: ("カスタマーサポート", "丁寧な対応のサポートスタッフ"),
    FEMALE_STAFF: ("女性新入社員", "元気で前向きな新入社員"),
}

# VOICEVOXの話者IDとパラメータのマッピング
VOICEVOX_SPEAKER_MAPPING = {
    MALE_MANAGER: {"speaker": 11, "style": 0},  # 玄野武宏（ノーマル）
    MALE_SALES: {"speaker": 13, "style": 0},    # 青山龍星（ノーマル）
    MALE_CONSULTANT: {"speaker": 12, "style": 0},  # 白上虎太郎（ふつう）
    MALE_STAFF: {"speaker": 3, "style": 0},    # ずんだもん（ノーマル）
    FEMALE_MANAGER: {"speaker": 16, "style": 0},  # 九州そら（ノーマル）
    FEMALE_SALES: {"speaker": 15, "style": 0},    # 九州そら（あまあま）
    FEMALE_SUPPORT: {"speaker": 8, "style": 0}, # 春日部つむぎ（ノーマル）
    FEMALE_STAFF: {"speaker": 2, "style": 0},   # 四国めたん（ノーマル）
}

def get_all_speakers() -> Dict[str, Dict[str, Any]]:
    """利用可能な話者の一覧を取得します"""
    return {
        SPEAKER_INFO[speaker_id][0]: {
            "id": speaker_id,
            "name": SPEAKER_INFO[speaker_id][0],
            "description": SPEAKER_INFO[speaker_id][1]
        }
        for speaker_id in SPEAKER_INFO.keys()
    }

def get_voicevox_params(business_speaker_id: int) -> Dict[str, int]:
    """ビジネス話者IDからVOICEVOXのパラメータを取得"""
    if business_speaker_id not in VOICEVOX_SPEAKER_MAPPING:
        raise ValueError(f"Invalid business speaker ID: {business_speaker_id}")
    return VOICEVOX_SPEAKER_MAPPING[business_speaker_id] 