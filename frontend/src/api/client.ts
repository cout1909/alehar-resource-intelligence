import type {
  BatchSummary,
  Lender,
  Summary,
  SystemStatus,
  Verification,
} from "../types/api";

const base = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

async function send<T>(path: string, options: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(
    () => controller.abort(),
    options.method === "POST" ? 900000 : 90000,
  );
  try {
    const response = await fetch(`${base}${path}`, {
      ...options,
      signal: controller.signal,
    });
    if (!response.ok) {
      const messages: Record<number, string> = {
        403: "This action is disabled in the public demo.",
        404: "This record was not found.",
        409: "Another verification is running, or this review has already been decided. Refresh and try again.",
        422: "Please check the supplied values and try again.",
        503: "The database is unavailable. Please try again later.",
      };
      throw new Error(
        messages[response.status] ||
          "The request could not be completed. Please try again.",
      );
    }
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof TypeError)
      throw new Error(
        "Cannot reach the backend. Check the connection and retry.",
      );
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(
        "The request timed out. A verification may still be running; refresh before retrying.",
      );
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

// Share simultaneous reads, including React StrictMode effects; never cache mutations.
const pendingReads = new Map<string, Promise<unknown>>();
function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  if (options.method && options.method !== "GET") return send<T>(path, options);
  const existing = pendingReads.get(path);
  if (existing) return existing as Promise<T>;
  const pending = send<T>(path, options).finally(() =>
    pendingReads.delete(path),
  );
  pendingReads.set(path, pending);
  return pending;
}

export const api = {
  lenders: () => request<{ total: number; lenders: Lender[] }>("/lenders"),
  lender: (id: string | number) => request<Lender>(`/lenders/${id}`),
  latest: () => request<Verification[]>("/dashboard/latest"),
  summary: () => request<Summary>("/dashboard/summary"),
  system: () => request<SystemStatus>("/system/status"),
  history: (query = "") =>
    request<Verification[]>(`/verification-results${query}`),
  result: (id: string) => request<Verification>(`/verification-results/${id}`),
  lenderHistory: (id: string | number, offset = 0) =>
    request<Verification[]>(`/lenders/${id}/history?limit=50&offset=${offset}`),
  pending: (offset = 0) =>
    request<Verification[]>(`/reviews/pending?limit=50&offset=${offset}`),
  verify: (id: number) =>
    request<Verification>(`/lenders/${id}/verify`, { method: "POST" }),
  verifyAll: () => request<BatchSummary>("/verify-all", { method: "POST" }),
  review: (id: number, action: "approve" | "reject", note: string) =>
    request<Verification>(`/verification-results/${id}/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note }),
    }),
};
