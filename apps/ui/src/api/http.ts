import { ApiError } from "./client";

export type ErrorKind = "validation" | "domain" | "infra" | "unknown";

export interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  headers?: Record<string, string>;
  body?: string;
  signal?: AbortSignal;
  timeoutMs?: number;
  retries?: number;
}

function classify(status: number): ErrorKind {
  if (status === 400 || status === 422) return "validation";
  if (status >= 401 && status < 500) return "domain";
  if (status >= 500) return "infra";
  return "unknown";
}

async function readErrorBody(response: Response): Promise<string> {
  const raw = await response.text().catch(() => "");
  if (!raw) return "unknown";
  try {
    const parsed = JSON.parse(raw) as { detail?: string; message?: string };
    return parsed.detail ?? parsed.message ?? raw;
  } catch {
    return raw;
  }
}

export async function requestJson<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const {
    method = "GET",
    headers = {},
    body,
    signal,
    timeoutMs = 15_000,
    retries = 0,
  } = options;

  const combinedController = new AbortController();
  const onAbort = () => combinedController.abort();
  signal?.addEventListener("abort", onAbort, { once: true });

  try {
    for (let attempt = 0; attempt <= retries; attempt += 1) {
      const timeout = setTimeout(() => combinedController.abort(), timeoutMs);
      try {
        const response = await fetch(path, {
          method,
          headers,
          body,
          signal: combinedController.signal,
        });
        if (!response.ok) {
          const detail = await readErrorBody(response);
          throw new ApiError(response.status, `${classify(response.status)}:${detail}`);
        }
        return (await response.json()) as T;
      } catch (error) {
        const isLastAttempt = attempt === retries;
        if (error instanceof DOMException && error.name === "AbortError") {
          throw new ApiError(0, "infra:timeout");
        }
        if (!isLastAttempt) {
          continue;
        }
        if (error instanceof ApiError) {
          throw error;
        }
        throw new ApiError(0, "infra:network");
      } finally {
        clearTimeout(timeout);
      }
    }
  } finally {
    signal?.removeEventListener("abort", onAbort);
  }

  throw new ApiError(0, "unknown:request-failed");
}

