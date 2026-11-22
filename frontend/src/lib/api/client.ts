import "server-only";
import { cookies } from "next/headers";

const API_URL = (process.env.API_URL ?? "http://localhost:8000/api").replace(/\/$/, "");
export const TOKEN_COOKIE = "access_token";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

type Query = Record<string, string | number | boolean | null | undefined>;
type ApiOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  query?: Query;
  auth?: boolean;
};

async function readDetail(res: Response): Promise<string> {
  try {
    const detail = (await res.json())?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((e) => e?.msg ?? "Invalid input").join(", ");
  } catch {
    /* body was not JSON */
  }
  return res.statusText || "Request failed";
}

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { body, query, auth = true, headers, ...init } = options;

  const url = new URL(API_URL + path);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  }

  const h = new Headers(headers);
  h.set("Accept", "application/json");
  if (body !== undefined) h.set("Content-Type", "application/json");
  if (auth) {
    const token = (await cookies()).get(TOKEN_COOKIE)?.value;
    if (token) h.set("Authorization", `Bearer ${token}`);
  }

  let res: Response;
  try {
    res = await fetch(url, {
      cache: "no-store",
      ...init,
      headers: h,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(503, "Cannot reach the API");
  }

  if (!res.ok) throw new ApiError(res.status, await readDetail(res));
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}