from __future__ import annotations

"""Module 4: RAGAS Evaluation — 4 metrics + failure analysis."""

import os, sys, json, math
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dataclasses import dataclass, asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (TEST_SET_PATH, OPENAI_API_KEY, LLM_PROVIDER, LLM_MODEL,
                    RAGAS_LLM_MODEL, RAGAS_EMBEDDING_MODEL)
from src.llm_clients import create_ragas_llm, create_ragas_embeddings


METRICS = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float | None
    answer_relevancy: float | None
    context_precision: float | None
    context_recall: float | None


def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    """Load test set from JSON. (Đã implement sẵn)"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str],
                   metric_names: list[str] | None = None) -> dict:
    """Evaluate with the RAGAS 0.1 API pinned in requirements.txt.

    Aggregate fallback values remain numeric for callers, but status and
    valid_counts distinguish missing measurements from genuinely low scores.
    Failed per-question measurements are None, serialized as JSON null.
    """
    requested = list(METRICS) if metric_names is None else list(dict.fromkeys(metric_names))
    if not requested or any(name not in METRICS for name in requested):
        raise ValueError("metric_names must select one or more of the four supported metrics")
    if len({len(questions), len(answers), len(contexts), len(ground_truths)}) != 1:
        raise ValueError("questions, answers, contexts and ground_truths must have equal lengths")
    if any(not isinstance(value, str) for column in (questions, answers, ground_truths) for value in column):
        raise ValueError("questions, answers and ground_truths must contain strings")
    if any(not isinstance(group, list) or any(not isinstance(c, str) for c in group) for group in contexts):
        raise ValueError("contexts must be a list of lists of strings")

    rows = [EvalResult(q, a, list(c), gt, None, None, None, None)
            for q, a, c, gt in zip(questions, answers, contexts, ground_truths)]
    output = {**dict.fromkeys(METRICS, 0.0), "per_question": rows, "status": "skipped",
              "error": None, "valid_counts": dict.fromkeys(METRICS, 0),
              "evaluated_metrics": requested, "metadata": {"evaluator_models": []}}
    if not questions:
        output["error"] = "Empty evaluation dataset"
        return output
    if not OPENAI_API_KEY:
        output["error"] = "OPENAI_API_KEY is not configured; RAGAS was not run"
        print(f"  ⚠️  {output['error']}")
        return output
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall
        from ragas.run_config import RunConfig

        dataset = Dataset.from_dict({"question": questions, "answer": answers,
                                     "contexts": contexts, "ground_truth": ground_truths})
        faithful_metric = Faithfulness()
        faithful_metric.sentence_segmenter = CompleteSentenceSegmenter(faithful_metric.sentence_segmenter)
        metrics = {"faithfulness": faithful_metric, "answer_relevancy": AnswerRelevancy(),
                   "context_precision": ContextPrecision(), "context_recall": ContextRecall()}
        evaluator_llm = create_ragas_llm()
        evaluator_embeddings = create_ragas_embeddings()
        configured_llm = getattr(evaluator_llm, "langchain_llm", evaluator_llm)
        evaluator_models = [configured_llm.model_name]
        if "answer_relevancy" in requested:
            evaluator_models.append(evaluator_embeddings.model)
        if any(not isinstance(model, str) or not model.strip() for model in evaluator_models):
            raise ValueError("RAGAS evaluator clients must expose their configured model IDs")
        result = evaluate(
            dataset, metrics=[metrics[name] for name in requested],
            llm=evaluator_llm,
            embeddings=evaluator_embeddings,
            run_config=RunConfig(timeout=180, max_retries=2,
                                 max_workers=4 if LLM_PROVIDER == "openai" else 1),
            raise_exceptions=False,
        )
        output["metadata"]["evaluator_models"] = list(dict.fromkeys(evaluator_models))
        records = result.to_pandas().to_dict(orient="records")
        if len(records) != len(rows):
            raise ValueError("RAGAS returned an unexpected number of rows")
        for row, record in zip(rows, records):
            for metric in METRICS:
                setattr(row, metric, _finite_score(record.get(metric)))
        for metric in METRICS:
            valid = [getattr(row, metric) for row in rows if getattr(row, metric) is not None]
            output[metric] = sum(valid) / len(valid) if valid else 0.0
            output["valid_counts"][metric] = len(valid)
        counts = [output["valid_counts"][name] for name in requested]
        output["status"] = "ok" if all(count == len(rows) for count in counts) else (
            "partial" if any(counts) else "failed")
        if output["status"] != "ok":
            output["error"] = "Some RAGAS measurements failed; inspect null scores and valid_counts"
    except Exception as exc:
        output["status"] = "failed"
        output["error"] = f"{type(exc).__name__}: {exc}"
        print(f"  ⚠️  RAGAS evaluation failed: {output['error']}")
    return output


class CompleteSentenceSegmenter:
    """Preserve answer text while making fragments visible to RAGAS 0.1.

    Faithfulness discards sentences without a terminal period. Add punctuation
    only to its evaluation view; never rewrite the saved answer or invent claims.
    """
    def __init__(self, segmenter):
        self.segmenter = segmenter

    def segment(self, answer: str) -> list[str]:
        parts = self.segmenter.segment(answer) if self.segmenter else [answer]
        return [part.strip().rstrip(".!?") + "." for part in parts if part.strip()]


def _finite_score(value) -> float | None:
    if value is None:
        return None
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    return score if math.isfinite(score) else None


def failure_analysis(eval_results: list[EvalResult | dict], bottom_n: int = 5) -> list[dict]:
    """Analyze bottom-N worst questions using Diagnostic Tree."""
    if bottom_n <= 0:
        return []
    diagnostic_tree = {
        "faithfulness": ("Possible unsupported claims in the answer",
                         "Inspect answer claims against context; tighten grounding prompt",
                         ["Output incorrect?", "Check whether context supports each claim", "Inspect LLM generation"]),
        "answer_relevancy": ("Possible mismatch between answer and question",
                             "Inspect question intent; make the answer direct and complete",
                             ["Output off topic?", "Check question intent", "Inspect generation prompt"]),
        "context_precision": ("Possibly too many irrelevant retrieved chunks",
                              "Inspect retrieved candidates; improve reranking or metadata filters",
                              ["Output incorrect?", "Context irrelevant?", "Inspect retrieval and reranking"]),
        "context_recall": ("Possibly missing evidence needed for the expected answer",
                           "Inspect corpus coverage, chunk boundaries, hybrid search and parent expansion",
                           ["Output incomplete?", "Evidence missing?", "Check corpus, chunking and retrieval"]),
    }
    failures = []
    for result in eval_results:
        row = asdict(result) if isinstance(result, EvalResult) else result
        scores = {metric: _finite_score(row.get(metric)) for metric in METRICS}
        # Incomplete evaluations are not comparable with fully measured rows.
        if any(score is None for score in scores.values()):
            continue
        worst = min(scores, key=scores.get)
        diagnosis, fix, tree = diagnostic_tree[worst]
        failures.append({"question": row["question"], "expected": row.get("ground_truth", ""),
                         "answer": row.get("answer", ""), "contexts": list(row.get("contexts", [])),
                         "worst_metric": worst, "worst_score": scores[worst],
                         "score": sum(scores.values()) / len(METRICS), "metrics": scores,
                         "diagnosis": diagnosis, "suggested_fix": fix, "error_tree": tree})
    return sorted(failures, key=lambda row: row["score"])[:bottom_n]


def save_report(results: dict, failures: list[dict], path: str = "reports/ragas_report.json"):
    """Save evaluation report to JSON. (Đã implement sẵn)"""
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    rows = [asdict(row) if isinstance(row, EvalResult) else dict(row)
            for row in results.get("per_question", [])]
    for row in rows:
        for metric in METRICS:
            row[metric] = _finite_score(row.get(metric))
    report = {
        "aggregate": {metric: _finite_score(results.get(metric)) for metric in METRICS},
        "num_questions": len(rows),
        "status": results.get("status", "unknown"),
        "error": results.get("error"),
        "valid_counts": results.get("valid_counts", {}),
        "evaluated_metrics": results.get("evaluated_metrics", list(METRICS)),
        "faithfulness_sentence_normalization": "terminal punctuation only; saved answers unchanged",
        "provider": LLM_PROVIDER,
        "generation_model": LLM_MODEL,
        "evaluation_model": RAGAS_LLM_MODEL,
        "evaluation_embedding_model": RAGAS_EMBEDDING_MODEL,
        "enrichment_enabled": results.get("enrichment_enabled", False),
        "enrichment_counts": results.get("enrichment_counts", {}),
        "per_question": rows,
        "failures": failures,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, allow_nan=False)
    print(f"Report saved to {path}")


if __name__ == "__main__":
    test_set = load_test_set()
    print(f"Loaded {len(test_set)} test questions")
    print("Run pipeline.py first to generate answers, then call evaluate_ragas().")
