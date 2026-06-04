import { useEffect, useState } from "react";
import {
  getConversations,
  type ConversationSummary,
  type UploadResponse,
} from "@/lib/api";
import { PdfUpload } from "@/components/PdfUpload";
import { cn } from "@/lib/utils";
import { FileText, MessageSquare, Plus, Sparkles, Trash2 } from "lucide-react";
import { deleteConversation } from "@/lib/api";

interface SidebarProps {
  activeConversationId: string | null;
  onSelectConversation: (conv: ConversationSummary) => void;
  onNewConversation: (data: UploadResponse) => void;
  refreshKey: number; // bump this to re-fetch conversations
}

export function Sidebar({
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  refreshKey,
}: SidebarProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [showUpload, setShowUpload] = useState(false);

  useEffect(() => {
    getConversations()
      .then(setConversations)
      .catch(() => setConversations([]));
  }, [refreshKey]);

  function handleUploadComplete(data: UploadResponse) {
    setShowUpload(false);
    onNewConversation(data);
  }

  async function handleDelete(e: React.MouseEvent, id: string) {
    e.stopPropagation();
    try {
      await deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
    } catch {
      // silently fail
    }
  }

  return (
    <aside className="flex h-full w-72 flex-col border-r border-border bg-sidebar">
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-border px-4 py-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
          <Sparkles className="h-4 w-4 text-primary-foreground" />
        </div>
        <h1 className="text-base font-semibold text-sidebar-foreground">PDF Wizard</h1>
      </div>

      {/* New chat button */}
      <div className="p-3">
        <button
          onClick={() => setShowUpload((v) => !v)}
          className={cn(
            "flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors cursor-pointer",
            "border border-dashed border-sidebar-border",
            "text-sidebar-foreground hover:bg-sidebar-accent",
          )}
        >
          <Plus className="h-4 w-4" />
          New Chat
        </button>
      </div>

      {/* Upload area (collapsible) */}
      {showUpload && (
        <div className="px-3 pb-3 animate-in slide-in-from-top-2 fade-in-0 duration-200">
          <PdfUpload onUploadComplete={handleUploadComplete} />
        </div>
      )}

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto px-3 pb-3 scrollbar-thin scrollbar-thumb-sidebar-border scrollbar-track-transparent">
        {conversations.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-8 text-center">
            <FileText className="h-8 w-8 text-muted-foreground/50" />
            <p className="text-xs text-muted-foreground">No conversations yet</p>
          </div>
        ) : (
          <div className="flex flex-col gap-1">
            <p className="px-2 pb-1 pt-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Recent
            </p>
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => onSelectConversation(conv)}
                className={cn(
                  "group flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm transition-colors cursor-pointer",
                  activeConversationId === conv.id
                    ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/50",
                )}
              >
                <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" />
                <span className="flex-1 truncate">{conv.pdf_name}</span>
                <Trash2
                  className="h-3.5 w-3.5 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100 hover:text-destructive"
                  onClick={(e) => handleDelete(e, conv.id)}
                />
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-border px-4 py-3">
        <p className="text-[10px] text-muted-foreground/60 text-center">
          Powered by Gemini + LangChain
        </p>
      </div>
    </aside>
  );
}
