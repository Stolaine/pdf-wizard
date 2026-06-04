import { cn } from "@/lib/utils";
import { Bot, User } from "lucide-react";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  thinking?: string;
  isNew?: boolean;
}

export function MessageBubble({ role, content, thinking, isNew = false }: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div
      className={cn(
        "flex gap-3 max-w-[85%] animate-in fade-in-0 slide-in-from-bottom-2 duration-300",
        isUser ? "ml-auto flex-row-reverse" : "mr-auto",
      )}
      style={isNew ? { animationDelay: "50ms" } : undefined}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-muted-foreground",
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Bubble */}
      <div
        className={cn(
          "rounded-2xl px-4 py-3 text-sm leading-relaxed",
          isUser
            ? "bg-primary text-primary-foreground rounded-br-md"
            : "bg-muted text-foreground rounded-bl-md",
        )}
      >
        {/* Thinking block if present */}
        {!isUser && thinking && (
          <details className="group mb-2 border-l-2 border-primary/30 pl-3 text-xs text-muted-foreground select-none cursor-pointer">
            <summary className="font-semibold outline-none hover:text-foreground transition-colors py-1 flex items-center gap-1 list-none [&::-webkit-details-marker]:hidden">
              <span className="inline-block transition-transform duration-200 group-open:rotate-90 text-[10px]">▶</span>
              <span>Thinking Process</span>
            </summary>
            <div className="mt-2 pl-1 font-normal text-muted-foreground/80 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto border-t border-muted/55 pt-2 select-text cursor-auto scrollbar-thin">
              {thinking}
            </div>
          </details>
        )}

        {/* Render line breaks */}
        {content.split("\n").map((line, i) => (
          <span key={i}>
            {line}
            {i < content.split("\n").length - 1 && <br />}
          </span>
        ))}
      </div>
    </div>
  );
}
