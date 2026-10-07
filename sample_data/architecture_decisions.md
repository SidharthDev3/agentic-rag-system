# Architectural Decision Records (ADRs) — NexusRAG

## ADR-001: LangGraph for Agentic Orchestration Over Linear Chains

### Context
Traditional RAG pipelines follow a rigid sequential paradigm: Query -> Vector DB -> Prompt -> LLM. This naive approach suffers from high failure rates when dealing with ambiguous queries, multi-hop reasoning, comparison questions, or out-of-domain prompts where retrieval should be aborted or decomposed.

### Decision
We adopt LangGraph to model the RAG pipeline as a cyclic state machine. The state graph defines explicit nodes:
1. Query Understanding & Classification
2. Query Rewriter & Decomposition
3. Retrieval Strategy Planner
4. Hybrid Dense/Sparse Retrieval
5. Cross-Encoder Reranker
6. Context Compressor
7. Grounded Answer Synthesis
8. Citation Verifier
9. Grounding & Hallucination Guardrail

### Consequences
- Allows conditional routing: conversational pleasantries bypass expensive retrieval, whereas comparison queries trigger multi-hop parallel retrieval.
- Exposes intermediate telemetry and state transitions to the client for streaming observability.
- Enhances determinism and auditability compared to unbounded autonomous agent loops.

---

## ADR-002: PostgreSQL + pgvector as Unified Data Store

### Context
Managing distinct databases for relational operational metadata (documents, users, logs) and dedicated vector databases (e.g. Pinecone, Milvus, Qdrant) introduces synchronization complexity, distributed transactions, and additional infrastructure costs.

### Decision
We use PostgreSQL with the `pgvector` extension and built-in `tsvector` full-text search.

### Consequences
- Single database transaction handles document records, metadata, chunk text, full-text indexes, and high-dimensional vector embeddings.
- ACID guarantees ensure document deletion cascades completely to chunks and vector indexes.
- Supports HNSW and IVFFlat index types for scalable cosine distance search.

---

## ADR-003: Hybrid Retrieval with Reciprocal Rank Fusion (RRF)

### Context
Dense vector embeddings excel at semantic similarity and conceptual matching, but frequently fail on exact keywords, part numbers, domain acronyms, and rare terms (the "vocabulary mismatch" problem). Conversely, BM25 keyword search excels at exact lexical matching but fails on synonymous phrasing.

### Decision
We combine dense vector similarity search with PostgreSQL full-text search (BM25-equivalent) using Reciprocal Rank Fusion:
RRF(d) = sum( weight_i / (k + rank_i(d)) ) with constant k = 60.

### Consequences
- Provides high recall across both semantic and exact lexical search spaces.
- Robust against score distribution differences between cosine distance and BM25 rank scores.

---

## ADR-004: Two-Stage Retrieval with Cross-Encoder Reranking

### Context
Bi-encoders compute vector embeddings for documents and queries independently, allowing pre-computation and fast approximate nearest neighbors search. However, they lack token-level cross-attention between query and passage.

### Decision
We implement a two-stage retrieval pipeline:
1. Fast first-stage hybrid retrieval retrieves top-15 candidate chunks.
2. Second-stage cross-encoder (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2`) processes `[Query, Passage]` pairs jointly with full self-attention to produce precision scores.

### Consequences
- Boosts Precision@5 and MRR significantly compared to single-stage vector retrieval alone.
- Keeps latency low by running the computationally intensive cross-encoder only on the top-15 candidate chunks.

---

## ADR-005: Deterministic Citation Mapping and Grounding Verification

### Context
LLMs hallucinate facts and can cite plausible-looking sources that do not actually support their assertions.

### Decision
The system verifies all bracketed citation markers `[1]`, `[2]` against actual retrieved chunk IDs. Furthermore, a dedicated grounding evaluation node assesses claim-context alignment and flags unsupported statements. If grounding confidence drops below 0.70, the system surfaces a clear caveat or refusal rather than delivering confident misinformation.

