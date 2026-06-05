import { useEffect, useState } from "react";
import {
  getDatabaseMetrics,
  type DatabaseMetricsResponse,
} from "@/lib/api";
import { Database, FileText, MessageSquare, HardDrive, Cpu, ShieldCheck, Loader2, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

export function MetricsDashboard() {
  const [metrics, setMetrics] = useState<DatabaseMetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchMetrics = () => {
    setLoading(true);
    setError("");
    getDatabaseMetrics()
      .then((res) => {
        setMetrics(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load metrics");
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  function formatBytes(bytes: number) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }

  function formatDuration(seconds: number | null | undefined) {
    if (seconds == null) return "-";
    return `${seconds.toFixed(2)}s`;
  }

  if (loading) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground animate-pulse">Loading database metrics…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 px-4 text-center">
        <p className="text-sm font-semibold text-destructive">{error}</p>
        <button
          onClick={fetchMetrics}
          className="flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Retry
        </button>
      </div>
    );
  }

  if (!metrics) return null;

  return (
    <div className="flex-1 overflow-y-auto bg-background p-6 md:p-8 scrollbar-thin">
      {/* Title */}
      <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Database className="h-6 w-6 text-primary" />
            Database Statistics
          </h2>
          <p className="text-sm text-muted-foreground">
            Real-time metrics for relational files, chat history, and vector embeddings.
          </p>
        </div>
        <button
          onClick={fetchMetrics}
          className="flex items-center gap-1.5 rounded-lg border border-border px-3.5 py-2 text-xs font-semibold text-foreground hover:bg-muted transition-colors"
          title="Refresh statistics"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        {/* Files Card */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-blue-500/10 text-blue-500 rounded-lg">
            <FileText className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Total Files</p>
            <h4 className="text-2xl font-bold text-foreground mt-0.5">{metrics.total_files}</h4>
          </div>
        </div>

        {/* Chats Card */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-purple-500/10 text-purple-500 rounded-lg">
            <MessageSquare className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Conversations</p>
            <h4 className="text-2xl font-bold text-foreground mt-0.5">{metrics.total_conversations}</h4>
          </div>
        </div>

        {/* Messages Card */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-green-500/10 text-green-500 rounded-lg">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Total Messages</p>
            <h4 className="text-2xl font-bold text-foreground mt-0.5">{metrics.total_messages}</h4>
          </div>
        </div>

        {/* Disk Card */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-yellow-500/10 text-yellow-500 rounded-lg">
            <HardDrive className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Storage Size</p>
            <h4 className="text-2xl font-bold text-foreground mt-0.5">{formatBytes(metrics.total_file_size_bytes)}</h4>
          </div>
        </div>
      </div>

      {/* Detail Layout */}
      <div className="grid gap-6 lg:grid-cols-3 mb-8">
        {/* Left Column: Vector Collections & Statuses */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          {/* Status Breakdown */}
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider mb-4">Ingestion Statuses</h3>
            <div className="flex flex-col gap-3">
              {Object.entries(metrics.status_counts).map(([status, count]) => {
                const colors = {
                  COMPLETED: "bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20",
                  PROCESSING: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20",
                  PENDING: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
                  CANCELLED: "bg-gray-500/10 text-gray-500 border-gray-500/20",
                  FAILED: "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20",
                }[status] || "bg-muted text-muted-foreground";

                return (
                  <div key={status} className="flex items-center justify-between py-1 border-b border-border last:border-0">
                    <span className={cn("px-2.5 py-0.5 rounded-full text-xs font-bold border", colors)}>
                      {status}
                    </span>
                    <span className="text-sm font-semibold text-foreground">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Chroma Collections */}
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm flex-1">
            <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider mb-4 flex items-center gap-1.5">
              <Cpu className="h-4 w-4 text-primary" />
              Chroma Collections ({metrics.chroma_collections.length})
            </h3>
            {metrics.chroma_collections.length === 0 ? (
              <p className="text-xs text-muted-foreground italic">No vector collections exist.</p>
            ) : (
              <div className="flex flex-col gap-3 max-h-[300px] overflow-y-auto pr-1 scrollbar-thin">
                {metrics.chroma_collections.map((col) => (
                  <div key={col.name} className="flex flex-col p-2.5 bg-muted/40 rounded-lg border border-border">
                    <span className="text-xs font-mono font-medium text-foreground truncate" title={col.name}>
                      {col.name}
                    </span>
                    <span className="text-[10px] text-muted-foreground mt-1 font-semibold">
                      Documents/Chunks: <span className="text-foreground">{col.count}</span>
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Files Log */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card p-6 shadow-sm overflow-hidden flex flex-col">
          <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider mb-4">Ingested Files Log</h3>
          <div className="flex-1 overflow-x-auto scrollbar-thin">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-border bg-muted/30 text-muted-foreground">
                  <th className="py-2.5 px-3 font-semibold">Filename</th>
                  <th className="py-2.5 px-3 font-semibold">Size</th>
                  <th className="py-2.5 px-3 font-semibold">Pages</th>
                  <th className="py-2.5 px-3 font-semibold">Chunks</th>
                  <th className="py-2.5 px-3 font-semibold">Time</th>
                  <th className="py-2.5 px-3 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {metrics.files.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-muted-foreground italic">
                      No files ingested yet.
                    </td>
                  </tr>
                ) : (
                  metrics.files.map((file) => (
                    <tr key={file.id} className="hover:bg-muted/10">
                      <td className="py-2.5 px-3 font-medium text-foreground truncate max-w-[150px]" title={file.filename}>
                        {file.filename}
                      </td>
                      <td className="py-2.5 px-3 text-muted-foreground">{formatBytes(file.file_size)}</td>
                      <td className="py-2.5 px-3 text-muted-foreground">{file.num_pages}</td>
                      <td className="py-2.5 px-3 text-muted-foreground">{file.num_chunks}</td>
                      <td className="py-2.5 px-3 text-muted-foreground">{formatDuration(file.time_taken)}</td>
                      <td className="py-2.5 px-3">
                        <span className={cn(
                          "px-2 py-0.5 rounded-full text-[10px] font-bold border",
                          {
                            COMPLETED: "bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20",
                            PROCESSING: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20",
                            PENDING: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
                            CANCELLED: "bg-gray-500/10 text-gray-500 border-gray-500/20",
                            FAILED: "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20",
                          }[file.status] || "bg-muted text-muted-foreground"
                        )}>
                          {file.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
