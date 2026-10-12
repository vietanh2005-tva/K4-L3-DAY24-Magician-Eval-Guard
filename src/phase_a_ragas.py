from __future__ import annotations

"""Phase A: RAGAS Production Evaluation — 50q, 3 distributions, cluster analysis."""

import json
import math
import os
import re
import sys
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from numbers import Real

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH, ANSWERS_PATH, ARTIFACTS_DIR
from src.experiment_support import model_ids, write_json

Distribution = str  # "factual" | "multi_hop" | "adversarial"
DISTRIBUTIONS = ("factual", "multi_hop", "adversarial")
METRICS = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")

DIAGNOSTIC_TREE = {
    "faithfulness": (
        "Cần đối chiếu từng khẳng định của answer với bằng chứng trong contexts",
        "Kiểm tra các khẳng định chưa được context hỗ trợ; yêu cầu generation dẫn căn cứ hoặc từ chối khi thiếu dữ liệu"),
    "answer_relevancy": (
        "Cần kiểm tra answer đã trả lời trực tiếp và đủ các vế của question chưa",
        "Tách các ý được hỏi, đối chiếu với answer và sửa prompt để trả lời đủ từng ý"),
    "context_precision": (
        "Cần đọc từng context để xác định đoạn nào phù hợp với question",
        "Kiểm tra thứ hạng các đoạn liên quan; điều chỉnh hybrid search, reranking và bộ lọc nguồn/phiên bản"),
    "context_recall": (
        "Cần đối chiếu các ý thiết yếu của reference với toàn bộ contexts",
        "Tìm bằng chứng cho các ý còn thiếu trong corpus; kiểm tra chunk boundaries, hybrid search và top_k"),
}


@dataclass
class RagasResult:
    question_id: int
    distribution: Distribution
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float

    @property
    def avg_score(self) -> float:
        return (self.faithfulness + self.answer_relevancy +
                self.context_precision + self.context_recall) / 4

    @property
    def worst_metric(self) -> str:
        scores = {
            "faithfulness":      self.faithfulness,
            "answer_relevancy":  self.answer_relevancy,
            "context_precision": self.context_precision,
            "context_recall":    self.context_recall,
        }
        return min(scores, key=scores.get)


# ─── Đã implement sẵn ────────────────────────────────────────────────────────

@dataclass
class RagasEvaluation:
    """Task 2 output: measured rows plus model identifiers reported by m4."""
    results: list[RagasResult]
    evaluator_models: list[str]

def load_test_set_50q(path: str = TEST_SET_PATH) -> list[dict]:
    """Load 50q test set với 3 distributions."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_answers(path: str = ANSWERS_PATH) -> list[dict]:
    """Load pre-generated answers từ setup_answers.py."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"answers_50q.json không tìm thấy tại {path}\n"
            "→ Chạy trước: python scripts/setup_answers.py --live"
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_phase_a_report(results: list[RagasResult], clusters: dict, bottom: list[dict]) -> dict:
    """Provided exporter: preserve the student-produced Task 3 rows verbatim."""
    per_dist: dict[str, dict] = {}
    for dist in ["factual", "multi_hop", "adversarial"]:
        subset = [r for r in results if r.distribution == dist]
        if subset:
            per_dist[dist] = {
                "count": len(subset),
                "faithfulness":      sum(r.faithfulness for r in subset) / len(subset),
                "answer_relevancy":  sum(r.answer_relevancy for r in subset) / len(subset),
                "context_precision": sum(r.context_precision for r in subset) / len(subset),
                "context_recall":    sum(r.context_recall for r in subset) / len(subset),
                "avg_score":         sum(r.avg_score for r in subset) / len(subset),
            }

    report = {
        "total_questions": len(results),
        "per_question": [asdict(r) for r in results],
        "per_distribution": per_dist,
        "failure_clusters": clusters,
        "bottom_10": bottom,
    }
    return report


def save_phase_a_report(results: list[RagasResult], clusters: dict, bottom: list[dict],
                        path: str = os.path.join(ARTIFACTS_DIR, "ragas_50q.json")) -> None:
    write_json(path, build_phase_a_report(results, clusters, bottom))



# ─── Tasks 1-4: Sinh viên implement ──────────────────────────────────────────

def group_by_distribution(test_set: list[dict]) -> dict[str, list[dict]]:
    """Task 1: Nhóm 50 câu hỏi theo 3 distributions.

    Returns:
        {"factual": [...], "multi_hop": [...], "adversarial": [...]}
    """
    groups = {distribution: [] for distribution in DISTRIBUTIONS}
    for item in test_set:
        distribution = item.get("distribution")
        if distribution not in groups:
            raise ValueError(f"Question {item.get('id')}: unknown distribution {distribution!r}")
        groups[distribution].append(item)
    return groups


