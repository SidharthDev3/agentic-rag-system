# Comprehensive Survey of Retrieval-Augmented Generation (RAG) Paradigms

## 1. Evolution of RAG Paradigms

### Naive RAG
The first generation of RAG follows a linear three-step process:
1. Indexing: Split documents into fixed-size chunks and store vector embeddings.
2. Retrieval: Compute cosine similarity between the query embedding and chunk vectors to retrieve top-k chunks.
3. Generation: Concatenate chunks into the system prompt and generate a completion.

**Limitations:**
- Low precision: irrelevant chunks pollute the LLM context window.
- Low recall: fails when queries use phrasing different from indexed passages.
- Inability to verify hallucinations or handle queries where no relevant documents exist.

### Advanced RAG
Advanced RAG introduces pre-retrieval and post-retrieval optimizations:
- **Pre-retrieval:** Query rewriting, expansion, and semantic chunking with metadata enrichment.
- **Post-retrieval:** Re-ranking candidate chunks with cross-encoders, and context compression to eliminate noise.

### Modular & Agentic RAG
Agentic RAG models retrieval as an intelligent decision-making process. The system dynamically classifies intent, plans multi-step retrieval strategies, queries multiple indexes in parallel, reflects upon retrieval quality, and validates citations prior to returning the final answer.

---

## 2. Dense Semantic vs Sparse Lexical Retrieval

| Feature | Dense Retrieval (Vector) | Sparse Retrieval (BM25 / Keyword) |
| :--- | :--- | :--- |
| **Matching Mechanism** | High-dimensional embedding distance | Term frequency and inverted document frequency |
| **Strengths** | Handles synonyms, paraphrasing, conceptual questions | Exact matches, acronyms, code identifiers, part numbers |
| **Weaknesses** | Vocabulary mismatch on exact terms, higher compute | Struggles with semantic nuance and paraphrased concepts |
| **Best Used For** | Conceptual understanding and general research | Precise technical IDs, names, and explicit keyword searches |

### The Value of Hybrid Fusion
By combining dense and sparse retrievals via Reciprocal Rank Fusion (RRF), systems avoid the single-point-of-failure inherent to either approach in isolation.

---

## 3. Chunking Strategies and Trade-Offs

1. **Fixed-Size Chunking:** Simple character or token slicing. Prone to splitting sentences and destroying contextual coherence.
2. **Recursive Character Chunking:** Splits hierarchy by paragraphs, then sentences, then words. Balances structure with size boundaries.
3. **Semantic Chunking:** Slices text at shifts in embedding similarity between consecutive sentences.
4. **Document Hierarchy Chunking:** Extracts document headers, preserving section titles and page numbers within metadata payloads.

---

## 4. Evaluation Methodologies

Production RAG evaluation requires both retrieval and generation metrics:
- **Recall@K & Precision@K:** Measure information retrieval coverage and purity.
- **Mean Reciprocal Rank (MRR):** Measures how early the first truly relevant chunk appears.
- **Faithfulness / Groundedness:** Measures whether claims in the generated response are factually supported by retrieved context.
- **Citation Precision:** Measures the fraction of generated citations that accurately link to the underlying source text.

