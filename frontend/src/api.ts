import { getToken } from "./auth";

// API base URL. Empty string = same-origin relative `/api` (local dev via the
// Vite proxy, or the built UI served by FastAPI itself). For separate hosting
// (e.g. frontend on Vercel, backend on Koyeb/Render) set VITE_API_BASE at
// build time to the backend origin, e.g. "https://ptransmit-api.koyeb.app".
export const API_BASE: string = (import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "");

export type SystemInfo = {
  app: string;
  version: string;
  demo_mode: boolean;
  python: string;
  platform: string;
  disclaimer: string;
};

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api${path}`, {
    ...options,
    headers: {
      ...(options.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.body && !(options.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
    },
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    const msg = typeof detail.detail === "string" ? detail.detail : JSON.stringify(detail.detail || detail);
    throw new Error(msg || `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export async function apiText(path: string): Promise<string> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res.text();
}
