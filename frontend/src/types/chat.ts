export interface ChatFilters {
  doc_types: string[];
  enable_web_search?: boolean | null;
}

export interface ChatAskRequest {
  session_id: string;
  question: string;
  filters: ChatFilters;
}

export interface SourceItem {
  chunk_id?: string | null;
  doc_id?: string | null;
  doc_name: string;
  doc_type: string;
  page?: number | null;
  section?: string | null;
  excerpt: string;
  score?: number | null;
  url?: string | null;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceItem[] | null;
  created_at: string;
}

export interface ChatSessionSummary {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionCreateRequest {
  session_id?: string;
  title?: string;
}

export interface RetrievalCandidate {
  chunk_id: string;
  text: string;
  doc_name: string;
  doc_type: string;
  page?: number | null;
  section?: string | null;
  dense_score?: number | null;
  sparse_score?: number | null;
  fused_score?: number | null;
  rerank_score?: number | null;
}

export interface ChatDebugResponse {
  original_query: string;
  rewritten_query: string;
  grounded: boolean;
  prompt_preview: string;
  dense_candidates: RetrievalCandidate[];
  sparse_candidates: RetrievalCandidate[];
  fused_candidates: RetrievalCandidate[];
  reranked_candidates: RetrievalCandidate[];
  selected_sources: SourceItem[];
  memories: string[];
  web_results: SourceItem[];
}

export interface ChatSessionDeleteResponse {
  session_id: string;
  deleted_messages: number;
  deleted_retrieval_logs: number;
  deleted_memories: number;
}

export interface MemoryItem {
  id: string;
  session_id: string;
  content: string;
  memory_type: string;
  metadata: Record<string, unknown>;
  usage_count: number;
  last_used_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface MemorySearchResponse {
  items: MemoryItem[];
}

export interface MemoryDeleteResponse {
  session_id: string;
  deleted: number;
}

export interface LocalSessionSummary {
  id: string;
  title: string;
  updatedAt: string;
  createdAt?: string;
  messageCount?: number;
}
