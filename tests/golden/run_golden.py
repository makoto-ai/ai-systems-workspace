import json
import argparse
from pathlib import Path
from datetime import datetime
from evaluator import score
import re

def _sanitize_prediction(text: str) -> str:
    """応答をクリーンアップ（改行削除、余分なスペース削除）"""
    if not text:
        return ""
    # 改行やタブを削除、複数スペースを単一スペースに
    cleaned = re.sub(r'\s+', ' ', text.strip())
    return cleaned


# 実モデル呼び出しに差し替え（UnifiedAIService 経由）
def predict(text: str) -> str:
    try:
        try:
            from services.ai_service import get_unified_ai_service, AIProvider  # type: ignore
        except ImportError:
            from app.services.ai_service import get_unified_ai_service, AIProvider

        svc = get_unified_ai_service()

        # 低温度で決定性を高める
        # プライマリが落ちた場合は自動フォールバック
        import asyncio

        # 出力を空白区切りキーワード列にするようプロンプトを強制
        prompt = (
            "[SYSTEM] あなたはキーワード抽出器です。\n"
            "以下の厳密ルールに100%従ってください。違反は不可：\n"
            "- 出力は半角英数/日本語のみ（記号・句読点・絵文字・改行・タブ禁止）\n"
            "- 語の区切りは半角スペース1つのみ（複数スペース禁止）\n"
            "- 3〜5語、最大5語まで。説明・補足・助詞・接続詞は出力しない\n"
            "- 名詞/固有名詞中心。冗長表現は避け、見出し語で\n"
            "[INPUT]\n" + text + "\n"
            "[FORMAT_EXAMPLE]\n"
            "営業ロープレ 自動化 暴走防止 CI 整備\n"
            "[OUTPUT]\n"
        )
        result = asyncio.run(
            svc.chat_completion(
                prompt, max_tokens=60, temperature=0.0, provider=AIProvider.GROQ
            )
        )
        raw = (result or {}).get("response", "").strip()
        pred = _sanitize_prediction(raw)

        # フォーマット検証（半角英数/日本語・空白区切り・最大5語）
        ok = bool(re.fullmatch(r"[A-Za-z0-9ぁ-んァ-ン一-龥]+( [A-Za-z0-9ぁ-んァ-ン一-龥]+){0,4}", pred))
        if ok and pred:
            return pred

        # 1回だけ再試行（厳密指示）
        retry_prompt = (
            "先の出力は規則違反です。以下の厳密な出力ルールに従って再出力してください。\n"
            "[厳密ルール]\n"
            "- 半角英数/日本語のみ（記号・句読点・絵文字・改行禁止）\n"
            "- 語の区切りは半角スペース1つのみ\n"
            "- 最大5語。説明や補足は禁止\n"
            "[入力]\n" + text + "\n"
            "[出力例]\n"
            "営業ロープレ 自動化 暴走防止 CI 整備\n"
            "[出力]\n"
        )
        result2 = asyncio.run(
            svc.chat_completion(
                retry_prompt, max_tokens=50, temperature=0.0, provider=AIProvider.GROQ
            )
        )
        raw2 = (result2 or {}).get("response", "").strip()
        pred2 = _sanitize_prediction(raw2)
        return pred2
    except Exception as e:
        # 失敗時は空文字（評価で0点）を返す。詳細は上位でログ化。
        return ""


def load_config():
    """設定ファイルから設定を読み込み"""
    import yaml
    config_path = Path(__file__).parent / "config.yml"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception:
            pass
    return {"threshold": 0.3}  # デフォルト

def main():
    parser = argparse.ArgumentParser()
    
    # 設定ファイルからデフォルト値を取得
    config = load_config()
    default_threshold = config.get("threshold", 0.3)
    
    parser.add_argument("--threshold", type=float, default=default_threshold)
    args = parser.parse_args()

    cases_dir = Path(__file__).parent / "cases"
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"

    passed = 0
    total = 0

    with log_path.open("a", encoding="utf-8") as out:
        for p in sorted(cases_dir.glob("*.json")):
            data = json.loads(p.read_text(encoding="utf-8"))
            cid = data.get("id")
            ref = data.get("reference", "")
            pred = predict(data.get("input", ""))
            s = score(ref, pred)
            ok = s >= args.threshold
            rec = {
                "id": cid,
                "score": s,
                "passed": ok,
                "reference": ref,
                "prediction": pred,
                "threshold": args.threshold,
                "input": data.get("input", ""),
            }
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            total += 1
            if ok:
                passed += 1

    print(f"passed {passed}/{total} (threshold={args.threshold})")
    print(f"log: {log_path}")

if __name__ == "__main__":
    main()
