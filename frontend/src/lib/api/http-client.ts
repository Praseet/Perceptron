// Phase 4 - lib/api/http-client.ts
// Real implementation of AflApiClient using fetch() against the
// FastAPI backend (src/api/main.py). Every method matches Appendix C.
// Every method surfaces a clear, typed error rather than swallowing.
//
// Per Phase 4 prompt: this file's job is to fail loudly and correctly;
// fallback-to-demo behavior is the page-level concern, not this one.
//
// AflApiClient is imported from types.ts to avoid a circular import
// (client.ts imports this file's httpClient value).

import type {
  Attack,
  EvalPerClassRow,
  BusinessMetricsResponse,
  ConfusionResponse,
  GenerateRequest,
  GenerateResult,
  HealthResponse,
  LoopEvent,
  LoopHistoryEntry,
  LoopRunRequest,
  PredictRequest,
  PredictResult,
  PrCurveResponse,
  SystemStatus,
  AflApiClient,
} from "./types";

const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";

async function jsonRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${BASE}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(
      `HTTP ${res.status} ${res.statusText} from ${url}: ${text.slice(0, 200)}`,
    );
  }
  return (await res.json()) as T;
}

async function getJson<T>(path: string): Promise<T> {
  return jsonRequest<T>(path, { method: "GET" });
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  return jsonRequest<T>(path, { method: "POST", body: JSON.stringify(body) });
}

// Per H.2.17 / H.13: POST /api/generate may stream as SSE when it
// takes > 2s, otherwise return JSON. The API client owns the
// transport details. We always POST; the server decides whether to
// stream.
async function postJsonOrStream<T>(
  path: string,
  body: unknown,
  onProgress?: (msg: string) => void,
): Promise<T> {
  const url = `${BASE}${path}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(
      `HTTP ${res.status} ${res.statusText} from ${url}: ${text.slice(0, 200)}`,
    );
  }
  const contentType = res.headers.get("content-type") ?? "";
  if (contentType.includes("text/event-stream")) {
    return consumeSse<T>(res, onProgress);
  }
  return (await res.json()) as T;
}

// Per H.13.2: minimal SSE parser for response.body.getReader().
// No npm dependency added.
async function consumeSse<T>(
  res: Response,
  onProgress?: (msg: string) => void,
): Promise<T> {
  if (!res.body) throw new Error("SSE response has no body");
  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let result: T | null = null;
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const rawEvent = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const dataLine = rawEvent
        .split("\n")
        .find((l) => l.startsWith("data:"));
      if (!dataLine) continue;
      const json = dataLine.slice(5).trim();
      if (!json) continue;
      try {
        const parsed = JSON.parse(json);
        if (parsed?.type === "progress" && onProgress) {
          onProgress(String(parsed.message ?? ""));
        } else if (parsed?.type === "result" && parsed.result) {
          result = parsed.result as T;
        } else if (parsed?.type === "error") {
          throw new Error(String(parsed.message ?? "stream error"));
        } else if (parsed?.result) {
          // Some implementations put the result at the top level.
          result = parsed as T;
        }
      } catch (e) {
        if (e instanceof Error) throw e;
        // ignore non-JSON keepalive
      }
    }
  }
  if (result == null) throw new Error("SSE stream ended without a result event");
  return result;
}

export const httpClient: AflApiClient = {
  async getHealth() {
    return getJson<HealthResponse>("/api/health");
  },
  async getAttacks() {
    return getJson<Attack[]>("/api/attacks");
  },
  async getAttack(id: string) {
    return getJson<Attack>(`/api/attacks/${encodeURIComponent(id)}`);
  },
  async generate(req: GenerateRequest, onProgress?: (msg: string) => void) {
    return postJsonOrStream<GenerateResult>("/api/generate", req, onProgress);
  },
  async predict(req: PredictRequest) {
    return postJson<PredictResult>("/api/predict", req);
  },
  async getEvalPerClass() {
    return getJson<EvalPerClassRow[]>("/api/eval/per-class");
  },
  async getEvalPrCurve() {
    return getJson<PrCurveResponse>("/api/eval/pr-curve");
  },
  // H.2.14: business-threshold metrics. Backend not yet shipped; this
  // will return 404 in live mode until the FastAPI route is added.
  // Flagged in PROGRESS.md per the spec's "contract completion, not
  // new product feature" framing.
  async getEvalBusiness() {
    return getJson<BusinessMetricsResponse>("/api/eval/business");
  },
  // H.2.15: confusion heatmap data. Same situation.
  async getEvalConfusion() {
    return getJson<ConfusionResponse>("/api/eval/confusion");
  },
  async getLoopHistory() {
    return getJson<LoopHistoryEntry[]>("/api/loop/history");
  },
  runLoop(req: LoopRunRequest, onEvent: (e: LoopEvent) => void): () => void {
    // POST-with-body for SSE, per H.13.1 (EventSource is GET-only).
    const controller = new AbortController();
    (async () => {
      try {
        const res = await fetch(`${BASE}/api/loop/run`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(req),
          signal: controller.signal,
        });
        if (!res.ok || !res.body) {
          throw new Error(
            `HTTP ${res.status} from /api/loop/run`,
          );
        }
        const reader = res.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          let idx: number;
          while ((idx = buffer.indexOf("\n\n")) !== -1) {
            const rawEvent = buffer.slice(0, idx);
            buffer = buffer.slice(idx + 2);
            const dataLine = rawEvent
              .split("\n")
              .find((l) => l.startsWith("data:"));
            if (!dataLine) continue;
            const json = dataLine.slice(5).trim();
            if (!json) continue;
            try {
              const parsed = JSON.parse(json) as LoopEvent;
              onEvent(parsed);
            } catch {
              // ignore non-JSON keepalive lines
            }
          }
        }
      } catch (e) {
        if (controller.signal.aborted) return;
        onEvent({
          type: "error",
          message: e instanceof Error ? e.message : String(e),
        });
      }
    })();
    return () => controller.abort();
  },
  async getSystemStatus() {
    return getJson<SystemStatus>("/api/system/status");
  },
};