def run_ragas_50q(answers: list[dict]) -> RagasEvaluation:
    """Task 2: Chạy RAGAS 4 metrics trên toàn bộ 50 câu hỏi.

    Gợi ý — import từ Day 18 của bạn:
        from src.m4_eval import evaluate_ragas

    Steps:
        1. Extract questions, answers, contexts, ground_truths từ answers list
        2. Gọi evaluate_ragas() từ m4_eval.py
        3. Kết hợp kết quả với distribution info từ answers list
        4. Return RagasEvaluation(results, raw["metadata"]["evaluator_models"])
           m4 must report its actual LLM/embedding models; never guess JUDGE_MODEL.
    """
    if not answers:
        raise ValueError("RAGAS needs non-empty answers; generate answers_50q.json first")
    group_by_distribution(answers)
    ids = [answer["id"] for answer in answers]
    if any(type(question_id) is not int or question_id <= 0 for question_id in ids) or len(set(ids)) != len(ids):
        raise ValueError("RAGAS answers must have unique positive integer IDs")

    from src.m4_eval import evaluate_ragas

    raw = evaluate_ragas(
        [answer["question"] for answer in answers],
        [answer["answer"] for answer in answers],
        [list(answer["contexts"]) for answer in answers],
        [answer["ground_truth"] for answer in answers],
    )
    if not isinstance(raw, Mapping):
        raise ValueError("m4 must return an evaluation mapping")
    if raw.get("status", "ok") != "ok":
        raise ValueError(f"RAGAS evaluation is {raw.get('status')}: {raw.get('error')}")
    per_question = raw.get("per_question")
    if not isinstance(per_question, list) or len(per_question) != len(answers):
        raise ValueError("m4 per_question must contain exactly one row per answer")
    evaluator_metadata = raw.get("metadata")
    evaluator_models = evaluator_metadata.get("evaluator_models") if isinstance(evaluator_metadata, Mapping) else None
    if not model_ids(evaluator_models, "m4 evaluator_models"):
        raise ValueError("m4 must report non-empty evaluator_models from its evaluator clients")

    results = []
    for answer, measured in zip(answers, per_question):
        # m4 adapters may expose records as mappings or dataclass-like objects.
        fields = ("question", "answer", "contexts", "ground_truth", *METRICS)
        values = measured if isinstance(measured, Mapping) else {
            field: getattr(measured, field) for field in fields if hasattr(measured, field)}
        for field in ("question", "answer", "contexts", "ground_truth"):
            if field in values and values[field] != answer[field]:
                raise ValueError(f"Question {answer['id']}: m4 {field} does not match input row order")
        scores = {}
        for metric in METRICS:
            value = values.get(metric)
            if isinstance(value, bool) or not isinstance(value, Real):
                raise ValueError(f"Question {answer['id']}: {metric} must be numeric, not bool/string")
            try:
                value = float(value)
            except (TypeError, ValueError, OverflowError) as error:
                raise ValueError(f"Question {answer['id']}: missing or invalid {metric}") from error
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"Question {answer['id']}: {metric} must be finite and within [0, 1]")
            scores[metric] = value
        results.append(RagasResult(
            question_id=answer["id"], distribution=answer["distribution"],
            question=answer["question"], answer=answer["answer"],
            contexts=list(answer["contexts"]), ground_truth=answer["ground_truth"], **scores))
    return RagasEvaluation(results, list(evaluator_models))


def _excerpt(text: str, limit: int = 180) -> str:
    """Keep a short, identifiable source quote in each diagnostic row."""
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[:limit].rstrip() + "…"


