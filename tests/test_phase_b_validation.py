"""Reject corrupt judge responses and undefined calibration without live calls."""
import json
from unittest.mock import Mock

import pytest

from src import phase_b_judge as phase

pytestmark = pytest.mark.student


@pytest.mark.parametrize("payload", [
    None, [], {"winner": "C"},
    {"winner": "A", "reasoning": "", "scores": {"A": .8, "B": .2}},
    {"winner": "A", "reasoning": "ok", "scores": {"A": .8}},
    *[{"winner": "A", "reasoning": "ok", "scores": {"A": value, "B": .2}}
      for value in (True, "0.8", -1, 1.1, float("nan"), float("inf"))],
])
def test_invalid_json_payload_fails(openai_client, payload):
    openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps(payload)
    with pytest.raises(ValueError):
        phase.pairwise_judge("question", "first", "second", "reference")


@pytest.mark.parametrize("content", [None, "not json", "```json\n{}\n```"])
def test_missing_or_malformed_json_fails(openai_client, content):
    openai_client.chat.completions.create.return_value.choices[0].message.content = content
    with pytest.raises(ValueError, match="valid JSON"):
        phase.pairwise_judge("question", "first", "second")


def test_reasoning_is_trimmed(openai_client):
    payload = {"winner": "A", "reasoning": "  supported by reference  ",
               "scores": {"A": .9, "B": .2}}
    openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps(payload)
    result = phase.pairwise_judge("question", "first", "second", "reference")
    assert result["reasoning"] == "supported by reference"


def test_bias_rejects_inconsistent_swap_consensus():
    row = phase.JudgeResult(
        "question", "first", "second", "A", "B", "A",
        "first pass", "second pass", False,
    )
    with pytest.raises(ValueError, match="inconsistent swap consensus"):
        phase.bias_report([row])


@pytest.mark.parametrize("judge,human", [([], []), ([0], [0, 1]), ([1], [1]),
                                        ([0], [0]), ([True], [0]), ([2], [0])])
def test_invalid_or_undefined_kappa_is_not_zero(judge, human):
    with pytest.raises(ValueError):
        phase.cohen_kappa(judge, human)


def test_two_ties_remain_consistent(monkeypatch):
    mocked = Mock(return_value={"winner": "tie", "reasoning": "equivalent",
                                "scores": {"A": .7, "B": .6}})
    monkeypatch.setattr(phase, "pairwise_judge", mocked)
    result = phase.swap_and_average("question", "first", "second", "reference")
    assert result.final_winner == "tie" and result.position_consistent
    assert result.scores_pass2 == {"A": .6, "B": .7}
    assert mocked.call_count == 2


def test_verbosity_uses_decisive_denominator_and_unicode_lengths():
    rows = [
        phase.JudgeResult("Q", "ngắn", "câu trả lời dài", "B", "B", "B", "r", "r", True),
        phase.JudgeResult("Q", "abcd", "efgh", "A", "A", "A", "r", "r", True),
        phase.JudgeResult("Q", "abcd", "efgh", "tie", "tie", "tie", "r", "r", True),
    ]
    report = phase.bias_report(rows)
    assert report["verbosity_bias"] == .5
    assert report["verbosity_details"] == {
        "a_wins_a_longer": 0, "b_wins_b_longer": 1, "total_decisive": 2}
