# AI Systems Engineering & Production RAG Operations

## 1. LLM Serving and Latency Economics

Deploying production AI applications requires careful optimization of latency and cost metrics:
- **Time-to-First-Token (TTFT):** The duration from request dispatch until the first token streams to the client. TTFT is dominated by retrieval latency, prompt token length, and model prefill computation.
- **Inter-Token Latency (ITL):** The speed of subsequent token generation during autoregressive decoding.
- **Context Window Saturation:** Stuffing excessive irrelevant chunks into the prompt degrades LLM reasoning ("lost in the middle" phenomenon) and linearly inflates inference costs.

## 2. Streaming Architecture: Server-Sent Events (SSE)

For agentic applications where pipeline execution spans multiple stages (Query Analysis -> Hybrid Retrieval -> Reranking -> LLM Generation), streaming provides superior UX:
- **SSE vs WebSockets:** Server-Sent Events use unidirectional HTTP streaming over standard port 80/443. Unlike WebSockets, SSE works cleanly through enterprise proxies, CDNs, and load balancers, with automatic reconnection and native browser EventSource support.
- **Workflow Stepper Events:** NexusRAG emits lifecycle events before token streaming starts (`analyzing`, `retrieving`, `reranked`), giving users instant visibility into the agent's thought process.

## 3. Production Grounding and Guardrails

Unchecked LLMs frequently produce hallucinated references or false answers when knowledge bases lack relevant material. Production guardrails must implement:
1. Retrieval threshold gating: reject queries with low top-k similarity scores before calling LLMs.
2. Grounding verification: compare generated assertions against retrieved text using token overlap or secondary NLI evaluation.
3. Strict refusal policies: train prompts to politely refuse ungrounded questions instead of guessing.

