import { useState, useRef, type KeyboardEvent } from "react";
import { Send } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = "Ask a question about your PDF…",
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleSend() {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    // Reset height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleInput() {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
    }
  }

  return (
    <div className="flex items-end gap-2 rounded-2xl border border-border bg-card p-2 shadow-sm transition-colors focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/20">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onInput={handleInput}
        disabled={disabled}
        placeholder={placeholder}
        rows={1}
        className={cn(
          "flex-1 resize-none bg-transparent px-2 py-2 text-sm outline-none placeholder:text-muted-foreground",
          "scrollbar-thin scrollbar-thumb-muted scrollbar-track-transparent",
          disabled && "opacity-50 cursor-not-allowed",
        )}
      />
      <button
        onClick={handleSend}
        disabled={disabled || !value.trim()}
        className={cn(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl transition-all duration-200",
          value.trim() && !disabled
            ? "bg-primary text-primary-foreground hover:opacity-90 cursor-pointer"
            : "bg-muted text-muted-foreground cursor-not-allowed",
        )}
      >
        <Send className="h-4 w-4" />
      </button>
    </div>
  );
}
