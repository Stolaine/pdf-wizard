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
  message: string;
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
  pdf_name: string;
  collection_name: string;
  created_at: string;
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

export async function uploadPdf(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  return request<UploadResponse>(`${BASE}/upload`, {
    method: "POST",
    body: form,
  });
}

export async function queryPdf(
  question: string,
  conversationId: string,
  collectionName: string,
): Promise<QueryResponse> {
  return request<QueryResponse>(`${BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      conversation_id: conversationId,
      collection_name: collectionName,
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

export async function healthCheck(): Promise<{ status: string }> {
  return request<{ status: string }>(`${BASE}/health`);
}
