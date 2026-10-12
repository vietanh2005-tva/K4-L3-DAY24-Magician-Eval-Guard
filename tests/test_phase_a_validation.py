"""Offline regressions for evaluator integrity and Phase A analysis."""

from dataclasses import asdict
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src import phase_a_ragas as phase

pytestmark = pytest.mark.student


@pytest.fixture
def saved_answers():
    return [{**question, "answer": f"Pipeline answer {question['id']}",
             "contexts": [f"Retrieved evidence {question['id']}"],
             "generation_mode": "llm", "generation_model": "generator-test"}
            for question in phase.load_test_set_50q()]


@pytest.fixture
def evaluator(monkeypatch, saved_answers):
    rows = [{**{field: answer[field] for field in ("question", "answer", "contexts", "ground_truth")},
             **dict.fromkeys(phase.METRICS, .75)} for answer in saved_answers]
    raw = {"per_question": rows, "status": "ok",
           "metadata": {"evaluator_models": ["measured-llm", "measured-embedding"]}}
    evaluate = Mock(return_value=raw)
    monkeypatch.setitem(sys.modules, "src.m4_eval", SimpleNamespace(evaluate_ragas=evaluate))
    return raw, evaluate


def test_mapping_metrics_preserve_all_inputs_and_client_model_ids(saved_answers, evaluator):
    raw, evaluate = evaluator
    result = phase.run_ragas_50q(saved_answers)
    evaluate.assert_called_once_with(
        [row["question"] for row in saved_answers], [row["answer"] for row in saved_answers],
        [row["contexts"] for row in saved_answers], [row["ground_truth"] for row in saved_answers])
    assert result.evaluator_models == raw["metadata"]["evaluator_models"]
    for original, measured in zip(saved_answers, result.results):
        assert measured.question_id == original["id"]
        assert measured.distribution == original["distribution"]
        for field in ("question", "answer", "contexts", "ground_truth"):
            assert getattr(measured, field) == original[field]
        assert all(type(getattr(measured, metric)) is float for metric in phase.METRICS)
    result.results[0].contexts.append("changed copy")
    assert saved_answers[0]["contexts"] == ["Retrieved evidence 1"]


@pytest.mark.parametrize("value", [None, True, False, "0.8", float("nan"), float("inf"), -.1, 1.1])
def test_invalid_metrics_are_rejected_without_fabricated_scores(saved_answers, evaluator, value):
    raw, _ = evaluator
    raw["per_question"][0]["faithfulness"] = value
    with pytest.raises(ValueError, match="Question 1: faithfulness"):
        phase.run_ragas_50q(saved_answers)


@pytest.mark.parametrize("mutation", ["missing", "short", "extra", "reordered", "missing_metric"])
def test_evaluator_cannot_drop_or_reassign_rows(saved_answers, evaluator, mutation):
    raw, _ = evaluator
    if mutation == "missing":
        raw.pop("per_question")
    elif mutation == "short":
        raw["per_question"].pop()
    elif mutation == "extra":
        raw["per_question"].append(raw["per_question"][0])
    elif mutation == "reordered":
        raw["per_question"] = list(reversed(raw["per_question"]))
    else:
        raw["per_question"][0].pop("context_recall")
    with pytest.raises(ValueError):
        phase.run_ragas_50q(saved_answers)


@pytest.mark.parametrize("metadata", [None, {}, {"evaluator_models": []},
                                     {"evaluator_models": [" "]}, {"evaluator_models": "judge"}])
def test_evaluator_models_are_required_without_judge_fallback(saved_answers, evaluator, metadata):
    raw, _ = evaluator
    raw["metadata"] = metadata
    with pytest.raises(ValueError, match="evaluator_models"):
        phase.run_ragas_50q(saved_answers)


@pytest.mark.parametrize("status", ["skipped", "partial", "failed"])
def test_incomplete_evaluation_is_not_exported_as_complete(saved_answers, evaluator, status):
    raw, _ = evaluator
    raw.update(status=status, error="Provider evaluation incomplete")
    with pytest.raises(ValueError, match=status):
        phase.run_ragas_50q(saved_answers)


@pytest.mark.parametrize("mutation", ["empty", "duplicate_id", "unknown_distribution"])
def test_invalid_input_stops_before_calling_evaluator(saved_answers, evaluator, mutation):
    _, evaluate = evaluator
    if mutation == "empty":
        saved_answers.clear()
    elif mutation == "duplicate_id":
        saved_answers[0]["id"] = saved_answers[1]["id"]
    else:
        saved_answers[0]["distribution"] = "unknown"
    with pytest.raises(ValueError):
        phase.run_ragas_50q(saved_answers)
    evaluate.assert_not_called()


