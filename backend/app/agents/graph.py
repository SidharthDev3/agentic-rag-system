import time
from typing import Any, Dict, List, Optional
from langgraph.graph import END, StateGraph
from app.agents.nodes.citation_verifier import citation_verifier_node
from app.agents.nodes.context_compressor import context_compressor_node
from app.agents.nodes.generator import answer_generator_node
from app.agents.nodes.grounding_checker import grounding_checker_node
from app.agents.nodes.hybrid_retriever import hybrid_retriever_node
from app.agents.nodes.query_analyzer import query_analyzer_node
from app.agents.nodes.query_rewriter import query_rewriter_node
from app.agents.nodes.reranker import reranker_node
from app.agents.nodes.retrieval_planner import retrieval_planner_node
from app.agents.state import AgentState
from app.core.logging import logger
from app.schemas.chat import ChatResponse, LatencyBreakdown


def route_after_analysis(state: AgentState) -> str:
    """Conditional router based on query analysis."""
    if not state.get("needs_retrieval", True):
        # Skip retrieval and jump straight to answer generation / direct response
        return "generator"
    return "query_rewriter"


def build_nexusrag_graph():
    """Builds and compiles the full LangGraph Agentic RAG workflow."""
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("query_analyzer", query_analyzer_node)
    workflow.add_node("query_rewriter", query_rewriter_node)
    workflow.add_node("retrieval_planner", retrieval_planner_node)
    workflow.add_node("hybrid_retriever", hybrid_retriever_node)
    workflow.add_node("reranker", reranker_node)
    workflow.add_node("context_compressor", context_compressor_node)
    workflow.add_node("generator", answer_generator_node)
    workflow.add_node("citation_verifier", citation_verifier_node)
    workflow.add_node("grounding_checker", grounding_checker_node)

    # Set Entry Point
    workflow.set_entry_point("query_analyzer")

    # Conditional Routing from query_analyzer
    workflow.add_conditional_edges(
        "query_analyzer",
        route_after_analysis,
        {
            "generator": "generator",
            "query_rewriter": "query_rewriter",
        },
    )

    # Linear workflow for retrieval branch
    workflow.add_edge("query_rewriter", "retrieval_planner")
    workflow.add_edge("retrieval_planner", "hybrid_retriever")
    workflow.add_edge("hybrid_retriever", "reranker")
    workflow.add_edge("reranker", "context_compressor")
    workflow.add_edge("context_compressor", "generator")
    workflow.add_edge("generator", "citation_verifier")
    workflow.add_edge("citation_verifier", "grounding_checker")
    workflow.add_edge("grounding_checker", END)

    return workflow.compile()


nexusrag_graph = build_nexusrag_graph()


async def run_agentic_rag(
    query: str,
    conversation_id: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    top_k: int = 5,
    use_reranker: bool = True,
    strategy_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes the agentic RAG workflow over the state graph.
    Returns the completed AgentState.
    """
    start_total = time.perf_counter()

    initial_state: AgentState = {
        "query": query,
        "conversation_id": conversation_id,
        "conversation_history": conversation_history or [],
        "top_k": top_k,
        "use_reranker": use_reranker,
        "strategy_override": strategy_override,
        "classification": "factual",
        "needs_retrieval": True,
        "entities": [],
        "rewritten_queries": [query],
        "retrieval_strategy": "single_hop_hybrid",
        "retrieved_chunks": [],
        "reranked_chunks": [],
        "compressed_context": "",
        "raw_answer": "",
        "answer": "",
        "citations": [],
        "is_grounded": True,
        "grounding_score": 1.0,
        "grounding_explanation": None,
        "workflow_steps": [],
        "query_analysis_ms": 0.0,
        "retrieval_ms": 0.0,
        "rerank_ms": 0.0,
        "llm_generation_ms": 0.0,
        "verification_ms": 0.0,
        "total_latency_ms": 0.0,
        "error": None,
    }

    final_state = await nexusrag_graph.ainvoke(initial_state)
    total_ms = (time.perf_counter() - start_total) * 1000
    final_state["total_latency_ms"] = round(total_ms, 2)

    return final_state

