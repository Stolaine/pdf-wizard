import { cn } from "@/lib/utils";

interface LoaderProps {
  className?: string;
  text?: string;
}

export function Loader({ className, text = "Thinking" }: LoaderProps) {
  return (
    <div className={cn("flex items-center gap-2 text-muted-foreground", className)}>
      <div className="flex items-center gap-1">
        <span
          className="inline-block h-2 w-2 rounded-full bg-primary/60 animate-bounce"
          style={{ animationDelay: "0ms" }}
        />
        <span
          className="inline-block h-2 w-2 rounded-full bg-primary/60 animate-bounce"
          style={{ animationDelay: "150ms" }}
        />
        <span
          className="inline-block h-2 w-2 rounded-full bg-primary/60 animate-bounce"
          style={{ animationDelay: "300ms" }}
        />
      </div>
      <span className="text-sm font-medium">{text}…</span>
    </div>
  );
}
