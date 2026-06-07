import { useCallback, useState, useRef } from "react";
import { Upload, FileText, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { uploadPdf, type UploadResponse } from "@/lib/api";

interface PdfUploadProps {
  onUploadComplete: (data: UploadResponse) => void;
  createConversation?: boolean;
}

type UploadState = "idle" | "dragging" | "uploading" | "success" | "error";

export function PdfUpload({ onUploadComplete, createConversation = true }: PdfUploadProps) {
  const [state, setState] = useState<UploadState>("idle");
  const [fileName, setFileName] = useState("");
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setState("error");
        setError("Only PDF files are accepted.");
        return;
      }
      if (file.size > 20 * 1024 * 1024) {
        setState("error");
        setError("File is too large. Maximum size is 20 MB.");
        return;
      }

      setFileName(file.name);
      setState("uploading");
      setError("");

      try {
        const data = await uploadPdf(file, createConversation);
        setState("success");
        onUploadComplete(data);
        // Reset after a brief success animation
        setTimeout(() => setState("idle"), 2000);
      } catch (err) {
        setState("error");
        setError(err instanceof Error ? err.message : "Upload failed.");
      }
    },
    [onUploadComplete, createConversation],
  );

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setState("idle");
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  function onDragOver(e: React.DragEvent) {
    e.preventDefault();
    setState("dragging");
  }

  function onDragLeave() {
    setState("idle");
  }

  function onFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    // Reset input so the same file can be re-selected
    e.target.value = "";
  }

  return (
    <div
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onClick={() => state !== "uploading" && inputRef.current?.click()}
      className={cn(
        "group relative flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-6 transition-all duration-200",
        state === "dragging" && "border-primary bg-primary/5 scale-[1.02]",
        state === "uploading" && "border-muted cursor-wait",
        state === "success" && "border-green-500/50 bg-green-500/5",
        state === "error" && "border-destructive/50 bg-destructive/5",
        state === "idle" &&
          "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/50",
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        onChange={onFileSelect}
        className="hidden"
      />

      {state === "uploading" && (
        <>
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm font-medium text-foreground">Processing {fileName}…</p>
          <p className="text-xs text-muted-foreground">Extracting text & creating embeddings</p>
        </>
      )}

      {state === "success" && (
        <>
          <CheckCircle className="h-8 w-8 text-green-500" />
          <p className="text-sm font-medium text-green-600 dark:text-green-400">
            {fileName} uploaded successfully!
          </p>
        </>
      )}

      {state === "error" && (
        <>
          <AlertCircle className="h-8 w-8 text-destructive" />
          <p className="text-sm font-medium text-destructive">{error}</p>
          <p className="text-xs text-muted-foreground">Click or drop to try again</p>
        </>
      )}

      {(state === "idle" || state === "dragging") && (
        <>
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted transition-colors group-hover:bg-primary/10">
            {state === "dragging" ? (
              <FileText className="h-6 w-6 text-primary" />
            ) : (
              <Upload className="h-6 w-6 text-muted-foreground group-hover:text-primary transition-colors" />
            )}
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-foreground">
              {state === "dragging" ? "Drop your PDF here" : "Upload PDF"}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Drag & drop or click to browse · Max 20 MB
            </p>
          </div>
        </>
      )}
    </div>
  );
}
