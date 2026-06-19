"""TF-IDF cosine similarity for deterministic finding deduplication.

Runs without external dependencies using stdlib math only.
Produces embedding-quality dedup for finding titles without requiring
sentence-transformers (~300MB). Upgrade path: install sentence-transformers
and pass a loaded SentenceTransformer to _is_duplicate() for full semantic
embeddings — the fallback chain in synthesizer.py handles both paths.

Threshold 0.80: two findings with this similarity or higher describe the same bug.
"""

from __future__ import annotations

import math
import re
from collections import Counter

SIMILARITY_THRESHOLD = 0.80

_STOP_WORDS = frozenset({
    "a", "an", "the", "is", "in", "on", "at", "to", "for", "of", "and", "or",
    "but", "with", "not", "this", "that", "it", "be", "are", "was", "were",
    "has", "have", "had", "been", "will", "would", "could", "should", "may",
    "can", "do", "does", "did", "no", "from", "by", "as", "up", "if", "so",
})


def _tokenize(text: str) -> list[str]:
    tokens = re.sub(r"[^\w\s]", " ", text.lower()).split()
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]


def _idf(tokenized_docs: list[list[str]]) -> dict[str, float]:
    N = len(tokenized_docs)
    vocab: set[str] = {t for doc in tokenized_docs for t in doc}
    result: dict[str, float] = {}
    for term in vocab:
        df = sum(1 for doc in tokenized_docs if term in doc)
        result[term] = math.log((N + 1) / (df + 1)) + 1  # smoothed BM25-style
    return result


def _tfidf_vector(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    if not tokens:
        return {}
    counts = Counter(tokens)
    total = len(tokens)
    vec = {term: (count / total) * idf.get(term, 1.0) for term, count in counts.items()}
    mag = math.sqrt(sum(v * v for v in vec.values())) or 1.0
    return {k: v / mag for k, v in vec.items()}


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    # dot product — only iterate the smaller set
    if len(a) > len(b):
        a, b = b, a
    return sum(a_val * b.get(k, 0.0) for k, a_val in a.items())


class TFIDFEmbedder:
    """Batch TF-IDF deduplicator for finding titles.

    Usage pattern: create once per run, call is_duplicate() in order as new
    findings are encountered. The IDF weights are recomputed from the growing
    corpus each call — this is O(n·|vocab|) but n < 200 in practice so it's fast.
    """

    def __init__(self) -> None:
        self._corpus: list[str] = []

    def is_duplicate(self, candidate: str, existing: list[str]) -> bool:
        """Return True if candidate is semantically similar to any title in existing.

        Uses TF-IDF cosine similarity (primary) with a Jaccard backstop.
        The Jaccard backstop catches high word-overlap cases that TF-IDF misses
        when the corpus is small (n < 5) and IDF values are undifferentiated.
        """
        if not existing:
            return False
        cand_tokens = set(_tokenize(candidate))

        # Jaccard backstop — catches obvious rephrases with ≥65% token overlap
        for title in existing:
            ex_tokens = set(_tokenize(title))
            if cand_tokens and ex_tokens:
                union = cand_tokens | ex_tokens
                if union and len(cand_tokens & ex_tokens) / len(union) >= 0.65:
                    return True

        # TF-IDF cosine — better for larger corpora where IDF is meaningful
        all_docs = existing + [candidate]
        tokenized = [_tokenize(d) for d in all_docs]
        if not any(tokenized):
            return False
        idf = _idf(tokenized)
        vectors = [_tfidf_vector(t, idf) for t in tokenized]
        cand_vec = vectors[-1]
        return any(_cosine(ex_vec, cand_vec) >= SIMILARITY_THRESHOLD for ex_vec in vectors[:-1])

    # Sentence-transformer drop-in compatibility shim:
    # synthesizer.py calls embedder.encode([texts]) and uses numpy for cosine.
    # This shim makes TFIDFEmbedder work in that path too.
    def encode(self, texts: list[str]) -> list[list[float]]:  # type: ignore[return]
        """Produce pseudo-embeddings from TF-IDF vectors (for numpy cosine path)."""
        tokenized = [_tokenize(t) for t in texts]
        idf = _idf(tokenized)
        dim_order: list[str] = sorted({t for doc in tokenized for t in doc})
        vecs: list[list[float]] = []
        for tokens in tokenized:
            vec = _tfidf_vector(tokens, idf)
            vecs.append([vec.get(term, 0.0) for term in dim_order])
        return vecs
