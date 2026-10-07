import React, { useState } from "react";
import { Library, Plus } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { FileUploadZone } from "@/components/documents/FileUploadZone";
import { DocumentList } from "@/components/documents/DocumentList";
import type { ToastMessage } from "@/components/ui/Toast";

interface KnowledgePageProps {
  onAddToast: (type: ToastMessage["type"], title: string, desc?: string) => void;
}

export function KnowledgePage({ onAddToast }: KnowledgePageProps) {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-2.5">
        <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center">
          <Library className="w-3.5 h-3.5 text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-slate-100">Knowledge Base</h1>
          <p className="text-xs text-slate-500 mt-0.5">Upload and manage documents for retrieval</p>
        </div>
      </div>

      {/* Upload Zone */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="w-4 h-4 text-indigo-400" />
            Upload Documents
          </CardTitle>
        </CardHeader>
        <CardContent>
          <FileUploadZone
            onUploadSuccess={() => setRefreshTrigger((t) => t + 1)}
            onAddToast={onAddToast}
          />
        </CardContent>
      </Card>

      {/* Document List */}
      <Card>
        <CardHeader>
          <CardTitle>Indexed Documents</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <DocumentList onAddToast={onAddToast} refreshTrigger={refreshTrigger} />
        </CardContent>
      </Card>
    </div>
  );
}

