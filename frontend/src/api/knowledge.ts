import type { DocumentItem, DocumentListResponse, DocType, KnowledgeStatsResponse } from "../types/knowledge";
import { apiClient, unwrapResponse } from "./client";

export async function fetchDocuments(params: {
  page?: number;
  page_size?: number;
  doc_type?: string;
}): Promise<DocumentListResponse> {
  return unwrapResponse(apiClient.get("/knowledge/documents", { params }));
}

export async function uploadDocument(file: File, docType: DocType): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("doc_type", docType);
  return unwrapResponse(
    apiClient.post("/knowledge/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data"
      }
    })
  );
}

export async function deleteDocument(documentId: string): Promise<{ id: string }> {
  return unwrapResponse(apiClient.delete(`/knowledge/documents/${documentId}`));
}

export async function reindexDocument(documentId: string): Promise<{ id: string; status: string }> {
  return unwrapResponse(apiClient.post(`/knowledge/documents/${documentId}/reindex`));
}

export async function fetchKnowledgeStats(): Promise<KnowledgeStatsResponse> {
  return unwrapResponse(apiClient.get("/knowledge/stats"));
}

