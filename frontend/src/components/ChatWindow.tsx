import { useEffect, useRef } from "react";
import { MessageBubble } from "@/components/MessageBubble";
import { Loader } from "@/components/Loader";
import type { MessageOut } from "@/lib/api";
import { FileText } from "lucide-react";

interface ChatWindowProps {
  messages: MessageOut[];
  isLoading?: boolean;
  pdfName?: string;
}

export function ChatWindow({ messages, isLoading = false, pdfName }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 px-4 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted">
          <FileText className="h-8 w-8 text-muted-foreground" />
        </div>
        {pdfName ? (
          <>
            <h3 className="text-lg font-semibold text-foreground">
              Ready to answer your questions
            </h3>
            <p className="max-w-sm text-sm text-muted-foreground">
              <span className="font-medium text-foreground">{pdfName}</span> has been
              processed. Ask anything about its contents below.
            </p>
          </>
        ) : (
          <>
            <h3 className="text-lg font-semibold text-foreground">
              Upload a PDF to get started
            </h3>
            <p className="max-w-sm text-sm text-muted-foreground">
              Upload a document using the button in the sidebar, then ask questions about
              its contents.
            </p>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-4 py-6 scrollbar-thin scrollbar-thumb-muted scrollbar-track-transparent">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} role={msg.role} content={msg.content} thinking={msg.thinking} />
      ))}
      {isLoading && (
        <div className="mr-auto">
          <Loader />
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
