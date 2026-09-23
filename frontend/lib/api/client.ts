import { HealthCheckResult } from "@/lib/api/types";

const DEFAULT_API_URL = "http://localhost:8000";

export const getApiBaseUrl = (): string =>
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || DEFAULT_API_URL;

export const requestJson = async <T>(
  path: string,
  init?: RequestInit,
): Promise<HealthCheckResult<T>> => {
  const url = `${getApiBaseUrl()}${path}`;

  try {
    const response = await fetch(url, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      let detail = `HTTP ${response.status}`;
      try {
        const errBody = (await response.json()) as {
          detail?: string | { message?: string };
        };
        if (typeof errBody.detail === "string") {
          detail = errBody.detail;
        } else if (errBody.detail && typeof errBody.detail === "object") {
          detail = errBody.detail.message || detail;
        }
      } catch {
        /* ignore parse errors */
      }
      return { ok: false, error: detail };
    }

    if (response.status === 204) {
      return { ok: true, data: undefined as T };
    }

    const data = (await response.json()) as T;
    return { ok: true, data };
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unable to reach backend";
    return { ok: false, error: message };
  }
};
