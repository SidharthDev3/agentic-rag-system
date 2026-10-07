import { FormEvent, useState } from "react";
import { Search } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { hybridSearch } from "@/services/api";
import type { SearchResponse } from "@/types";

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      setResult((await hybridSearch(query.trim(), 8, true)) as SearchResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div><h1 className="text-xl font-bold text-slate-100">Evidence Search</h1><p className="text-sm text-slate-500 mt-1">Inspect hybrid retrieval results before asking the agent.</p></div>
      <Card><CardContent className="p-4"><form onSubmit={submit} className="flex gap-3"><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search indexed documents..." className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 text-sm text-slate-100 outline-none focus:border-indigo-500" /><Button type="submit" disabled={isLoading}><Search className="w-4 h-4" />{isLoading ? "Searching" : "Search"}</Button></form></CardContent></Card>
      {error && <p className="text-sm text-red-400">{error}</p>}
      {result && <><p className="text-xs text-slate-500">{result.total_results} results · {result.latency_ms.toFixed(0)} ms</p><div className="space-y-3">{result.results.map((item) => <Card key={item.chunk_id}><CardHeader><CardTitle className="text-sm flex items-center justify-between gap-3"><span className="truncate">{item.filename}</span><Badge variant="outline">{item.score.toFixed(3)}</Badge></CardTitle></CardHeader><CardContent className="pt-0"><p className="text-sm text-slate-400 leading-relaxed whitespace-pre-wrap">{item.content}</p><p className="mt-3 text-xs text-slate-600">{item.retrieval_type}{item.page ? ` · page ${item.page}` : ""}</p></CardContent></Card>)}</div>{result.total_results === 0 && <p className="text-sm text-slate-500 text-center py-8">No matching evidence found.</p>}</>}
    </div>
  );
}
