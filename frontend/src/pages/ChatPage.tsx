import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { MessageSquare, Plus, Trash2, ChevronRight, Clock } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { listConversations, deleteConversation } from "@/services/api";
import { formatDate, truncate } from "@/lib/utils";
import type { Conversation } from "@/types";
import type { ToastMessage } from "@/components/ui/Toast";

interface ChatPageProps {
  onAddToast: (type: ToastMessage["type"], title: string, desc?: string) => void;
}

export function ChatPage({ onAddToast }: ChatPageProps) {
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["conversations", refreshKey],
    queryFn: () => listConversations(0, 30) as Promise<{ conversations: Conversation[]; total: number }>,
    refetchInterval: 10000,
  });

  const conversations = data?.conversations ?? [];

  const handleDelete = async (id: string) => {
    try {
      await deleteConversation(id);
      if (activeConvId === id) setActiveConvId(null);
      setRefreshKey((k) => k + 1);
      onAddToast("success", "Conversation deleted");
    } catch (err: any) {
      onAddToast("error", "Delete failed", err.message);
    }
  };

  return (
    <div className="flex h-full bg-slate-950">
      {/* Conversation Sidebar */}
      <aside className="w-56 shrink-0 border-r border-slate-800/70 flex flex-col bg-slate-950/80">
        <div className="px-3 py-3 border-b border-slate-800/60">
          <Button
            variant="primary"
            size="sm"
            className="w-full"
            onClick={() => setActiveConvId(null)}
          >
            <Plus className="w-3.5 h-3.5" />
            New Chat
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto py-2 px-2 space-y-0.5">
          {isLoading
            ? Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full rounded-lg" />
              ))
            : conversations.map((conv) => (
                <div
                  key={conv.id}
                  className={`group flex items-start gap-2 px-2.5 py-2 rounded-lg cursor-pointer transition-colors ${
                    activeConvId === conv.id
                      ? "bg-indigo-600/20 border border-indigo-600/30"
                      : "hover:bg-slate-800/60 border border-transparent"
                  }`}
                  onClick={() => setActiveConvId(conv.id)}
                >
                  <MessageSquare className="w-3.5 h-3.5 text-slate-500 mt-0.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-slate-300 truncate font-medium">{conv.title}</p>
                    <p className="text-[10px] text-slate-600 mt-0.5">{conv.message_count} msg</p>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDelete(conv.id); }}
                    className="opacity-0 group-hover:opacity-100 text-slate-600 hover:text-red-400 transition-all shrink-0"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              ))}
          {!isLoading && conversations.length === 0 && (
            <p className="text-[11px] text-slate-600 text-center mt-6 px-3">
              No conversations yet.
              <br />Start a new chat!
            </p>
          )}
        </div>
      </aside>

      {/* Chat Panel */}
      <div className="flex-1 flex flex-col min-w-0">
        <ChatInterface
          conversationId={activeConvId}
          onConversationCreated={(id) => {
            setActiveConvId(id);
            setRefreshKey((k) => k + 1);
          }}
          onAddToast={onAddToast}
        />
      </div>
    </div>
  );
}

