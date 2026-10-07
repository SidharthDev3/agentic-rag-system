const API_BASE = "/api/v1";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Documents ──────────────────────────────────────────────────────────────

export async function uploadDocument(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    body: form,
  });
  return handleResponse(res);
}

export async function listDocuments(skip = 0, limit = 50) {
  const res = await fetch(`${API_BASE}/documents?skip=${skip}&limit=${limit}`);
  return handleResponse(res);
}

export async function getDocument(id: string) {
  const res = await fetch(`${API_BASE}/documents/${id}`);
  return handleResponse(res);
}

export async function deleteDocument(id: string) {
  const res = await fetch(`${API_BASE}/documents/${id}`, { method: "DELETE" });
  return handleResponse(res);
}

// ── Chat ───────────────────────────────────────────────────────────────────

export interface ChatPayload {
  query: string;
  conversation_id?: string | null;
  top_k?: number;
  use_reranker?: boolean;
  strategy_override?: string | null;
}

export async function sendChatMessage(payload: ChatPayload) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

export function streamChatMessage(
  payload: ChatPayload,
  callbacks: {
    onStatus?: (step: string, message: string) => void;
    onToken?: (token: string) => void;
    onCitations?: (citations: any[]) => void;
    onDone?: (data: any) => void;
    onError?: (err: string) => void;
    onStepCompleted?: (step: string, name: string, latency_ms: number) => void;
  }
): () => void {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${API_BASE}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!res.ok) {
        callbacks.onError?.(`HTTP ${res.status}`);
        return;
      }

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) return;

      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          const trimmed = line.replace(/^data: /, "").trim();
          if (!trimmed) continue;
          try {
            const event = JSON.parse(trimmed);
            if (event.type === "status") callbacks.onStatus?.(event.step, event.message);
            else if (event.type === "step_completed") callbacks.onStepCompleted?.(event.step, event.name, event.latency_ms);
            else if (event.type === "token") callbacks.onToken?.(event.token);
            else if (event.type === "citations") callbacks.onCitations?.(event.citations);
            else if (event.type === "done") callbacks.onDone?.(event);
          } catch {
            // ignore parse errors
          }
        }
      }
    } catch (err: any) {
      if (err.name !== "AbortError") {
        callbacks.onError?.(err.message || "Stream error");
      }
    }
  })();

  return () => controller.abort();
}

// ── Conversations ──────────────────────────────────────────────────────────

export async function listConversations(skip = 0, limit = 50) {
  const res = await fetch(`${API_BASE}/conversations?skip=${skip}&limit=${limit}`);
  return handleResponse(res);
}

export async function getConversation(id: string) {
  const res = await fetch(`${API_BASE}/conversations/${id}`);
  return handleResponse(res);
}

export async function createConversation(title = "New Conversation") {
  const res = await fetch(`${API_BASE}/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  return handleResponse(res);
}

export async function deleteConversation(id: string) {
  const res = await fetch(`${API_BASE}/conversations/${id}`, { method: "DELETE" });
  return handleResponse(res);
}

// ── Stats & Health ─────────────────────────────────────────────────────────

export async function getSystemStats() {
  const res = await fetch(`${API_BASE}/stats`);
  return handleResponse(res);
}

export async function getHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return handleResponse(res);
}

// ── Search ─────────────────────────────────────────────────────────────────

export async function hybridSearch(query: string, top_k = 5, use_reranking = true) {
  const res = await fetch(`${API_BASE}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k, use_reranking }),
  });
  return handleResponse(res);
}

// ── Evaluation ─────────────────────────────────────────────────────────────

export async function getLatestEvaluation() {
  const res = await fetch(`${API_BASE}/evaluation/latest`);
  return handleResponse(res);
}

export async function runEvaluation(run_name = "Manual Run", top_k = 5) {
  const res = await fetch(`${API_BASE}/evaluation/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ run_name, top_k }),
  });
  return handleResponse(res);
}

