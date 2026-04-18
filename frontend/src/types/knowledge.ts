import type { PaginatedData } from "./common";

export type DocType = "policy" | "manual" | "ticket" | "case";
export type IngestStatus = "PENDING" | "PROCESSING" | "DONE" | "FAILED";

export interface DocumentItem {
  id: string;
  name: string;
  doc_type: DocType;
  file_path: string;
  file_size: number;
  status: IngestStatus;
  chunk_count: number;
  error_msg?: string | null;
  uploaded_by: string;
  created_at: string;
  updated_at: string;
  processed_at?: string | null;
}

export interface KnowledgeStatsResponse {
  total_documents: number;
  total_chunks: number;
  by_type: Array<{
    name: string;
    value: number;
  }>;
  processing_documents: number;
}

export type DocumentListResponse = PaginatedData<DocumentItem>;

