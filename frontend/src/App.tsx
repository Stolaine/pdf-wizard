import { useState, useCallback } from "react";
import { Sidebar } from "@/components/Sidebar";
import { ChatWindow } from "@/components/ChatWindow";
import { ChatInput } from "@/components/ChatInput";
import { Menu } from "lucide-react";
import {
  getConversation,
  queryPdf,
  type ConversationSummary,
  type MessageOut,
  type UploadResponse,
  type UploadedFileOut,
} from "@/lib/api";

export default function App() {
  // ── State ────────────────────────────────────────────────────────────
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [activeFiles, setActiveFiles] = useState<UploadedFileOut[]>([]);
  const [messages, setMessages] = useState<MessageOut[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // ── Handlers ─────────────────────────────────────────────────────────

  /** Called when a new PDF is uploaded or new chat is started */
  const handleNewConversation = useCallback((data: UploadResponse) => {
    setConversationId(data.conversation_id);
    setMessages([]);
    setRefreshKey((k) => k + 1);
    
    // Fetch conversation detail to load the files list automatically
    getConversation(data.conversation_id)
      .then((detail) => {
        setActiveFiles(detail.files || []);
      })
      .catch(() => {
        setActiveFiles([]);
      });
  }, []);

  /** Called when user clicks a conversation in the sidebar */
  const handleSelectConversation = useCallback(async (conv: ConversationSummary) => {
    setConversationId(conv.id);
    setActiveFiles(conv.files || []);
    setMessages([]);
    try {
      const detail = await getConversation(conv.id);
      setMessages(detail.messages);
      setActiveFiles(detail.files || []);
    } catch {
      setMessages([]);
    }
  }, []);

  /** Called when context files of the active chat are updated */
  const handleUpdateActiveFiles = useCallback((updatedFiles: UploadedFileOut[]) => {
    setActiveFiles(updatedFiles);
    setRefreshKey((k) => k + 1); // trigger sidebar update
  }, []);

  /** Called when user sends a question */
  const handleSend = useCallback(
    async (question: string) => {
      if (!conversationId) return;

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
        const res = await queryPdf(question, conversationId);
        const assistantMsg: MessageOut = {
          id: Date.now() + 1,
          role: "assistant",
          content: res.answer,
          thinking: res.thinking,
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
    [conversationId],
  );

  // ── Render ───────────────────────────────────────────────────────────

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden">
      {/* Sidebar */}
      {isSidebarOpen && (
        <Sidebar
          activeConversationId={conversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          refreshKey={refreshKey}
          onCollapse={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <main className="flex flex-1 flex-col overflow-hidden relative">
        {/* Header (with Sidebar Toggle and context display) */}
        <header className="flex items-center gap-4 px-6 py-3 shrink-0">
          {!isSidebarOpen && (
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground cursor-pointer transition-colors"
              title="Open Sidebar"
            >
              <Menu className="h-5 w-5" />
            </button>
          )}
          
          <div className="flex items-center gap-2 overflow-hidden">
            <span className="text-sm font-semibold text-foreground truncate">
              {conversationId 
                ? (activeFiles.length > 0 
                    ? `Chat about ${activeFiles.map(f => f.filename).join(", ")}` 
                    : "Empty Chat") 
                : ""}
            </span>
          </div>
        </header>

        {/* Chat area (lists active files and Add Context UI internally) */}
        <ChatWindow 
          messages={messages} 
          isLoading={isLoading} 
          activeFiles={activeFiles}
          conversationId={conversationId}
          onUpdateActiveFiles={handleUpdateActiveFiles}
          onNewConversation={handleNewConversation}
        />

        {/* Input (only visible when a conversation is active) */}
        {conversationId && (
          <div className="border-t border-border bg-background px-4 py-3 shrink-0">
            <div className="mx-auto max-w-3xl">
              <ChatInput onSend={handleSend} disabled={isLoading} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
