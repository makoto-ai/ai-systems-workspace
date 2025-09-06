import yaml
from pathlib import Path

def test_spec_file_exists():
    assert Path("specs/speech_analysis_v1.yaml").is_file()

def test_spec_minimal_schema():
    data = yaml.safe_load(Path("specs/speech_analysis_v1.yaml").read_text(encoding="utf-8"))
    # 主要キーの存在
    for key in ["id","purpose","inputs","process","outputs","non_functional","acceptance_tests","versioning"]:
        assert key in data, f"missing key: {key}"
    # 出力仕様の最低限の契約
    out = data["outputs"]
    for k in ["summary","positives","improvements","next_practice"]:
        assert k in out, f"missing outputs.{k}"


