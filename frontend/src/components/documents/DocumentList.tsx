import React, { useCallback, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  FileText,
  Trash2,
  ChevronRight,
  AlertCircle,
  Loader2,
  RefreshCw,
  FileSearch,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardContent } from "@/components/ui/Card";
import { SkeletonDocumentRow } from "@/components/ui/Skeleton";
import { cn, formatBytes, formatDate } from "@/lib/utils";
import { listDocuments, deleteDocument } from "@/services/api";
import type { Document } from "@/types";

interface DocumentListProps {
  onAddToast?: (type: "success" | "error", title: string, desc?: string) => void;
  refreshTrigger?: number;
}

const statusConfig: Record<string, { label: string; variant: "success" | "warning" | "error" | "info" | "default" }> = {
  indexed: { label: "Indexed", variant: "success" },
  processing: { label: "Processing", variant: "info" },
  pending: { label: "Pending", variant: "warning" },
  failed: { label: "Failed", variant: "error" },
};

const typeIcon: Record<string, string> = {
  pdf: "📄",
  docx: "📝",
  txt: "📃",
  md: "⬇️",
};

function ConfirmDialog({
  doc,
  onConfirm,
  onCancel,
  loading,
}: {
  doc: Document;
  onConfirm: () => void;
  onCancel: () => void;
  loading: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 max-w-sm w-full mx-4 shadow-2xl">
        <div className="flex items-start gap-3 mb-4">
          <div className="w-9 h-9 rounded-xl bg-red-950/60 border border-red-800/60 flex items-center justify-center shrink-0">
            <AlertCircle className="w-4.5 h-4.5 text-red-400" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-100 text-sm">Delete document?</h3>
            <p className="text-xs text-slate-400 mt-1">
              <span className="font-medium text-slate-200">{doc.filename}</span> and all{" "}
              {doc.chunk_count} indexed chunks will be permanently deleted.
            </p>
          </div>
        </div>
        <div className="flex gap-2 justify-end">
          <Button variant="ghost" size="sm" onClick={onCancel} disabled={loading}>
            Cancel
          </Button>
          <Button variant="danger" size="sm" onClick={onConfirm} loading={loading}>
            <Trash2 className="w-3.5 h-3.5" />
            Delete
          </Button>
        </div>
      </div>
    </div>
  );
}

export function DocumentList({ onAddToast, refreshTrigger }: DocumentListProps) {
  const [confirmDoc, setConfirmDoc] = useState<Document | null>(null);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["documents", refreshTrigger],
    queryFn: () => listDocuments(0, 100) as Promise<{ documents: Document[]; total: number }>,
    refetchInterval: 5000, // Poll for processing status updates
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteDocument(id),
    onSuccess: (_, id) => {
      queryClient.setQueryData(["documents", refreshTrigger], (old: any) => ({
        ...old,
        documents: old.documents.filter((d: Document) => d.id !== id),
        total: old.total - 1,
      }));
      onAddToast?.("success", "Document deleted", "All associated chunks removed.");
      setConfirmDoc(null);
    },
    onError: (err: any) => {
      onAddToast?.("error", "Delete failed", err.message);
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-0">
        {Array.from({ length: 5 }).map((_, i) => <SkeletonDocumentRow key={i} />)}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center gap-3 py-10 text-center">
        <AlertCircle className="w-8 h-8 text-red-400" />
        <p className="text-sm text-slate-400">Failed to load documents.</p>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="w-3.5 h-3.5" />
          Retry
        </Button>
      </div>
    );
  }

  const docs = data?.documents ?? [];

  if (docs.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 py-12 text-center text-slate-500">
        <FileSearch className="w-10 h-10 opacity-40" />
        <div>
          <p className="text-sm font-medium">No documents yet</p>
          <p className="text-xs mt-1">Upload PDFs, DOCX, TXT, or Markdown files to get started.</p>
        </div>
      </div>
    );
  }

  return (
    <>
      {confirmDoc && (
        <ConfirmDialog
          doc={confirmDoc}
          onConfirm={() => deleteMutation.mutate(confirmDoc.id)}
          onCancel={() => setConfirmDoc(null)}
          loading={deleteMutation.isPending}
        />
      )}

      <div className="divide-y divide-slate-800/60">
        {docs.map((doc) => {
          const status = statusConfig[doc.status] ?? { label: doc.status, variant: "default" as const };
          return (
            <div
              key={doc.id}
              className="group flex items-center gap-4 px-4 py-3.5 hover:bg-slate-900/40 transition-colors"
            >
              <div className="w-8 h-8 rounded-lg bg-slate-800/80 flex items-center justify-center text-base shrink-0">
                {typeIcon[doc.file_type] ?? "📄"}
              </div>
              <div className="flex-1 min-w-0 space-y-0.5">
                <p className="text-sm font-medium text-slate-200 truncate">{doc.filename}</p>
                <div className="flex items-center gap-2 text-[11px] text-slate-500">
                  <span>{formatBytes(doc.file_size)}</span>
                  <span>·</span>
                  <span>{doc.chunk_count} chunks</span>
                  <span>·</span>
                  <span>{formatDate(doc.created_at)}</span>
                </div>
              </div>
              <Badge variant={status.variant} size="sm">
                {doc.status === "processing" && <Loader2 className="w-2.5 h-2.5 animate-spin" />}
                {status.label}
              </Badge>
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => navigate(`/knowledge/${doc.id}`)}
                  title="View document"
                >
                  <ChevronRight className="w-3.5 h-3.5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setConfirmDoc(doc)}
                  title="Delete document"
                  className="hover:text-red-400"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}

