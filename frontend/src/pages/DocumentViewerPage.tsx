import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  FileText,
  Hash,
  CalendarDays,
  HardDrive,
  Layers,
  ChevronDown,
  ChevronUp,
  AlertCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { getDocument } from "@/services/api";
import { formatBytes, formatDate } from "@/lib/utils";
import type { DocumentDetail, DocumentChunk } from "@/types";

function ChunkCard({ chunk, index }: { chunk: DocumentChunk; index: number }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="border border-slate-800/60 rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded((e) => !e)}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-800/40 transition-colors text-left"
      >
        <span className="text-xs font-mono font-bold text-indigo-400 w-6 shrink-0">#{index + 1}</span>
        <div className="flex-1 min-w-0">
          <p className="text-xs text-slate-300 truncate">{chunk.content.substring(0, 100)}…</p>
          <div className="flex items-center gap-2 mt-0.5 text-[10px] text-slate-600">
            {chunk.page_number && <span>Page {chunk.page_number}</span>}
            {chunk.section && <span>· {chunk.section}</span>}
            <span>· {chunk.token_count} tokens</span>
          </div>
        </div>
        {expanded ? <ChevronUp className="w-3.5 h-3.5 text-slate-600 shrink-0" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-600 shrink-0" />}
      </button>
      {expanded && (
        <div className="px-4 py-3 bg-slate-950/40 border-t border-slate-800/60">
          <p className="text-xs text-slate-400 leading-relaxed font-mono whitespace-pre-wrap break-words">{chunk.content}</p>
        </div>
      )}
    </div>
  );
}

export function DocumentViewerPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: doc, isLoading, isError } = useQuery<DocumentDetail>({
    queryKey: ["document", id],
    queryFn: () => getDocument(id!) as Promise<DocumentDetail>,
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="p-6 space-y-5 max-w-4xl mx-auto">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full rounded-xl" />
        <Skeleton className="h-48 w-full rounded-xl" />
      </div>
    );
  }

  if (isError || !doc) {
    return (
      <div className="p-6 flex flex-col items-center gap-3 text-center">
        <AlertCircle className="w-8 h-8 text-red-400" />
        <p className="text-slate-400 text-sm">Document not found.</p>
        <Button variant="outline" size="sm" onClick={() => navigate("/knowledge")}>
          <ArrowLeft className="w-3.5 h-3.5" />
          Back
        </Button>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-5 max-w-4xl mx-auto">
      {/* Back */}
      <Button variant="ghost" size="sm" onClick={() => navigate("/knowledge")} className="text-slate-500">
        <ArrowLeft className="w-3.5 h-3.5" />
        Knowledge Base
      </Button>

      {/* Document Header */}
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-xl shrink-0">
          {doc.file_type === "pdf" ? "📄" : doc.file_type === "docx" ? "📝" : "📃"}
        </div>
        <div className="min-w-0">
          <h1 className="text-lg font-bold text-slate-100 break-all">{doc.filename}</h1>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <Badge variant={doc.status === "indexed" ? "success" : "warning"}>
              {doc.status}
            </Badge>
            <span className="text-xs text-slate-500">{formatDate(doc.created_at)}</span>
          </div>
        </div>
      </div>

      {/* Metadata */}
      <Card>
        <CardHeader>
          <CardTitle>Document Metadata</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="grid grid-cols-2 divide-x divide-slate-800/60">
            <div className="divide-y divide-slate-800/60">
              {[
                [<HardDrive className="w-3.5 h-3.5" />, "File Size", formatBytes(doc.file_size)],
                [<Layers className="w-3.5 h-3.5" />, "Chunks", doc.chunk_count],
                [<Hash className="w-3.5 h-3.5" />, "File Type", doc.file_type.toUpperCase()],
              ].map(([icon, label, val], i) => (
                <div key={i} className="flex items-center gap-2.5 px-5 py-3">
                  <span className="text-slate-600">{icon}</span>
                  <span className="text-xs text-slate-500 flex-1">{label as string}</span>
                  <span className="text-xs font-mono text-slate-300">{String(val)}</span>
                </div>
              ))}
            </div>
            <div className="divide-y divide-slate-800/60">
              {[
                [<CalendarDays className="w-3.5 h-3.5" />, "Created", formatDate(doc.created_at)],
                [<CalendarDays className="w-3.5 h-3.5" />, "Updated", formatDate(doc.updated_at)],
                [<Hash className="w-3.5 h-3.5" />, "SHA-256", doc.content_hash.slice(0, 12) + "…"],
              ].map(([icon, label, val], i) => (
                <div key={i} className="flex items-center gap-2.5 px-5 py-3">
                  <span className="text-slate-600">{icon}</span>
                  <span className="text-xs text-slate-500 flex-1">{label as string}</span>
                  <span className="text-xs font-mono text-slate-300">{String(val)}</span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Chunks */}
      <Card>
        <CardHeader>
          <CardTitle>Indexed Chunks ({doc.chunks?.length ?? 0})</CardTitle>
          <p className="text-xs text-slate-500">Each chunk is independently embedded and retrievable</p>
        </CardHeader>
        <CardContent className="space-y-2">
          {doc.chunks?.length ? (
            doc.chunks.map((chunk, i) => <ChunkCard key={chunk.id} chunk={chunk} index={i} />)
          ) : (
            <p className="text-xs text-slate-600 text-center py-4">No chunks indexed yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

