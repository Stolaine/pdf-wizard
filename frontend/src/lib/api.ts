/**
 * API client for communicating with the FastAPI backend.
 * In development, requests are proxied by Vite to localhost:8000.
 */

const BASE = "/api";

// ── Types ──────────────────────────────────────────────────────────────────

export interface UploadResponse {
  filename: string;
  num_chunks: number;
  collection_name: string;
  conversation_id: string;
  file_id: string;
  message: string;
}

export interface UploadedFileOut {
  id: string;
  filename: string;
  collection_name: string;
  num_chunks: number;
  created_at: string;
  file_size: number;
  num_pages: number;
  chunk_size: number;
  overlap_size: number;
  vector_size?: number | null;
  embedding_model?: string | null;
  time_taken?: number | null;
  embedding_start_time?: string | null;
  embedding_end_time?: string | null;
  status: string;
  progress: number;
}

export interface SourceChunk {
  content: string;
  page: number | null;
}

export interface QueryResponse {
  answer: string;
  conversation_id: string;
  sources: SourceChunk[];
  thinking?: string;
}

export interface MessageOut {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  thinking?: string;
}

export interface ConversationSummary {
  id: string;
  title: string;
  pdf_name?: string;
  collection_name?: string;
  created_at: string;
  files: UploadedFileOut[];
}

export interface ConversationDetail extends ConversationSummary {
  messages: MessageOut[];
}

// ── Helpers ────────────────────────────────────────────────────────────────

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

// ── API functions ──────────────────────────────────────────────────────────

export async function uploadPdf(file: File, createConversation: boolean = true): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  return request<UploadResponse>(`${BASE}/upload?create_conversation=${createConversation}`, {
    method: "POST",
    body: form,
  });
}

export async function queryPdf(
  question: string,
  conversationId: string,
): Promise<QueryResponse> {
  return request<QueryResponse>(`${BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      conversation_id: conversationId,
    }),
  });
}

export async function getConversations(): Promise<ConversationSummary[]> {
  return request<ConversationSummary[]>(`${BASE}/conversations`);
}

export async function getConversation(id: string): Promise<ConversationDetail> {
  return request<ConversationDetail>(`${BASE}/conversations/${id}`);
}

export async function deleteConversation(id: string): Promise<void> {
  await request(`${BASE}/conversations/${id}`, { method: "DELETE" });
}

export async function getFiles(): Promise<UploadedFileOut[]> {
  return request<UploadedFileOut[]>(`${BASE}/files`);
}

export async function deleteFile(id: string): Promise<void> {
  await request(`${BASE}/files/${id}`, { method: "DELETE" });
}

export async function startConversationWithFile(fileId: string): Promise<ConversationSummary> {
  return request<ConversationSummary>(`${BASE}/files/${fileId}/conversations`, {
    method: "POST",
  });
}

export async function addFileToConversation(
  conversationId: string,
  fileId: string,
): Promise<ConversationSummary> {
  return request<ConversationSummary>(`${BASE}/conversations/${conversationId}/files/${fileId}`, {
    method: "POST",
  });
}

export async function healthCheck(): Promise<{ status: string }> {
  return request<{ status: string }>(`${BASE}/health`);
}

export async function cancelFileEmbedding(fileId: string): Promise<void> {
  await request(`${BASE}/files/${fileId}/cancel`, { method: "POST" });
}

export async function createBlankConversation(): Promise<ConversationSummary> {
  return request<ConversationSummary>(`${BASE}/conversations`, { method: "POST" });
}

export async function renameConversation(id: string, title: string): Promise<ConversationSummary> {
  return request<ConversationSummary>(`${BASE}/conversations/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
}

export interface CollectionMetric {
  name: string;
  count: number;
}

export interface DatabaseMetricsResponse {
  total_files: number;
  total_file_size_bytes: number;
  total_conversations: number;
  total_messages: number;
  status_counts: Record<string, number>;
  chroma_collections: CollectionMetric[];
  files: UploadedFileOut[];
}

export async function getDatabaseMetrics(): Promise<DatabaseMetricsResponse> {
  return request<DatabaseMetricsResponse>(`${BASE}/metrics`);
}
