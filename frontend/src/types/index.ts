export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  content_hash: string;
  status: "pending" | "processing" | "indexed" | "failed";
  error_message?: string;
  chunk_count: number;
  doc_metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  token_count: number;
  page_number?: number;
  section?: string;
  source: string;
  char_offset_start?: number;
  char_offset_end?: number;
  similarity_score?: number;
  rerank_score?: number;
  chunk_metadata: Record<string, any>;
  created_at: string;
}

export interface DocumentDetail extends Document {
  chunks: DocumentChunk[];
}

export interface Citation {
  id: string;
  document_id: string;
  filename: string;
  page?: number;
  chunk_id: string;
  relevance_score: number;
  text: string;
}

export interface WorkflowStep {
  step: string;
  name: string;
  status: "pending" | "running" | "completed" | "skipped" | "failed";
  latency_ms: number;
  details: Record<string, any>;
}

export interface LatencyBreakdown {
  query_analysis_ms: number;
  retrieval_ms: number;
  rerank_ms: number;
  llm_generation_ms: number;
  verification_ms: number;
  total_ms: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations?: Citation[];
  routing_strategy?: string;
  latency_ms?: number;
  msg_metadata?: Record<string, any>;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  messages?: Message[];
}

export interface RecentQuery {
  id: string;
  query: string;
  strategy: string;
  retrieval_latency_ms: number;
  rerank_latency_ms: number;
  total_latency_ms: number;
  chunk_count: number;
  created_at: string;
}

export interface StrategyCount {
  strategy: string;
  count: number;
}

export interface SystemStats {
  document_count: number;
  indexed_chunks_count: number;
  total_queries: number;
  avg_latency_ms: number;
  avg_retrieval_latency_ms: number;
  avg_llm_latency_ms: number;
  vector_store_status: string;
  reranker_status: string;
  llm_provider: string;
  embedding_model: string;
  recent_queries: RecentQuery[];
  strategy_distribution: StrategyCount[];
}

export interface MetricScore {
  name: string;
  score: number;
  description: string;
}

export interface EvaluationRun {
  id: string;
  run_name: string;
  dataset_size: number;
  metrics: Record<string, number>;
  detailed_metrics: MetricScore[];
  report_markdown?: string;
  created_at: string;
}

export interface SearchResultItem {
  chunk_id: string;
  document_id: string;
  filename: string;
  page?: number;
  content: string;
  score: number;
  retrieval_type: string;
}

export interface SearchResponse {
  query: string;
  total_results: number;
  latency_ms: number;
  results: SearchResultItem[];
}

