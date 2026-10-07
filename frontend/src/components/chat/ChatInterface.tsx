import React, { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Send, Square, RefreshCw, Trash2, Copy, Check, BookOpen, Zap, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { cn, formatDate } from "@/lib/utils";
import { streamChatMessage } from "@/services/api";
import type { Message, Citation, WorkflowStep } from "@/types";

// ── Citation Card ──────────────────────────────────────────────────────────

function CitationCard({ citation }: { citation: Citation }) {
  const [expanded, setExpanded] = useState(false);
  const score = Math.round(citation.relevance_score * 100);

  return (
    <div className="border border-slate-700/60 rounded-lg overflow-hidden bg-slate-900/60">
      <button
        onClick={() => setExpanded((e) => !e)}
        className="w-full flex items-start gap-3 px-3 py-2 hover:bg-slate-800/50 transition-colors text-left"
      >
        <span className="inline-flex items-center justify-center text-[11px] font-bold w-5 h-5 rounded-full bg-indigo-600/30 text-indigo-300 border border-indigo-600/40 shrink-0 mt-0.5">
          {citation.id}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-semibold text-slate-200 truncate max-w-[150px]">
              {citation.filename}
            </span>
            {citation.page && (
              <span className="text-[10px] text-slate-500">· Page {citation.page}</span>
            )}
            <Badge
              variant={score >= 80 ? "success" : score >= 60 ? "info" : "warning"}
              size="sm"
            >
              {score}% match
            </Badge>
          </div>
        </div>
        {expanded ? (
          <ChevronUp className="w-3.5 h-3.5 text-slate-500 shrink-0" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 text-slate-500 shrink-0" />
        )}
      </button>
      {expanded && (
        <div className="px-3 py-2 border-t border-slate-800/60 bg-slate-950/40">
          <p className="text-xs text-slate-400 leading-relaxed font-mono">{citation.text}</p>
        </div>
      )}
    </div>
  );
}

// ── Workflow Stepper ───────────────────────────────────────────────────────

function WorkflowStepper({ steps }: { steps: WorkflowStep[] }) {
  const [open, setOpen] = useState(false);
  if (!steps.length) return null;
  const total = steps.reduce((sum, s) => sum + s.latency_ms, 0);
  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 text-[11px] text-slate-500 hover:text-slate-400 transition-colors"
      >
        <Zap className="w-3 h-3" />
        {steps.length} pipeline steps · {total.toFixed(0)}ms
        {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>
      {open && (
        <div className="mt-2 space-y-1">
          {steps.map((step, i) => (
            <div key={i} className="flex items-center gap-2 text-[11px]">
              <div className="w-1.5 h-1.5 rounded-full bg-indigo-500/60 shrink-0" />
              <span className="text-slate-400 flex-1">{step.name}</span>
              <span className="text-slate-600 font-mono">{step.latency_ms.toFixed(0)}ms</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Message Bubble ─────────────────────────────────────────────────────────

function MessageBubble({
  message,
  onRegenerate,
}: {
  message: Message & { workflowSteps?: WorkflowStep[] };
  onRegenerate?: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className={cn("group flex gap-3", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center shrink-0 mt-0.5 shadow-lg shadow-indigo-900/30">
          <Zap className="w-3.5 h-3.5 text-white" />
        </div>
      )}

      <div className={cn("max-w-[78%] space-y-2", isUser && "items-end flex flex-col")}>
        {/* Message body */}
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed",
            isUser
              ? "bg-indigo-600 text-white rounded-tr-sm"
              : "bg-slate-800/80 border border-slate-700/60 text-slate-100 rounded-tl-sm"
          )}
        >
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <div className="prose prose-sm prose-invert max-w-none prose-pre:bg-slate-950/80 prose-pre:border prose-pre:border-slate-700/60 prose-code:text-indigo-300 prose-code:bg-slate-950/60 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-code:font-mono prose-headings:text-slate-100 prose-p:text-slate-200 prose-li:text-slate-200 prose-strong:text-slate-100">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Citations */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="space-y-1.5 w-full">
            <p className="flex items-center gap-1.5 text-[11px] text-slate-500">
              <BookOpen className="w-3 h-3" />
              {message.citations.length} source{message.citations.length !== 1 ? "s" : ""}
            </p>
            <div className="space-y-1">
              {message.citations.map((c) => (
                <CitationCard key={c.id} citation={c} />
              ))}
            </div>
          </div>
        )}

        {/* Workflow steps */}
        {!isUser && message.workflowSteps && (
          <WorkflowStepper steps={message.workflowSteps} />
        )}

        {/* Meta row */}
        <div
          className={cn(
            "flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity",
            isUser ? "justify-end" : "justify-start"
          )}
        >
          <span className="text-[10px] text-slate-600">{formatDate(message.created_at)}</span>
          <button onClick={handleCopy} className="text-slate-600 hover:text-slate-400 transition-colors">
            {copied ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
          </button>
          {!isUser && onRegenerate && (
            <button onClick={onRegenerate} className="text-slate-600 hover:text-slate-400 transition-colors">
              <RefreshCw className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {isUser && (
        <div className="w-7 h-7 rounded-lg bg-slate-700 flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold text-slate-300">
          U
        </div>
      )}
    </div>
  );
}

// ── Typing Indicator ───────────────────────────────────────────────────────

function TypingIndicator({ status }: { status: string }) {
  return (
    <div className="flex gap-3">
      <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center shrink-0 shadow-lg shadow-indigo-900/30">
        <Zap className="w-3.5 h-3.5 text-white" />
      </div>
      <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl rounded-tl-sm px-4 py-3 space-y-1.5">
        <div className="flex gap-1 items-center">
          <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:0ms]" />
          <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:150ms]" />
          <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:300ms]" />
        </div>
        {status && <p className="text-[11px] text-slate-500">{status}</p>}
      </div>
    </div>
  );
}

// ── Streaming Message ──────────────────────────────────────────────────────

function StreamingMessage({ tokens, citations }: { tokens: string; citations: Citation[] }) {
  return (
    <div className="flex gap-3">
      <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center shrink-0 mt-0.5 shadow-lg shadow-indigo-900/30">
        <Zap className="w-3.5 h-3.5 text-white" />
      </div>
      <div className="max-w-[78%] space-y-2">
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl rounded-tl-sm px-4 py-3 text-sm text-slate-100 leading-relaxed">
          <div className="prose prose-sm prose-invert max-w-none prose-code:text-indigo-300 prose-code:bg-slate-950/60 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-code:font-mono">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{tokens}</ReactMarkdown>
          </div>
          <span className="inline-block w-0.5 h-4 bg-indigo-400 animate-pulse ml-0.5 align-middle" />
        </div>
        {citations.length > 0 && (
          <div className="space-y-1">
            {citations.map((c) => <CitationCard key={c.id} citation={c} />)}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Empty State ────────────────────────────────────────────────────────────

function EmptyChat() {
  const suggestions = [
    "How does hybrid retrieval combine vector and keyword search?",
    "Summarize the key concepts in the knowledge base",
    "Compare Raft and Paxos consensus algorithms",
    "What is Reciprocal Rank Fusion and why use it?",
  ];
  return (
    <div className="flex-1 flex flex-col items-center justify-center py-16 px-6 text-center">
      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center mb-5 shadow-2xl shadow-indigo-900/50">
        <Zap className="w-7 h-7 text-white" />
      </div>
      <h2 className="text-lg font-bold text-slate-100 mb-2">NexusRAG — Agentic Knowledge Chat</h2>
      <p className="text-sm text-slate-400 max-w-md mb-8 leading-relaxed">
        Ask questions grounded in your uploaded documents. Every answer comes with verified source citations.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-xl">
        {suggestions.map((s) => (
          <button
            key={s}
            className="text-left px-4 py-3 rounded-xl border border-slate-800 bg-slate-900/50 hover:bg-slate-800/70 hover:border-slate-700 text-xs text-slate-400 hover:text-slate-300 transition-all duration-150 leading-snug"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

// ── Main Chat Interface ────────────────────────────────────────────────────

interface ChatInterfaceProps {
  conversationId?: string | null;
  initialMessages?: Message[];
  onConversationCreated?: (id: string) => void;
  onAddToast?: (type: "success" | "error", title: string, desc?: string) => void;
}

export function ChatInterface({
  conversationId: initialConvId,
  initialMessages = [],
  onConversationCreated,
  onAddToast,
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<(Message & { workflowSteps?: WorkflowStep[] })[]>(
    initialMessages as any
  );
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamTokens, setStreamTokens] = useState("");
  const [streamCitations, setStreamCitations] = useState<Citation[]>([]);
  const [statusMessage, setStatusMessage] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(initialConvId ?? null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const cancelStreamRef = useRef<(() => void) | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streamTokens, statusMessage]);

  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 180) + "px";
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!streaming && input.trim()) handleSend();
    }
  };

  const stopStream = () => {
    cancelStreamRef.current?.();
    setStreaming(false);
    setStatusMessage("");
  };

  const handleSend = useCallback(
    (queryOverride?: string) => {
      const query = (queryOverride ?? input).trim();
      if (!query || streaming) return;

      const userMsg: Message = {
        id: crypto.randomUUID(),
        conversation_id: conversationId ?? "",
        role: "user",
        content: query,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
      setStreaming(true);
      setStreamTokens("");
      setStreamCitations([]);
      setStatusMessage("Initializing agent pipeline...");

      let accTokens = "";
      let finalCitations: Citation[] = [];
      let finalSteps: WorkflowStep[] = [];

      const cancel = streamChatMessage(
        { query, conversation_id: conversationId, top_k: 5 },
        {
          onStatus: (_, msg) => setStatusMessage(msg),
          onStepCompleted: (step, name, latency_ms) => {
            finalSteps = [...finalSteps, { step, name, status: "completed", latency_ms, details: {} }];
          },
          onToken: (token) => {
            accTokens += token;
            setStreamTokens(accTokens);
            setStatusMessage("");
          },
          onCitations: (cits) => {
            finalCitations = cits as Citation[];
            setStreamCitations(cits as Citation[]);
          },
          onDone: (data) => {
            const asstMsg: Message & { workflowSteps?: WorkflowStep[] } = {
              id: crypto.randomUUID(),
              conversation_id: data.conversation_id,
              role: "assistant",
              content: accTokens,
              citations: finalCitations,
              routing_strategy: data.strategy,
              latency_ms: data.total_latency_ms,
              created_at: new Date().toISOString(),
              workflowSteps: finalSteps,
            };
            setMessages((prev) => [...prev, asstMsg]);
            setStreaming(false);
            setStreamTokens("");
            setStreamCitations([]);
            setStatusMessage("");

            if (!conversationId && data.conversation_id) {
              setConversationId(data.conversation_id);
              onConversationCreated?.(data.conversation_id);
            }
          },
          onError: (err) => {
            setStreaming(false);
            setStatusMessage("");
            setStreamTokens("");
            onAddToast?.("error", "Failed to get response", err);
          },
        }
      );
      cancelStreamRef.current = cancel;
    },
    [input, conversationId, streaming, onConversationCreated, onAddToast]
  );

  const handleClear = () => {
    stopStream();
    setMessages([]);
    setConversationId(null);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      {messages.length > 0 && (
        <div className="px-4 py-2.5 border-b border-slate-800/60 flex items-center justify-between bg-slate-950/60">
          <span className="text-xs text-slate-500">
            {messages.length} message{messages.length !== 1 ? "s" : ""}
            {conversationId && (
              <span className="ml-2 text-slate-600 font-mono">#{conversationId.slice(0, 8)}</span>
            )}
          </span>
          <Button variant="ghost" size="sm" onClick={handleClear} className="text-slate-500 hover:text-red-400">
            <Trash2 className="w-3.5 h-3.5" />
            Clear
          </Button>
        </div>
      )}

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        {messages.length === 0 && !streaming ? (
          <EmptyChat />
        ) : (
          <div className="p-5 space-y-6 max-w-4xl mx-auto w-full">
            {messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                onRegenerate={
                  msg.role === "assistant"
                    ? () => {
                        const lastUserMsg = [...messages]
                          .reverse()
                          .find((m) => m.role === "user");
                        if (lastUserMsg) handleSend(lastUserMsg.content);
                      }
                    : undefined
                }
              />
            ))}

            {streaming && streamTokens && (
              <StreamingMessage tokens={streamTokens} citations={streamCitations} />
            )}
            {streaming && !streamTokens && statusMessage && (
              <TypingIndicator status={statusMessage} />
            )}
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-slate-800/60 bg-slate-950/60 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="relative flex items-end gap-2 bg-slate-900/80 border border-slate-700/60 rounded-2xl px-4 pt-3 pb-2 focus-within:border-indigo-600/50 transition-colors">
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your documents… (Shift+Enter for new line)"
              disabled={streaming}
              className="flex-1 bg-transparent text-sm text-slate-100 placeholder-slate-600 resize-none outline-none min-h-[28px] max-h-[180px] py-0.5 leading-relaxed disabled:opacity-40"
            />
            <div className="flex items-center gap-1.5 shrink-0 pb-0.5">
              {streaming ? (
                <Button size="icon" variant="danger" onClick={stopStream} title="Stop generating">
                  <Square className="w-3.5 h-3.5" />
                </Button>
              ) : (
                <Button
                  size="icon"
                  variant="primary"
                  onClick={() => handleSend()}
                  disabled={!input.trim()}
                  title="Send message"
                >
                  <Send className="w-3.5 h-3.5" />
                </Button>
              )}
            </div>
          </div>
          <p className="text-[10px] text-slate-700 mt-1.5 text-center">
            Responses grounded in your indexed knowledge base · Citations verified by LangGraph agent
          </p>
        </div>
      </div>
    </div>
  );
}