def _diagnose(result: RagasResult) -> tuple[str, str]:
    """Record source evidence and a review hypothesis, not an asserted root cause."""
    metric = result.worst_metric
    review, fix = DIAGNOSTIC_TREE[metric]
    evidence = [f"{metric}={getattr(result, metric):.3f}; {review}.",
                f"Question: «{_excerpt(result.question)}».",
                f"Answer: «{_excerpt(result.answer)}».",
                f"Reference: «{_excerpt(result.ground_truth)}»."]
    if result.contexts:
        reference_terms = set(re.findall(r"\w+", result.ground_truth.casefold()))
        context = max(result.contexts, key=lambda value: len(
            reference_terms.intersection(re.findall(r"\w+", value.casefold()))))
        evidence.append(f"Context để đối chiếu ({len(result.contexts)} đoạn): «{_excerpt(context)}».")
        versions = sorted(set(re.findall(r"\b(?:v?20\d{2}|v\d+\.\d+)\b",
                                        "\n".join(result.contexts), flags=re.IGNORECASE)))
        if len(versions) > 1:
            evidence.append(f"Contexts có các mốc/phiên bản {', '.join(versions)}; cần kiểm tra hiệu lực.")
    else:
        evidence.append("Không có context được truy xuất để kiểm chứng câu trả lời.")
        fix = "Kiểm tra corpus/index và kết quả search/rerank để truy xuất được bằng chứng trước generation"
    if result.distribution == "multi_hop":
        fix += "; đối chiếu đủ bằng chứng cho từng vế và phép tính trong câu hỏi multi-hop"
    elif result.distribution == "adversarial":
        fix += "; đối chiếu phiên bản hiệu lực, phủ định và điều kiện trong question/reference"
    fix += f". Chạy lại cùng câu «{_excerpt(result.question, 100)}» và so sánh đủ bốn metric sau khi đọc evidence."
    return " ".join(evidence), fix


def bottom_10(results: list[RagasResult]) -> list[dict]:
    """Task 3: Lấy 10 câu hỏi có avg_score thấp nhất.

    Returns:
        [{"rank": 1, "question_id": ..., "distribution": ...,
          "question": ..., "avg_score": ..., "worst_metric": ...,
          "diagnosis": ..., "suggested_fix": ...}, ...]
    """
    output = []
    for rank, result in enumerate(sorted(results, key=lambda item: item.avg_score)[:10], 1):
        diagnosis, fix = _diagnose(result)
        output.append({
            "rank": rank, "question_id": result.question_id,
            "distribution": result.distribution, "question": result.question,
            "avg_score": result.avg_score, "worst_metric": result.worst_metric,
            "diagnosis": diagnosis, "suggested_fix": fix,
        })
    return output


def cluster_analysis(results: list[RagasResult]) -> dict:
    """Task 4: Phân tích failure clusters theo (worst_metric × distribution).

    Matrix thống kê worst_metric của mọi câu, không coi mọi câu là một failure.
    Nhóm yếu nhất = distribution có avg_score trung bình thấp nhất (bỏ nhóm rỗng).
    Tổng matrix theo cột chỉ là kích thước nhóm 20/20/10, không đo chất lượng.

    Returns:
        {
          "matrix": {
            "faithfulness":      {"factual": 3, "multi_hop": 5, "adversarial": 2},
            "answer_relevancy":  {...},
            "context_precision": {...},
            "context_recall":    {...},
          },
          "dominant_failure_distribution": "multi_hop",
          "dominant_failure_metric": "context_recall",
          "insight": "..."
        }
    """
    matrix = {metric: dict.fromkeys(DISTRIBUTIONS, 0) for metric in METRICS}
    scores = {distribution: [] for distribution in DISTRIBUTIONS}
    for result in results:
        if result.distribution not in scores:
            raise ValueError(f"Question {result.question_id}: unknown distribution {result.distribution!r}")
        matrix[result.worst_metric][result.distribution] += 1
        scores[result.distribution].append(result.avg_score)
    means = {distribution: sum(values) / len(values)
             for distribution, values in scores.items() if values}
    weakest = min(means, key=means.get) if means else None
    totals = {metric: sum(counts.values()) for metric, counts in matrix.items()}
    dominant_metric = max(totals, key=totals.get) if results else None
    if results:
        comparison = "; ".join(f"{distribution}: mean={mean:.4f}, n={len(scores[distribution])}"
                               for distribution, mean in means.items())
        insight = (
            f"{comparison}. Nhóm {weakest} có avg_score trung bình thấp nhất ({means[weakest]:.4f}). "
            f"{dominant_metric} là worst_metric của {totals[dominant_metric]}/{len(results)} câu. "
            "Matrix thống kê mọi câu, kể cả câu điểm cao; số đếm không phải số failures. "
            "Đọc question/answer/contexts/reference của bottom 10 để kiểm chứng nguyên nhân trước khi chọn cách sửa.")
    else:
        insight = "Chưa có kết quả để xác định nhóm yếu hoặc metric xuất hiện nhiều nhất."
    return {"matrix": matrix, "distribution_avg_scores": means,
            "dominant_failure_distribution": weakest,
            "dominant_failure_metric": dominant_metric, "insight": insight}


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from scripts.run_experiments import main
    raise SystemExit(main(["--phase", "a", *sys.argv[1:]]))