def test_grouping_preserves_order_and_leaves_absent_groups_empty():
    questions = [{"id": 8, "distribution": "multi_hop"}, {"id": 3, "distribution": "multi_hop"}]
    groups = phase.group_by_distribution(questions)
    assert groups == {"factual": [], "multi_hop": questions, "adversarial": []}
    assert groups["multi_hop"][0] is questions[0]


def test_bottom_diagnosis_uses_answer_reference_and_context_evidence():
    result = phase.RagasResult(
        41, "adversarial", "Áp dụng chính sách nghỉ phép năm nào?", "12 ngày phép.",
        ["Quy định v2023: 12 ngày.", "Quy định v2024: 15 ngày phép."],
        "Theo v2024, nhân viên có 15 ngày phép.", .9, .8, .7, .2)
    [row] = phase.bottom_10([result])
    assert result.answer in row["diagnosis"]
    assert result.ground_truth in row["diagnosis"]
    assert result.contexts[1] in row["diagnosis"]
    assert "v2023" in row["diagnosis"] and "v2024" in row["diagnosis"]
    assert "cần kiểm tra" in row["diagnosis"]
    assert "phiên bản hiệu lực" in row["suggested_fix"]
    assert "LLM hallucinating" not in row["diagnosis"]


def test_empty_context_is_explained_as_missing_evidence():
    result = phase.RagasResult(1, "multi_hop", "Q", "A", [], "GT", .1, .2, .3, .4)
    [row] = phase.bottom_10([result])
    assert "Không có context" in row["diagnosis"]
    assert "corpus/index" in row["suggested_fix"]
    assert "từng vế" in row["suggested_fix"]


def test_bottom_ties_keep_source_order_and_do_not_mutate_results():
    results = [phase.RagasResult(i, "factual", str(i), "A", ["C"], "GT", .8, .8, .8, .8)
               for i in (9, 2, 7)]
    original = [asdict(row) for row in results]
    assert [row["question_id"] for row in phase.bottom_10(results)] == [9, 2, 7]
    assert [asdict(row) for row in results] == original


def test_cluster_omits_empty_groups_from_means_and_counts_high_scores():
    result = phase.RagasResult(1, "factual", "Q", "A", ["C"], "GT", .99, .98, .97, .96)
    analysis = phase.cluster_analysis([result])
    assert analysis["distribution_avg_scores"] == {"factual": result.avg_score}
    assert analysis["dominant_failure_distribution"] == "factual"
    assert analysis["matrix"]["context_recall"] == {"factual": 1, "multi_hop": 0, "adversarial": 0}
    assert "kể cả câu điểm cao" in analysis["insight"]


def test_empty_cluster_does_not_invent_quality_scores():
    analysis = phase.cluster_analysis([])
    assert analysis["distribution_avg_scores"] == {}
    assert analysis["dominant_failure_distribution"] is None
    assert analysis["dominant_failure_metric"] is None
    assert all(value == 0 for counts in analysis["matrix"].values() for value in counts.values())


def test_phase_a_runner_exports_valid_report_using_student_analysis(saved_answers, evaluator, monkeypatch, tmp_path):
    from src import experiment_runners as runners
    from src.experiment_support import read_json, write_json
    from src.report_contracts import validate_metadata, validate_phase_a

    answer_path = tmp_path / "answers_50q.json"
    write_json(answer_path, saved_answers)
    monkeypatch.setattr(runners, "ANSWERS_PATH", answer_path)
    monkeypatch.setattr(runners, "ARTIFACTS_DIR", tmp_path)
    report = runners.run_phase_a()

    validate_phase_a(report, saved_answers)
    validate_metadata(report, [answer_path, runners.TEST_SET_PATH])
    assert read_json(tmp_path / "ragas_50q.json") == report
    assert report["failure_clusters"]["distribution_avg_scores"] == {
        "factual": .75, "multi_hop": .75, "adversarial": .75}
    assert report["metadata"]["models"]["evaluator"] == ["measured-embedding", "measured-llm"]
    assert report["metadata"]["models"]["judge"] == []
    assert report["bottom_10"] == phase.bottom_10(phase.run_ragas_50q(saved_answers).results)
