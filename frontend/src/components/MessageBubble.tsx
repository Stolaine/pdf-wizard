import { cn } from "@/lib/utils";
import { Bot, User } from "lucide-react";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  isNew?: boolean;
}

export function MessageBubble({ role, content, isNew = false }: MessageBubbleProps) {
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
