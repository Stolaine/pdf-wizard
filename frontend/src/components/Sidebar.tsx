import { useEffect, useState } from "react";
import {
  getConversations,
  getFiles,
  deleteConversation,
  deleteFile,
  startConversationWithFile,
  cancelFileEmbedding,
  type ConversationSummary,
  type UploadResponse,
  type UploadedFileOut,
} from "@/lib/api";
import { PdfUpload } from "@/components/PdfUpload";
import { cn } from "@/lib/utils";
import { FileText, MessageSquare, Plus, Sparkles, Trash2, MessageSquarePlus, PanelLeftClose, Sun, Moon, Square } from "lucide-react";

interface SidebarProps {
  activeConversationId: string | null;
  onSelectConversation: (conv: ConversationSummary) => void;
  onNewConversation: (data: UploadResponse) => void;
  refreshKey: number;
  onCollapse: () => void;
}

export function Sidebar({
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  refreshKey,
  onCollapse,
}: SidebarProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [files, setFiles] = useState<UploadedFileOut[]>([]);
  const [activeTab, setActiveTab] = useState<"chats" | "files">("chats");
  const [showUpload, setShowUpload] = useState(false);
  const [localRefreshKey, setLocalRefreshKey] = useState(0);

  const [theme, setTheme] = useState<"light" | "dark">(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("theme");
      if (stored === "light" || stored === "dark") return stored;
      if (window.matchMedia("(prefers-color-scheme: light)").matches) {
        return "light";
      }
    }
    return "dark";
  });

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    localStorage.setItem("theme", theme);
  }, [theme]);

  useEffect(() => {
    getConversations()
      .then(setConversations)
      .catch(() => setConversations([]));
    getFiles()
      .then(setFiles)
      .catch(() => setFiles([]));
  }, [refreshKey, localRefreshKey]);

  // Polling loop for pending/processing files
  useEffect(() => {
    const hasPendingOrProcessing = files.some(
      (f) => f.status === "PENDING" || f.status === "PROCESSING"
    );

    if (hasPendingOrProcessing) {
      const interval = setInterval(() => {
        getFiles()
          .then(setFiles)
          .catch(() => {});
        getConversations()
          .then(setConversations)
          .catch(() => {});
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [files]);

  function handleUploadComplete(data: UploadResponse) {
    setShowUpload(false);
    onNewConversation(data);
    setLocalRefreshKey((k) => k + 1);
    setActiveTab("chats"); // Switch to chats to see the active chat
  }

  async function handleDeleteChat(e: React.MouseEvent, id: string) {
    e.stopPropagation();
    try {
      await deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      console.error("Failed to delete conversation:", err);
    }
  }

  async function handleDeleteFile(e: React.MouseEvent, id: string) {
    e.stopPropagation();
    try {
      await deleteFile(id);
      setLocalRefreshKey((k) => k + 1);
    } catch (err) {
      console.error("Failed to delete file:", err);
    }
  }

  async function handleStartChat(e: React.MouseEvent, fileId: string) {
    e.stopPropagation();
    try {
      const newConv = await startConversationWithFile(fileId);
      onNewConversation({
        filename: newConv.pdf_name || "",
        num_chunks: 0,
        collection_name: newConv.collection_name || "",
        conversation_id: newConv.id,
        file_id: fileId,
        message: "New conversation started from existing file",
      });
      setActiveTab("chats");
    } catch (err) {
      console.error("Failed to start new conversation:", err);
    }
  }

  async function handleCancelEmbedding(e: React.MouseEvent, fileId: string) {
    e.stopPropagation();
    try {
      await cancelFileEmbedding(fileId);
      setLocalRefreshKey((k) => k + 1);
    } catch (err) {
      console.error("Failed to cancel embedding:", err);
    }
  }

  return (
    <aside className="flex h-full w-72 flex-col border-r border-border bg-sidebar shrink-0">
      {/* Compact Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3 shrink-0">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary">
            <Sparkles className="h-3.5 w-3.5 text-primary-foreground" />
          </div>
          <span className="text-sm font-bold text-sidebar-foreground">PDF Wizard</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
            className="rounded-lg p-1 text-muted-foreground hover:bg-sidebar-accent hover:text-foreground cursor-pointer transition-colors"
            title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          <button
            onClick={onCollapse}
            className="rounded-lg p-1 text-muted-foreground hover:bg-sidebar-accent hover:text-foreground cursor-pointer transition-colors"
            title="Collapse Sidebar"
          >
            <PanelLeftClose className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Upload button */}
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
          Upload PDF File
        </button>
      </div>

      {/* Upload dropzone */}
      {showUpload && (
        <div className="px-3 pb-3 animate-in slide-in-from-top-2 fade-in-0 duration-200">
          <PdfUpload onUploadComplete={handleUploadComplete} />
        </div>
      )}

      {/* Tabs */}
      <div className="px-3 mb-2 shrink-0">
        <div className="flex rounded-lg bg-muted/50 p-1">
          <button
            onClick={() => setActiveTab("chats")}
            className={cn(
              "flex-1 rounded-md py-1.5 text-xs font-medium transition-all cursor-pointer text-center",
              activeTab === "chats"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            Chats ({conversations.length})
          </button>
          <button
            onClick={() => setActiveTab("files")}
            className={cn(
              "flex-1 rounded-md py-1.5 text-xs font-medium transition-all cursor-pointer text-center",
              activeTab === "files"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            Files ({files.length})
          </button>
        </div>
      </div>

      {/* Navigation List */}
      <div className="flex-1 overflow-y-auto px-3 pb-3 scrollbar-thin scrollbar-thumb-sidebar-border scrollbar-track-transparent">
        {activeTab === "chats" ? (
          conversations.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-8 text-center">
              <MessageSquare className="h-8 w-8 text-muted-foreground/50" />
              <p className="text-xs text-muted-foreground">No conversations yet</p>
            </div>
          ) : (
            <div className="flex flex-col gap-1">
              {conversations.map((conv) => {
                const titleText =
                  conv.files && conv.files.length > 0
                    ? conv.files.map((f) => f.filename).join(", ")
                    : "Empty Chat";

                return (
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
                    <span className="flex-1 truncate" title={titleText}>
                      {titleText}
                    </span>
                    <Trash2
                      className="h-3.5 w-3.5 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100 hover:text-destructive cursor-pointer"
                      onClick={(e) => handleDeleteChat(e, conv.id)}
                    />
                  </button>
                );
              })}
            </div>
          )
        ) : files.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-8 text-center">
            <FileText className="h-8 w-8 text-muted-foreground/50" />
            <p className="text-xs text-muted-foreground">No files uploaded yet</p>
          </div>
        ) : (
          <div className="flex flex-col gap-1">
            {files.map((file) => {
              const isProcessing = file.status === "PENDING" || file.status === "PROCESSING";
              const radius = 6;
              const circumference = 2 * Math.PI * radius;
              const strokeDashoffset = circumference - (file.progress / 100) * circumference;

              return (
                <div
                  key={file.id}
                  className={cn(
                    "group flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm text-sidebar-foreground transition-colors",
                    "hover:bg-sidebar-accent/50",
                  )}
                >
                  {isProcessing ? (
                    <svg className="h-4 w-4 shrink-0 -rotate-90" viewBox="0 0 16 16">
                      <circle
                        cx="8"
                        cy="8"
                        r={radius}
                        className="stroke-muted-foreground/25 fill-none"
                        strokeWidth="2"
                      />
                      <circle
                        cx="8"
                        cy="8"
                        r={radius}
                        className="stroke-primary fill-none transition-all duration-300"
                        strokeWidth="2"
                        strokeDasharray={circumference}
                        strokeDashoffset={strokeDashoffset}
                      />
                    </svg>
                  ) : (
                    <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                  )}
                  <span className="flex-1 truncate" title={file.filename}>
                    {file.filename}
                    {isProcessing && (
                      <span className="ml-1.5 text-[10px] font-mono text-primary font-medium">
                        {file.progress}%
                      </span>
                    )}
                  </span>
                  <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                    {isProcessing ? (
                      <button
                        title="Cancel embedding"
                        className="rounded p-1 hover:bg-sidebar-accent hover:text-destructive cursor-pointer transition-colors"
                        onClick={(e) => handleCancelEmbedding(e, file.id)}
                      >
                        <Square className="h-3 w-3 fill-current" />
                      </button>
                    ) : (
                      <>
                        <button
                          title="Start new chat"
                          className="rounded p-1 hover:bg-sidebar-accent hover:text-primary cursor-pointer transition-colors"
                          onClick={(e) => handleStartChat(e, file.id)}
                        >
                          <MessageSquarePlus className="h-3.5 w-3.5" />
                        </button>
                        <button
                          title="Delete file"
                          className="rounded p-1 hover:bg-sidebar-accent hover:text-destructive cursor-pointer transition-colors"
                          onClick={(e) => handleDeleteFile(e, file.id)}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-border px-4 py-3 shrink-0">
        <p className="text-[10px] text-muted-foreground/60 text-center">
          Powered by Gemini + LangChain
        </p>
      </div>
    </aside>
  );
}
