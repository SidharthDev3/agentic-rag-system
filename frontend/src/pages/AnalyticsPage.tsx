import { useQuery } from "@tanstack/react-query";
import { BarChart3 } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { getSystemStats } from "@/services/api";
import type { SystemStats } from "@/types";

export function AnalyticsPage() {
  const { data: stats, isLoading, isError } = useQuery<SystemStats>({ queryKey: ["analytics"], queryFn: getSystemStats as () => Promise<SystemStats>, refetchInterval: 15000 });
  if (isLoading) return <div className="p-6 text-sm text-slate-500">Loading observability data…</div>;
  if (isError || !stats) return <div className="p-6 text-sm text-red-400">Unable to load observability data.</div>;
  return <div className="p-6 space-y-6 max-w-5xl mx-auto"><div className="flex gap-2 items-center"><BarChart3 className="w-5 h-5 text-indigo-400" /><div><h1 className="text-xl font-bold text-slate-100">Observability</h1><p className="text-sm text-slate-500">Telemetry recorded by completed agent workflows.</p></div></div><div className="grid md:grid-cols-3 gap-4">{[["Queries", stats.total_queries], ["Average latency", `${stats.avg_latency_ms.toFixed(0)} ms`], ["Retrieval latency", `${stats.avg_retrieval_latency_ms.toFixed(0)} ms`]].map(([label, value]) => <Card key={String(label)}><CardContent className="p-5"><p className="text-xs text-slate-500">{label}</p><p className="text-2xl font-bold mt-1 text-slate-100">{value}</p></CardContent></Card>)}</div><Card><CardHeader><CardTitle>Recent workflow executions</CardTitle></CardHeader><CardContent className="p-0">{stats.recent_queries.length ? <div className="divide-y divide-slate-800">{stats.recent_queries.map((query) => <div className="p-4 flex gap-4 items-start" key={query.id}><div className="flex-1 min-w-0"><p className="text-sm text-slate-300 truncate">{query.query}</p><p className="text-xs text-slate-600 mt-1">retrieval {query.retrieval_latency_ms.toFixed(0)} ms · rerank {query.rerank_latency_ms.toFixed(0)} ms · {query.chunk_count} chunks</p></div><Badge variant="outline">{query.strategy}</Badge></div>)}</div> : <p className="p-6 text-sm text-slate-500">No workflow telemetry recorded yet.</p>}</CardContent></Card></div>;
}
