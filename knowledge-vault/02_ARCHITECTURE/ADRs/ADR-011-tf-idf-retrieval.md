# ADR 011: In-Memory TF-IDF for Story Graph Retrieval

## Status
Accepted

## Context
Milestone M4 requires finding long-range semantic links between candidate segments across different chapters of a long livestream to form a Story Graph. Comparing every segment against every other segment using a generative model is $O(N^2)$ and too expensive. We need a fast, local retrieval mechanism to propose a subset of plausible candidate pairs to the generative model for linking.

Using a dedicated Vector Database (like Pinecone, Milvus, or Qdrant) violates ADR-006 (Minimal Operational Dependencies).
Using PostgreSQL `pgvector` introduces native binary extension dependencies which complicate local development and deployments for this simple MVP.

## Decision
We will use an **in-memory TF-IDF (Term Frequency - Inverse Document Frequency)** combined with **cosine similarity** via scikit-learn for initial cross-chapter pair retrieval.

1.  **Lightweight:** Scikit-learn is a standard Python dependency that does not require additional infrastructure or native database extensions.
2.  **Sufficient for Text:** Stream transcripts (dialogue) are highly lexical. While they lack the deep semantic mapping of dense neural embeddings, TF-IDF is surprisingly effective at finding callbacks and repeated jokes based on shared vocabulary.
3.  **In-Memory:** Given the bounds of a livestream (e.g., a few thousand candidate segments max), building a TF-IDF matrix in memory takes milliseconds and consumes negligible RAM.

## Consequences
- **Positive:** Zero new infrastructure. Fast local development. Satisfies ADR-006.
- **Negative:** Misses purely semantic links (e.g., synonyms used in a callback that share no exact words with the setup). If this becomes a severe limitation for story quality, we will revisit `pgvector` or local dense embeddings (e.g., SentenceTransformers) in a future milestone.

## References
- ADR 006: Minimal Operational Dependencies
