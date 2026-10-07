import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { FlaskConical } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import type { ToastMessage } from "@/components/ui/Toast";
import { getLatestEvaluation, runEvaluation } from "@/services/api";
import type { EvaluationRun } from "@/types";

export function EvaluationPage({ onAddToast }: { onAddToast: (type: ToastMessage["type"], title: string, desc?: string) => void }) {
  const [isRunning, setIsRunning] = useState(false);
  const { data, refetch, isLoading } = useQuery<EvaluationRun | null>({ queryKey: ["latest-evaluation"], queryFn: getLatestEvaluation as () => Promise<EvaluationRun | null> });
  async function run() { setIsRunning(true); try { await runEvaluation("Frontend evaluation"); await refetch(); onAddToast("success", "Evaluation completed"); } catch (err) { onAddToast("error", "Evaluation failed", err instanceof Error ? err.message : "Unknown error"); } finally { setIsRunning(false); } }
  return <div className="p-6 space-y-6 max-w-5xl mx-auto"><div className="flex justify-between gap-4"><div className="flex gap-2 items-center"><FlaskConical className="w-5 h-5 text-violet-400" /><div><h1 className="text-xl font-bold text-slate-100">RAG Evaluation</h1><p className="text-sm text-slate-500">Run the tracked benchmark against the evaluation dataset.</p></div></div><Button onClick={run} disabled={isRunning}>{isRunning ? "Running…" : "Run evaluation"}</Button></div><Card><CardHeader><CardTitle>{data ? data.run_name : "No evaluation run yet"}</CardTitle></CardHeader><CardContent>{isLoading ? <p className="text-sm text-slate-500">Loading…</p> : data ? <><div className="grid grid-cols-2 md:grid-cols-3 gap-3">{Object.entries(data.metrics).map(([name, score]) => <div key={name} className="rounded-lg bg-slate-900 p-3"><p className="text-xs text-slate-500 capitalize">{name.replace(/_/g, " ")}</p><p className="text-lg font-semibold text-slate-100">{(score * 100).toFixed(1)}%</p></div>)}</div><p className="text-xs text-slate-600 mt-4">Dataset: {data.dataset_size} cases</p></> : <p className="text-sm text-slate-500">Use the button above after ingesting sample data.</p>}</CardContent></Card></div>;
}
