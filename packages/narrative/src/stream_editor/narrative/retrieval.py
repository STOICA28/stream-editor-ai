"""
LinkCandidateRetriever — retrieves plausible narrative link candidates using TF-IDF.

Avoids O(N²) exhaustive pairwise model comparison.
For each target candidate, retrieves top-K semantically similar source candidates
from earlier in the timeline. These proposals are THEN validated by the Pro model.

No external vector DB. In-memory TF-IDF cosine similarity per generation run.
"""
from __future__ import annotations

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Minimum TF-IDF cosine similarity to propose a pair
DEFAULT_MIN_SIMILARITY = 0.15
# Max candidates to retrieve per node
DEFAULT_MAX_K = 10


def _tokenize(text: str) -> list[str]:
    """Simple word tokenizer — lowercase, remove punctuation, min 2 chars."""
    return [w for w in re.sub(r"[^\w\s]", " ", text.lower()).split() if len(w) >= 2]


def _compute_tf(tokens: list[str]) -> dict[str, float]:
    counts = Counter(tokens)
    total = max(len(tokens), 1)
    return {term: count / total for term, count in counts.items()}


@dataclass
class CandidatePair:
    source_id: str   # earlier candidate
    target_id: str   # later candidate (potential callback/payoff)
    similarity: float
    shared_terms: list[str]


class LinkCandidateRetriever:
    """
    TF-IDF based retrieval of plausible narrative link candidates.

    For each candidate, computes a TF-IDF vector from its transcript excerpt
    and summary. Retrieves top-K earlier candidates by cosine similarity.

    This is cheap retrieval — NOT narrative reasoning. The Pro model
    validates retrieved pairs before any edges are created.
    """

    def __init__(
        self,
        max_k: int = DEFAULT_MAX_K,
        min_similarity: float = DEFAULT_MIN_SIMILARITY,
    ) -> None:
        self._max_k = max_k
        self._min_similarity = min_similarity

    def retrieve_pairs(
        self,
        candidates: list[dict[str, object]],
    ) -> list[CandidatePair]:
        """
        For each candidate, retrieve top-K earlier candidates by TF-IDF similarity.

        Args:
            candidates: List of candidate dicts sorted by start_time.
                        Must have 'id', 'start_time', 'transcript_excerpt', 'summary'.

        Returns:
            List of CandidatePairs to evaluate for narrative relationships.
            No duplicates — each (source, target) appears at most once.
        """
        if len(candidates) < 2:
            return []

        # Sort by time to enforce temporal direction (source appears before target)
        sorted_candidates = sorted(candidates, key=lambda c: float(str(c.get("start_time", 0))))

        # Build text corpus
        texts: list[str] = []
        for c in sorted_candidates:
            excerpt = str(c.get("transcript_excerpt", "") or "")
            summary = str(c.get("summary", "") or "")
            texts.append(f"{excerpt} {summary}")

        # Compute TF vectors
        token_lists = [_tokenize(t) for t in texts]
        tf_vectors = [_compute_tf(tokens) for tokens in token_lists]

        # Build IDF from all tokens in corpus
        doc_freq: Counter[str] = Counter()
        n_docs = len(sorted_candidates)
        for tokens in token_lists:
            for term in set(tokens):
                doc_freq[term] += 1
        idf: dict[str, float] = {
            term: math.log((n_docs + 1) / (freq + 1)) + 1.0
            for term, freq in doc_freq.items()
        }

        # Compute TF-IDF vectors
        def tfidf(tf_vec: dict[str, float]) -> dict[str, float]:
            return {term: score * idf.get(term, 1.0) for term, score in tf_vec.items()}

        tfidf_vectors = [tfidf(tf) for tf in tf_vectors]

        # L2 norms for cosine similarity
        def norm(vec: dict[str, float]) -> float:
            return math.sqrt(sum(v * v for v in vec.values())) or 1.0

        norms = [norm(v) for v in tfidf_vectors]

        # Retrieve pairs: for each target index i, look at sources j < i
        pairs: list[CandidatePair] = []
        seen: set[tuple[str, str]] = set()

        for i in range(1, n_docs):
            target_vec = tfidf_vectors[i]
            target_norm = norms[i]
            target_id = str(sorted_candidates[i].get("id", ""))

            scored: list[tuple[float, int, list[str]]] = []
            for j in range(i):
                source_vec = tfidf_vectors[j]
                source_norm = norms[j]
                source_id = str(sorted_candidates[j].get("id", ""))

                # Cosine similarity
                shared_terms_set = set(target_vec.keys()) & set(source_vec.keys())
                dot = sum(target_vec[t] * source_vec[t] for t in shared_terms_set)
                sim = dot / (target_norm * source_norm)

                if sim >= self._min_similarity:
                    scored.append((sim, j, sorted(shared_terms_set)))

            # Take top-K
            scored.sort(key=lambda x: x[0], reverse=True)
            for sim, j, shared in scored[: self._max_k]:
                source_id = str(sorted_candidates[j].get("id", ""))
                pair_key = (source_id, target_id)
                if pair_key not in seen:
                    seen.add(pair_key)
                    pairs.append(CandidatePair(
                        source_id=source_id,
                        target_id=target_id,
                        similarity=sim,
                        shared_terms=shared[:10],   # keep top 10 shared terms for debug
                    ))

        logger.info(
            "Retrieval found %d candidate pairs from %d candidates (min_sim=%.2f, max_k=%d)",
            len(pairs), n_docs, self._min_similarity, self._max_k,
        )
        return pairs
