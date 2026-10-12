"""Safety decisions must come from engines, with no label leakage or fake timing."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from src import phase_c_guard as phase

pytestmark = pytest.mark.student


def test_pii_scope_ignores_english_ner_and_foreign_ids_but_keeps_email():
    text = "MFA v2024 public@example.com"
    rows = [SimpleNamespace(entity_type=kind, start=start, end=end, score=.9)
            for kind, start, end in [("ORGANIZATION", 0, 3), ("US_DRIVER_LICENSE", 4, 9),
                                     ("EMAIL_ADDRESS", 10, len(text))]]
    analyzer = SimpleNamespace(analyze=Mock(return_value=rows))
    anonymizer = SimpleNamespace(anonymize=Mock(return_value=SimpleNamespace(text="MFA v2024 <EMAIL_ADDRESS>")))
    result = phase.pii_scan(text, analyzer, anonymizer)
    assert [row["type"] for row in result["entities"]] == ["EMAIL_ADDRESS"]
    assert result["entities"][0]["text"] == "public@example.com"
    assert anonymizer.anonymize.call_args.kwargs["analyzer_results"] == [rows[-1]]
    analyzer.analyze.return_value = rows[:2]
    assert phase.pii_scan(text[:9], analyzer, anonymizer) == {
        "has_pii": False, "entities": [], "anonymized": text[:9]}


@pytest.mark.parametrize("log", [None, SimpleNamespace(activated_rails=[]),
    SimpleNamespace(activated_rails=[SimpleNamespace(stop=None)])])
def test_missing_decision_cannot_allow_input(log):
    rails = SimpleNamespace(generate_async=AsyncMock(return_value=SimpleNamespace(
        response=[{"content": "looks safe"}], log=log)))
    with pytest.raises(ValueError):
        asyncio.run(phase.check_input_rail("policy question", rails))


def test_safe_output_is_preserved_even_when_rail_rephrases_it():
    original = "Xin lỗi, tôi không thể đi làm; hãy gửi đơn nghỉ phép."
    rails = SimpleNamespace(generate_async=AsyncMock(return_value=SimpleNamespace(
        response=[{"content": "different text"}],
        log=SimpleNamespace(activated_rails=[SimpleNamespace(stop=False)]))))
    result = asyncio.run(phase.check_output_rail("leave?", original, rails))
    assert result == {"safe": True, "flagged_reason": None, "final_answer": original}


@pytest.mark.parametrize("replacement", ["", "unsafe original"])
def test_blocked_output_must_have_a_replacement(replacement):
    rails = SimpleNamespace(generate_async=AsyncMock(return_value=SimpleNamespace(
        response=[{"content": replacement}],
        log=SimpleNamespace(activated_rails=[SimpleNamespace(stop=True)]))))
    with pytest.raises(ValueError, match="replacement"):
        asyncio.run(phase.check_output_rail("question", "unsafe original", rails))


def test_expected_does_not_drive_decisions(monkeypatch):
    pii = Mock(return_value={"has_pii": False})
    rail = AsyncMock(return_value={"allowed": True})
    monkeypatch.setattr(phase, "pii_scan", pii)
    monkeypatch.setattr(phase, "check_input_rail", rail)
    source = [{"id": 1, "category": "arbitrary", "input": "same text", "expected": "blocked"},
              {"id": 2, "category": "arbitrary", "input": "same text", "expected": "allowed"}]
    rows = phase.run_adversarial_suite(source, object(), object(), object())
    assert [row["actual"] for row in rows] == ["allowed", "allowed"]
    assert [row["passed"] for row in rows] == [False, True]
    assert [call.args[0] for call in rail.await_args_list] == ["same text", "same text"]


def test_latency_measures_nemo_even_when_pii_blocks_in_one_loop(monkeypatch):
    loops = []
    pii = Mock(return_value={"has_pii": True})
    async def check(text, rails):
        loops.append(id(asyncio.get_running_loop()))
        return {"allowed": False}
    monkeypatch.setattr(phase, "pii_scan", pii)
    monkeypatch.setattr(phase, "check_input_rail", check)
    monkeypatch.setattr(phase.time, "perf_counter", Mock(side_effect=[i * .001 for i in range(12)]))
    result = phase.measure_p95_latency(["PII 034095001234"], 3, object(), object(), object())
    assert pii.call_count == len(loops) == 5  # two real warm-ups, three timed samples
    assert len(set(loops)) == 1
    assert result["n_samples"] == 3 and result["warmup_runs"] == 2
    assert result["input_guard_ms"]["p95"] == pytest.approx(2)


@pytest.mark.parametrize("texts,n", [([], 20), (["clean"], 0), (["clean"], True), ([""], 20)])
def test_invalid_latency_inputs_rejected_before_setup(monkeypatch, texts, n):
    setup = Mock()
    monkeypatch.setattr(phase, "setup_presidio", setup)
    with pytest.raises(ValueError):
        phase.measure_p95_latency(texts, n)
    setup.assert_not_called()
