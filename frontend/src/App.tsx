import { useState, useCallback } from "react";
import { Sidebar } from "@/components/Sidebar";
import { ChatWindow } from "@/components/ChatWindow";
import { ChatInput } from "@/components/ChatInput";
import {
  getConversation,
  queryPdf,
  type ConversationSummary,
  type MessageOut,
  type UploadResponse,
} from "@/lib/api";

export default function App() {
  // ── State ────────────────────────────────────────────────────────────
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [collectionName, setCollectionName] = useState<string | null>(null);
  const [pdfName, setPdfName] = useState<string | undefined>();
  const [messages, setMessages] = useState<MessageOut[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  // ── Handlers ─────────────────────────────────────────────────────────

  /** Called when a new PDF is uploaded */
  const handleNewConversation = useCallback((data: UploadResponse) => {
    setConversationId(data.conversation_id);
    setCollectionName(data.collection_name);
    setPdfName(data.filename);
    setMessages([]);
    setRefreshKey((k) => k + 1);
  }, []);

  /** Called when user clicks a conversation in the sidebar */
  const handleSelectConversation = useCallback(async (conv: ConversationSummary) => {
    setConversationId(conv.id);
    setCollectionName(conv.collection_name);
    setPdfName(conv.pdf_name);
    try {
      const detail = await getConversation(conv.id);
      setMessages(detail.messages);
    } catch {
      setMessages([]);
    }
  }, []);

  /** Called when user sends a question */
  const handleSend = useCallback(
    async (question: string) => {
      if (!conversationId || !collectionName) return;

      // Optimistically add user message
      const userMsg: MessageOut = {
        id: Date.now(),
        role: "user",
        content: question,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      try {
        const res = await queryPdf(question, conversationId, collectionName);
        const assistantMsg: MessageOut = {
          id: Date.now() + 1,
          role: "assistant",
          content: res.answer,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err) {
        const errorMsg: MessageOut = {
          id: Date.now() + 1,
          role: "assistant",
          content: `Sorry, something went wrong: ${err instanceof Error ? err.message : "Unknown error"}`,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setIsLoading(false);
      }
    },
    [conversationId, collectionName],
  );

  // ── Render ───────────────────────────────────────────────────────────

  return (
    <div className="flex h-screen w-full bg-background">
      {/* Sidebar */}
      <Sidebar
        activeConversationId={conversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        refreshKey={refreshKey}
      />

      {/* Main content */}
      <main className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        {pdfName && (
          <header className="flex items-center gap-2 border-b border-border px-6 py-3">
            <span className="text-sm font-medium text-foreground">{pdfName}</span>
            <span className="text-xs text-muted-foreground">·</span>
            <span className="text-xs text-muted-foreground">
              Ask questions about this document
            </span>
          </header>
        )}

        {/* Chat area */}
        <ChatWindow messages={messages} isLoading={isLoading} pdfName={pdfName} />

        {/* Input (only visible when a conversation is active) */}
        {conversationId && (
          <div className="border-t border-border bg-background px-4 py-3">
            <div className="mx-auto max-w-3xl">
              <ChatInput onSend={handleSend} disabled={isLoading} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
