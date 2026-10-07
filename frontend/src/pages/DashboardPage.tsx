import React, { useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  LayoutDashboard,
  Library,
  BarChart3,
  Clock,
  FileText,
  MessageSquare,
  TrendingUp,
  Zap,
  ChevronRight,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SkeletonStatCard } from "@/components/ui/Skeleton";
import { getSystemStats } from "@/services/api";
import { formatDate } from "@/lib/utils";
import type { SystemStats } from "@/types";

function StatCard({
  label,
  value,
  icon: Icon,
  sub,
  color = "indigo",
}: {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  sub?: string;
  color?: "indigo" | "emerald" | "amber" | "violet";
}) {
  const colors = {
    indigo: "bg-indigo-600/15 text-indigo-400 border-indigo-600/20",
    emerald: "bg-emerald-600/15 text-emerald-400 border-emerald-600/20",
    amber: "bg-amber-600/15 text-amber-400 border-amber-600/20",
    violet: "bg-violet-600/15 text-violet-400 border-violet-600/20",
  };

  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs text-slate-500 font-medium">{label}</p>
            <p className="text-2xl font-bold text-slate-100 mt-1">{value}</p>
            {sub && <p className="text-[11px] text-slate-500 mt-0.5">{sub}</p>}
          </div>
          <div className={`w-9 h-9 rounded-xl border flex items-center justify-center shrink-0 ${colors[color]}`}>
            <Icon className="w-4 h-4" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const navigate = useNavigate();
  const { data: stats, isLoading } = useQuery<SystemStats>({
    queryKey: ["stats"],
    queryFn: getSystemStats as any,
    refetchInterval: 15000,
  });

  const avgLatency = stats?.avg_latency_ms
    ? `${stats.avg_latency_ms.toFixed(0)}ms`
    : "—";

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2.5 mb-1">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center">
              <Zap className="w-3.5 h-3.5 text-white" />
            </div>
            <h1 className="text-xl font-bold text-slate-100">Dashboard</h1>
          </div>
          <p className="text-sm text-slate-500">
            NexusRAG — Agentic Knowledge Intelligence Platform
          </p>
        </div>
        <Badge
          variant={stats ? "success" : "default"}
          className="gap-1.5"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          {stats ? "API Connected" : "Connecting..."}
        </Badge>
      </div>

      {/* Stats Grid */}
      {isLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonStatCard key={i} />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Documents"
            value={stats?.document_count ?? 0}
            icon={Library}
            sub="Indexed in knowledge base"
            color="indigo"
          />
          <StatCard
            label="Indexed Chunks"
            value={stats?.indexed_chunks_count?.toLocaleString() ?? 0}
            icon={FileText}
            sub="Searchable text segments"
            color="violet"
          />
          <StatCard
            label="Total Queries"
            value={stats?.total_queries ?? 0}
            icon={MessageSquare}
            sub="Agent pipeline executions"
            color="emerald"
          />
          <StatCard
            label="Avg Latency"
            value={avgLatency}
            icon={Clock}
            sub="End-to-end pipeline (ms)"
            color="amber"
          />
        </div>
      )}

      {/* Two-column row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Info */}
        <Card>
          <CardHeader>
            <CardTitle>System Configuration</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-slate-800/60">
              {[
                ["LLM Provider", stats?.llm_provider ?? "—"],
                ["Embedding Model", stats?.embedding_model ?? "—"],
                ["Vector Store", stats?.vector_store_status ?? "—"],
                ["Reranker", stats?.reranker_status ?? "—"],
                ["Avg Retrieval", stats ? `${stats.avg_retrieval_latency_ms.toFixed(0)}ms` : "—"],
                ["Avg LLM", stats ? `${stats.avg_llm_latency_ms.toFixed(0)}ms` : "—"],
              ].map(([k, v]) => (
                <div key={k} className="flex items-center justify-between px-5 py-2.5">
                  <span className="text-xs text-slate-500">{k}</span>
                  <span className="text-xs font-mono text-slate-300">{v}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Strategy Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Query Routing Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {!stats?.strategy_distribution?.length ? (
              <div className="text-center py-6 text-slate-600 text-sm">
                No queries yet. Start chatting!
              </div>
            ) : (
              <div className="space-y-3">
                {stats.strategy_distribution.slice(0, 5).map((s) => {
                  const total = stats.total_queries || 1;
                  const pct = Math.round((s.count / total) * 100);
                  return (
                    <div key={s.strategy} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400 capitalize">{s.strategy.replace(/_/g, " ")}</span>
                        <span className="text-slate-500 font-mono">{s.count} ({pct}%)</span>
                      </div>
                      <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-indigo-600 to-violet-600 rounded-full transition-all duration-700"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Queries */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Queries</CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate("/analytics")}
            className="text-slate-500"
          >
            View all
            <ChevronRight className="w-3.5 h-3.5" />
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          {!stats?.recent_queries?.length ? (
            <div className="text-center py-8 text-slate-600 text-sm">No recent queries.</div>
          ) : (
            <div className="divide-y divide-slate-800/60">
              {stats.recent_queries.slice(0, 8).map((q) => (
                <div key={q.id} className="flex items-start gap-3 px-5 py-3">
                  <MessageSquare className="w-3.5 h-3.5 text-slate-600 mt-0.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-slate-300 truncate">{q.query}</p>
                    <div className="flex items-center gap-2 mt-0.5 text-[10px] text-slate-600">
                      <Badge variant="outline" size="sm">{q.strategy}</Badge>
                      <span>{q.total_latency_ms.toFixed(0)}ms</span>
                      <span>·</span>
                      <span>{q.chunk_count} chunks</span>
                      <span>·</span>
                      <span>{formatDate(q.created_at)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

