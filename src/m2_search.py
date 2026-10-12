from __future__ import annotations

"""Module 2: Hybrid Search — BM25 (Vietnamese) + Dense + RRF."""

import os, sys, re, unicodedata, warnings
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME, EMBEDDING_MODEL,
                    EMBEDDING_DIM, BM25_TOP_K, DENSE_TOP_K, HYBRID_TOP_K)


@dataclass
class SearchResult:
    text: str
    score: float
    metadata: dict
    method: str  # "bm25", "dense", "hybrid"


def segment_vietnamese(text: str) -> str:
    """Segment Vietnamese text into words."""
    if not text.strip():
        return ""
    from underthesea import word_tokenize

    return word_tokenize(unicodedata.normalize("NFC", text), format="text").replace("_", " ")


def _tokens(text: str) -> list[str]:
    """Normalize queries and documents consistently, including punctuation."""
    return re.findall(r"[^\W_]+", segment_vietnamese(text).casefold(), flags=re.UNICODE)


class BM25Search:
    def __init__(self):
        self.corpus_tokens = []
        self.documents = []
        self.bm25 = None

    def index(self, chunks: list[dict]) -> None:
        """Build BM25 index from chunks."""
        self.bm25 = None
        self.documents, self.corpus_tokens = [], []
        for chunk in chunks:
            tokens = _tokens(chunk["text"])
            if tokens:
                self.documents.append({"text": chunk["text"], "metadata": dict(chunk.get("metadata", {}))})
                self.corpus_tokens.append(tokens)
        if self.corpus_tokens:
            from rank_bm25 import BM25Okapi

            self.bm25 = BM25Okapi(self.corpus_tokens)

    def search(self, query: str, top_k: int = BM25_TOP_K) -> list[SearchResult]:
        """Search using BM25."""
        if self.bm25 is None or top_k <= 0 or not query.strip():
            return []
        tokens = _tokens(query)
        if not tokens:
            return []
        scores = self.bm25.get_scores(tokens)
        indices = sorted(range(len(scores)), key=lambda i: float(scores[i]), reverse=True)
        # BM25Okapi can produce zero/negative scores on very small corpora.
        # Keep lexical matches even in that case; discard documents with no overlap.
        query_terms = set(tokens)
        indices = [i for i in indices if query_terms.intersection(self.corpus_tokens[i])][:top_k]
        return [SearchResult(self.documents[i]["text"], float(scores[i]),
                             dict(self.documents[i]["metadata"]), "bm25") for i in indices]


class DenseSearch:
    def __init__(self):
        self._client = None
        self._encoder = None

    @property
    def client(self):
        """Connect lazily; make the scaffold's in-memory fallback visible."""
        if self._client is None:
            self._client = self._connect()
        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    def _connect(self):
        from qdrant_client import QdrantClient
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=30)
        try:
            client.get_collections()
            return client
        except Exception as exc:
            client.close()
            warnings.warn(f"Qdrant unavailable; using a temporary in-memory index: {exc}",
                          RuntimeWarning, stacklevel=2)
            return QdrantClient(":memory:")

    def _get_encoder(self):
        if self._encoder is None:
            from sentence_transformers import SentenceTransformer
            self._encoder = SentenceTransformer(EMBEDDING_MODEL)
        return self._encoder

    def index(self, chunks: list[dict], collection: str = COLLECTION_NAME) -> None:
        """Index chunks into Qdrant."""
        from qdrant_client.models import Distance, VectorParams, PointStruct

        documents = [c for c in chunks if c["text"].strip()]
        client = self.client
        if client.collection_exists(collection_name=collection):
            client.delete_collection(collection_name=collection)
        client.create_collection(collection_name=collection,
                                 vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE))
        if not documents:
            return
        encoder = self._get_encoder()
        for start in range(0, len(documents), 64):
            batch = documents[start:start + 64]
            vectors = encoder.encode([c["text"] for c in batch], normalize_embeddings=True,
                                     show_progress_bar=True)
            points = []
            for offset, (chunk, vector) in enumerate(zip(batch, vectors)):
                values = vector.tolist()
                if len(values) != EMBEDDING_DIM:
                    raise ValueError(f"Expected {EMBEDDING_DIM}-dimensional embeddings, got {len(values)}")
                points.append(PointStruct(id=start + offset, vector=values,
                                          payload={"text": chunk["text"],
                                                   "metadata": dict(chunk.get("metadata", {}))}))
            client.upsert(collection_name=collection, points=points, wait=True)

    def search(self, query: str, top_k: int = DENSE_TOP_K, collection: str = COLLECTION_NAME) -> list[SearchResult]:
        """Search using dense vectors."""
        if top_k <= 0 or not query.strip():
            return []
        client = self.client
        if not client.collection_exists(collection_name=collection):
            return []
        info = client.get_collection(collection_name=collection)
        if info.points_count == 0:
            return []
        vector = self._get_encoder().encode(query, normalize_embeddings=True).tolist()
        # Day 24 pins Qdrant client/server 1.9, which use the search endpoint.
        points = client.search(collection_name=collection, query_vector=vector,
                               limit=top_k, with_payload=True)
        return [SearchResult(pt.payload["text"], float(pt.score),
                             dict(pt.payload.get("metadata", {})), "dense")
                for pt in points if pt.payload and "text" in pt.payload]


def reciprocal_rank_fusion(results_list: list[list[SearchResult]], k: int = 60,
                           top_k: int = HYBRID_TOP_K) -> list[SearchResult]:
    """Merge ranked lists using RRF: score(d) = Σ 1/(k + rank)."""
    if k < 0:
        raise ValueError("RRF k must be non-negative")
    if top_k <= 0:
        return []
    scores, documents = {}, {}
    for results in results_list:
        seen = set()
        for rank, result in enumerate(results, start=1):
            metadata = result.metadata
            identity = ("id", metadata["chunk_id"]) if metadata.get("chunk_id") else (
                "text", metadata.get("source", ""), metadata.get("parent_id", ""), result.text)
            if identity in seen:
                continue
            seen.add(identity)
            documents.setdefault(identity, result)
            scores[identity] = scores.get(identity, 0.0) + 1.0 / (k + rank)
    identities = sorted(scores, key=scores.get, reverse=True)[:top_k]
    return [SearchResult(documents[key].text, scores[key], dict(documents[key].metadata), "hybrid")
            for key in identities]


class HybridSearch:
    """Combines BM25 + Dense + RRF. (Đã implement sẵn — dùng classes ở trên)"""
    def __init__(self):
        self.bm25 = BM25Search()
        self.dense = DenseSearch()
        self.parent_documents = {}

    def index(self, chunks: list[dict]) -> None:
        self.bm25.index(chunks)
        self.dense.index(chunks)

    def search(self, query: str, top_k: int = HYBRID_TOP_K) -> list[SearchResult]:
        bm25_results = self.bm25.search(query, top_k=BM25_TOP_K)
        dense_results = self.dense.search(query, top_k=DENSE_TOP_K)
        return reciprocal_rank_fusion([bm25_results, dense_results], top_k=top_k)


if __name__ == "__main__":
    print(f"Original:  Nhân viên được nghỉ phép năm")
    print(f"Segmented: {segment_vietnamese('Nhân viên được nghỉ phép năm')}")
