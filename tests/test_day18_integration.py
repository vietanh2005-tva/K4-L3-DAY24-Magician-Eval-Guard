"""Offline checks for the imported Day 18 modules and Day 24 adapters."""

import sys
from types import SimpleNamespace

import pytest

from src import m1_chunking, m2_search, m4_eval, m5_enrichment

pytestmark = pytest.mark.support


def test_chunking_and_enrichment_keep_source_order_and_parent_ids(monkeypatch):
    monkeypatch.setattr(m5_enrichment, "OPENAI_API_KEY", "")
    originals = []
    for source, text in (
        ("leave.md", "Nhân viên được nghỉ 15 ngày phép mỗi năm."),
        ("vpn.md", "Truy cập VPN cần xác thực nhiều yếu tố."),
    ):
        parents, children = m1_chunking.chunk_hierarchical(text, metadata={"source": source})
        parent_ids = {parent.metadata["parent_id"] for parent in parents}
        assert all(child.parent_id in parent_ids for child in children)
        originals.extend({"text": child.text, "metadata": {
            **child.metadata, "parent_id": child.parent_id}} for child in children)

    enriched = m5_enrichment.enrich_chunks(originals)
    assert len(enriched) == len(originals)
    for original, result in zip(originals, enriched):
        assert result.original_text == original["text"]
        assert result.enriched_text.endswith(original["text"])
        for key in ("source", "chunk_id", "parent_id"):
            assert result.auto_metadata[key] == original["metadata"][key]
        assert result.auto_metadata["enrichment_status"] == "fallback"


def test_dense_search_uses_qdrant_19_contract_and_preserves_payload():
    calls = []
    point = SimpleNamespace(score=.8, payload={
        "text": "Retrieved policy", "metadata": {"source": "leave.md", "parent_id": "p"}})

    def search(*, collection_name, query_vector, limit, with_payload):
        calls.append((collection_name, query_vector, limit, with_payload))
        return [point, SimpleNamespace(score=.1, payload=None)]

    dense = m2_search.DenseSearch()
    dense.client = SimpleNamespace(
        collection_exists=lambda **kwargs: True,
        get_collection=lambda **kwargs: SimpleNamespace(points_count=2), search=search)
    dense._encoder = SimpleNamespace(
        encode=lambda query, normalize_embeddings: SimpleNamespace(tolist=lambda: [.1, .2]))

    [result] = dense.search("Annual leave?", top_k=3, collection="day24-test")
    assert calls == [("day24-test", [.1, .2], 3, True)]
    assert result.text == point.payload["text"]
    assert result.metadata == point.payload["metadata"]
    assert result.score == .8
    assert result.method == "dense"


def install_fake_ragas(monkeypatch, records, wrapped):
    calls = []
    llm = SimpleNamespace(model_name="actual-evaluator-llm")
    if wrapped:
        llm = SimpleNamespace(langchain_llm=llm)
    embeddings = SimpleNamespace(model="actual-evaluator-embedding")

    class Faithfulness:
        sentence_segmenter = None

    def evaluate(dataset, *, metrics, llm, embeddings, run_config, raise_exceptions):
        calls.append({"dataset": dataset, "llm": llm, "embeddings": embeddings})
        return SimpleNamespace(to_pandas=lambda: SimpleNamespace(to_dict=lambda orient: records))

    monkeypatch.setitem(sys.modules, "datasets", SimpleNamespace(
        Dataset=SimpleNamespace(from_dict=lambda data: data)))
    monkeypatch.setitem(sys.modules, "ragas", SimpleNamespace(evaluate=evaluate))
    monkeypatch.setitem(sys.modules, "ragas.metrics", SimpleNamespace(
        Faithfulness=Faithfulness, AnswerRelevancy=object,
        ContextPrecision=object, ContextRecall=object))
    monkeypatch.setitem(sys.modules, "ragas.run_config", SimpleNamespace(
        RunConfig=lambda **kwargs: SimpleNamespace(**kwargs)))
    monkeypatch.setattr(m4_eval, "OPENAI_API_KEY", "unit-test-key")
    monkeypatch.setattr(m4_eval, "create_ragas_llm", lambda: llm)
    monkeypatch.setattr(m4_eval, "create_ragas_embeddings", lambda: embeddings)
    return calls, llm, embeddings


@pytest.mark.parametrize("wrapped", [False, True])
def test_ragas_records_models_from_used_clients_and_keeps_row_order(monkeypatch, wrapped):
    records = [dict.fromkeys(m4_eval.METRICS, .8), dict.fromkeys(m4_eval.METRICS, .2)]
    calls, llm, embeddings = install_fake_ragas(monkeypatch, records, wrapped)
    result = m4_eval.evaluate_ragas(["q1", "q2"], ["a1", "a2"], [["c1"], ["c2"]], ["gt1", "gt2"])

    assert result["status"] == "ok"
    assert result["metadata"]["evaluator_models"] == [
        "actual-evaluator-llm", "actual-evaluator-embedding"]
    assert [row.question for row in result["per_question"]] == ["q1", "q2"]
    assert [row.faithfulness for row in result["per_question"]] == [.8, .2]
    assert calls[0]["llm"] is llm
    assert calls[0]["embeddings"] is embeddings
    assert calls[0]["dataset"]["contexts"] == [["c1"], ["c2"]]


def test_failed_measurements_stay_missing(monkeypatch):
    records = [{**dict.fromkeys(m4_eval.METRICS, .8), "context_recall": float("nan")}]
    install_fake_ragas(monkeypatch, records, wrapped=False)
    result = m4_eval.evaluate_ragas(["q"], ["a"], [["c"]], ["gt"])
    assert result["status"] == "partial"
    assert result["per_question"][0].context_recall is None
    assert result["valid_counts"]["context_recall"] == 0


def test_missing_key_does_not_claim_evaluation_models(monkeypatch):
    monkeypatch.setattr(m4_eval, "OPENAI_API_KEY", "")
    result = m4_eval.evaluate_ragas(["q"], ["a"], [["c"]], ["gt"])
    assert result["status"] == "skipped"
    assert result["metadata"]["evaluator_models"] == []
    assert all(getattr(result["per_question"][0], metric) is None for metric in m4_eval.METRICS)
