import pytest

@pytest.mark.xfail(reason="実行ランナー未実装：run_analysis(audio_wav) が必要")
def test_contract_runtime_example():
    from app.analysis_runner import run_analysis  # TODO: 後で実装
    out = run_analysis("tests/fixtures/hello_short.wav")
    assert len(out["summary"]) <= 600
    assert len(out["positives"]) >= 1
    assert len(out["improvements"]) >= 1


