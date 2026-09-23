/**
 * Reusable API client for the FastAPI backend.
 */

const DEFAULT_API_URL = "http://localhost:8000";

export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || DEFAULT_API_URL;
}

export type ServiceHealth = {
  status: string;
  service: string;
};

export type DatabaseHealth = {
  status: string;
  database: string;
};

export type HealthCheckResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

async function fetchJson<T>(path: string): Promise<HealthCheckResult<T>> {
  const url = `${getApiBaseUrl()}${path}`;

  try {
    const response = await fetch(url, {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });

    if (!response.ok) {
      return {
        ok: false,
        error: `HTTP ${response.status}`,
      };
    }

    const data = (await response.json()) as T;
    return { ok: true, data };
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unable to reach backend";
    return { ok: false, error: message };
  }
}

export function fetchServiceHealth(): Promise<HealthCheckResult<ServiceHealth>> {
  return fetchJson<ServiceHealth>("/api/health");
}

export function fetchDatabaseHealth(): Promise<
  HealthCheckResult<DatabaseHealth>
> {
  return fetchJson<DatabaseHealth>("/api/health/database");
}
