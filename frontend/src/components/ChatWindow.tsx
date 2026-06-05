import { useEffect, useRef, useState } from "react";
import { MessageBubble } from "@/components/MessageBubble";
import { Loader } from "@/components/Loader";
import { PdfUpload } from "@/components/PdfUpload";
import {
  getFiles,
  addFileToConversation,
  type MessageOut,
  type UploadedFileOut,
  type UploadResponse,
} from "@/lib/api";
import { FileText, Plus, X, Link as LinkIcon, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";


interface ChatWindowProps {
  messages: MessageOut[];
  isLoading?: boolean;
  activeFiles: UploadedFileOut[];
  conversationId: string | null;
  onUpdateActiveFiles: (files: UploadedFileOut[]) => void;
  onNewConversation: (data: UploadResponse) => void;
}

export function ChatWindow({
  messages,
  isLoading = false,
  activeFiles,
  conversationId,
  onUpdateActiveFiles,
  onNewConversation,
}: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [availableFiles, setAvailableFiles] = useState<UploadedFileOut[]>([]);
  const [modalMode, setModalMode] = useState<"existing" | "upload">("existing");

  // Auto-scroll on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Fetch available files (filtering out files already in context) when modal opens
  useEffect(() => {
    if (showAddModal && conversationId) {
      getFiles()
        .then((allFiles) => {
          const filtered = allFiles.filter(
            (f) => !activeFiles.some((af) => af.id === f.id)
          );
          setAvailableFiles(filtered);
        })
        .catch(() => setAvailableFiles([]));
    }
  }, [showAddModal, conversationId, activeFiles]);

  async function handleLinkFile(fileId: string) {
    if (!conversationId) return;
    try {
      const updatedConv = await addFileToConversation(conversationId, fileId);
      onUpdateActiveFiles(updatedConv.files || []);
      setShowAddModal(false);
    } catch (err) {
      console.error("Failed to link file:", err);
    }
  }

  async function handleNewUploadComplete(data: UploadResponse) {
    if (conversationId) {
      try {
        // Associate newly uploaded file with ongoing chat
        const updatedConv = await addFileToConversation(conversationId, data.file_id);
        onUpdateActiveFiles(updatedConv.files || []);
        setShowAddModal(false);
      } catch (err) {
        console.error("Failed to link uploaded file:", err);
      }
    } else {
      // If no conversation active, trigger starting a new conversation
      onNewConversation(data);
    }
  }

  // ── Render Empty / Inactive State ─────────────────────────────────────
  if (!conversationId) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-6 px-4 py-12 text-center max-w-lg mx-auto overflow-y-auto">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
          <Sparkles className="h-7 w-7" />
        </div>
        <div>
          <h3 className="text-xl font-bold text-foreground">Welcome to PDF Wizard</h3>
          <p className="mt-2 text-sm text-muted-foreground max-w-sm mx-auto">
            Upload a new PDF document or select an existing chat to begin extracting insights and answering questions.
          </p>
        </div>
        <div className="w-full max-w-md border border-border rounded-xl p-4 bg-muted/10 shadow-sm">
          <PdfUpload onUploadComplete={handleNewUploadComplete} />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden relative">
      {/* Pinned Context Files Bar */}
      <div className="flex items-center justify-between border-b border-border bg-muted/10 px-6 py-2.5 shrink-0 flex-wrap gap-2">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mr-1 select-none">
            Context Documents:
          </span>
          {activeFiles.length === 0 ? (
            <span className="text-xs text-muted-foreground italic">No PDF files linked yet</span>
          ) : (
            activeFiles.map((file) => (
              <div
                key={file.id}
                className="flex items-center gap-1 rounded bg-muted/80 hover:bg-muted border border-border px-2 py-0.5 text-xs text-foreground transition-colors"
              >
                <FileText className="h-3 w-3 text-muted-foreground shrink-0" />
                <span className="max-w-[150px] truncate" title={file.filename}>
                  {file.filename}
                </span>
              </div>
            ))
          )}
        </div>

        <button
          onClick={() => {
            setModalMode("existing");
            setShowAddModal(true);
          }}
          className="flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 cursor-pointer transition-colors shadow-sm"
        >
          <Plus className="h-3 w-3" />
          Add Context
        </button>
      </div>

      {/* Message Bubbles Area */}
      <div className="flex-1 overflow-y-auto px-6 py-6 scrollbar-thin scrollbar-thumb-muted scrollbar-track-transparent">
        {messages.length === 0 && !isLoading ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
              <FileText className="h-6 w-6 text-muted-foreground" />
            </div>
            <h4 className="text-sm font-semibold text-foreground">Ready to Chat</h4>
            <p className="text-xs text-muted-foreground max-w-xs">
              Type your first question below to extract answers and explore the context documents.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                role={msg.role}
                content={msg.content}
                thinking={msg.thinking}
              />
            ))}
            {isLoading && (
              <div className="mr-auto">
                <Loader />
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Add Context Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-in fade-in-0 duration-200">
          <div className="relative w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg flex flex-col gap-4">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-base font-bold text-foreground">Add Context Document</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="rounded-lg p-1 text-muted-foreground hover:bg-muted hover:text-foreground cursor-pointer transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Mode Selector */}
            <div className="flex rounded-lg bg-muted p-1">
              <button
                onClick={() => setModalMode("existing")}
                className={cn(
                  "flex-1 rounded-md py-1.5 text-xs font-semibold transition-all cursor-pointer text-center",
                  modalMode === "existing"
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                Link Existing File
              </button>
              <button
                onClick={() => setModalMode("upload")}
                className={cn(
                  "flex-1 rounded-md py-1.5 text-xs font-semibold transition-all cursor-pointer text-center",
                  modalMode === "upload"
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                Upload New File
              </button>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto max-h-[300px]">
              {modalMode === "existing" ? (
                availableFiles.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-8 text-center">
                    <FileText className="h-8 w-8 text-muted-foreground/40 mb-2" />
                    <p className="text-xs text-muted-foreground max-w-[200px]">
                      No other uploaded files are available to link.
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col gap-1.5">
                    {availableFiles.map((file) => (
                      <div
                        key={file.id}
                        className="flex items-center justify-between gap-3 rounded-lg border border-border bg-muted/20 px-3 py-2.5 transition-colors hover:bg-muted/40"
                      >
                        <div className="flex items-center gap-2 overflow-hidden">
                          <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                          <span className="text-xs font-medium text-foreground truncate" title={file.filename}>
                            {file.filename}
                          </span>
                        </div>
                        <button
                          onClick={() => handleLinkFile(file.id)}
                          className="flex items-center gap-1 rounded bg-primary px-2.5 py-1 text-[11px] font-semibold text-primary-foreground hover:bg-primary/95 cursor-pointer transition-colors"
                        >
                          <LinkIcon className="h-3 w-3" />
                          Link
                        </button>
                      </div>
                    ))}
                  </div>
                )
              ) : (
                <div className="py-2">
                  <PdfUpload onUploadComplete={handleNewUploadComplete} />
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
