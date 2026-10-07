import React, { useState, useRef } from "react";
import { Upload, FileText, File, Loader2, X, CheckCircle, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { cn, formatBytes } from "@/lib/utils";
import { uploadDocument } from "@/services/api";

interface FileUploadZoneProps {
  onUploadSuccess?: (doc: any) => void;
  onAddToast?: (type: "success" | "error", title: string, desc?: string) => void;
}

const ACCEPTED_TYPES = ".pdf,.docx,.txt,.md";
const ACCEPTED_MIMES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
  "text/markdown",
  "text/x-markdown",
];

interface UploadItem {
  id: string;
  file: File;
  status: "pending" | "uploading" | "done" | "error";
  error?: string;
  result?: any;
}

export function FileUploadZone({ onUploadSuccess, onAddToast }: FileUploadZoneProps) {
  const [dragging, setDragging] = useState(false);
  const [queue, setQueue] = useState<UploadItem[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = (files: FileList | File[]) => {
    const newItems: UploadItem[] = Array.from(files)
      .filter((f) => ACCEPTED_MIMES.includes(f.type) || f.name.match(/\.(pdf|docx|txt|md)$/i))
      .map((file) => ({
        id: crypto.randomUUID(),
        file,
        status: "pending" as const,
      }));

    if (newItems.length === 0) {
      onAddToast?.("error", "Invalid file type", "Supported: PDF, DOCX, TXT, MD");
      return;
    }

    setQueue((prev) => [...prev, ...newItems]);
    newItems.forEach((item) => uploadItem(item));
  };

  const uploadItem = async (item: UploadItem) => {
    setQueue((prev) => prev.map((i) => (i.id === item.id ? { ...i, status: "uploading" } : i)));
    try {
      const result = await uploadDocument(item.file);
      setQueue((prev) =>
        prev.map((i) => (i.id === item.id ? { ...i, status: "done", result } : i))
      );
      onAddToast?.(
        "success",
        `Indexed: ${item.file.name}`,
        `${(result as any).chunk_count} chunks created`
      );
      onUploadSuccess?.(result);
    } catch (err: any) {
      setQueue((prev) =>
        prev.map((i) =>
          i.id === item.id ? { ...i, status: "error", error: err.message } : i
        )
      );
      onAddToast?.("error", `Failed: ${item.file.name}`, err.message);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    addFiles(e.dataTransfer.files);
  };

  const removeItem = (id: string) =>
    setQueue((prev) => prev.filter((i) => i.id !== id));

  const fileIcon = (name: string) => {
    const ext = name.split(".").pop()?.toLowerCase();
    if (ext === "pdf") return "📄";
    if (ext === "docx") return "📝";
    if (ext === "md") return "⬇️";
    return "📃";
  };

  return (
    <div className="space-y-3">
      {/* Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-200",
          dragging
            ? "border-indigo-500 bg-indigo-950/20"
            : "border-slate-700/60 hover:border-slate-600 hover:bg-slate-900/40"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED_TYPES}
          className="hidden"
          onChange={(e) => e.target.files && addFiles(e.target.files)}
        />
        <div className="flex flex-col items-center gap-2">
          <div className={cn(
            "w-12 h-12 rounded-2xl flex items-center justify-center transition-colors",
            dragging ? "bg-indigo-600/30" : "bg-slate-800/80"
          )}>
            <Upload className={cn("w-5 h-5", dragging ? "text-indigo-400" : "text-slate-500")} />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-300">
              {dragging ? "Drop to upload" : "Drop files or click to browse"}
            </p>
            <p className="text-xs text-slate-500 mt-0.5">PDF, DOCX, TXT, Markdown · Max 25MB each</p>
          </div>
        </div>
      </div>

      {/* Upload Queue */}
      {queue.length > 0 && (
        <div className="space-y-2">
          {queue.map((item) => (
            <div
              key={item.id}
              className="flex items-center gap-3 px-4 py-2.5 bg-slate-900/60 border border-slate-800/60 rounded-xl"
            >
              <span className="text-base shrink-0">{fileIcon(item.file.name)}</span>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-slate-200 truncate">{item.file.name}</p>
                <p className="text-[10px] text-slate-500">{formatBytes(item.file.size)}</p>
              </div>
              <div className="shrink-0">
                {item.status === "uploading" && (
                  <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
                )}
                {item.status === "done" && (
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                )}
                {item.status === "error" && (
                  <span title={item.error}>
                    <AlertCircle className="w-4 h-4 text-red-400" />
                  </span>
                )}
                {item.status === "pending" && (
                  <Loader2 className="w-4 h-4 text-slate-600 animate-spin" />
                )}
              </div>
              {(item.status === "done" || item.status === "error") && (
                <button
                  onClick={() => removeItem(item.id)}
                  className="text-slate-600 hover:text-slate-400 transition-colors shrink-0"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
