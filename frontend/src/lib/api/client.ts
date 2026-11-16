const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

type Options = {
  method?: string;
  body?: unknown;
  query?: Record<string, string | number | boolean | null | undefined>;
};

export async function apiFetch<T>(path: string, { method = "GET", body, query }: Options = {}): Promise<T> {
  const url = new URL(API_URL + path);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, String(value));
  }

  const res = await fetch(url, {
    method,
    headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });

  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new ApiError(res.status, typeof data?.detail === "string" ? data.detail : res.statusText);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}