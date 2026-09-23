import { getApiBaseUrl, requestJson } from "@/lib/api/client";
import type {
  DatabaseHealth,
  Job,
  JobCreateInput,
  JobImportHistoryItem,
  JobImportRequest,
  JobImportResult,
  JobListItem,
  JobMatch,
  JobStats,
  ResumeProfile,
  ServiceHealth,
} from "@/lib/api/types";
import type { HealthCheckResult } from "@/lib/api/types";

export type * from "@/lib/api/types";
export { getApiBaseUrl } from "@/lib/api/client";

const requestMultipart = async <T>(
  path: string,
  formData: FormData,
): Promise<HealthCheckResult<T>> => {
  const url = `${getApiBaseUrl()}${path}`;
  try {
    const response = await fetch(url, {
      method: "POST",
      body: formData,
      cache: "no-store",
    });
    if (!response.ok) {
      let detail = `HTTP ${response.status}`;
      try {
        const errBody = (await response.json()) as {
          detail?: string | { message?: string };
        };
        if (typeof errBody.detail === "string") detail = errBody.detail;
        else if (errBody.detail && typeof errBody.detail === "object") {
          detail = errBody.detail.message || detail;
        }
      } catch {
        /* ignore */
      }
      return { ok: false, error: detail };
    }
    return { ok: true, data: (await response.json()) as T };
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unable to reach backend";
    return { ok: false, error: message };
  }
};

export const fetchServiceHealth = () =>
  requestJson<ServiceHealth>("/api/health");

export const fetchDatabaseHealth = () =>
  requestJson<DatabaseHealth>("/api/health/database");

export const fetchJobs = (
  params?: Record<string, string | number | undefined>,
) => {
  const search = new URLSearchParams();
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== "") {
        search.set(key, String(value));
      }
    }
  }
  const qs = search.toString();
  return requestJson<JobListItem[]>(`/api/jobs${qs ? `?${qs}` : ""}`);
};

export const fetchJobStats = () => requestJson<JobStats>("/api/jobs/stats");

export const fetchJob = (id: number) => requestJson<Job>(`/api/jobs/${id}`);

export const createJob = (payload: JobCreateInput) =>
  requestJson<Job>("/api/jobs", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const deleteJob = (id: number) =>
  requestJson<void>(`/api/jobs/${id}`, { method: "DELETE" });

export const analyzeJob = (id: number) =>
  requestJson<{ job: Job; matches: JobMatch[] }>(`/api/jobs/${id}/analyze`, {
    method: "POST",
  });

export const fetchJobMatches = (id: number) =>
  requestJson<JobMatch[]>(`/api/jobs/${id}/matches`);

export const updateJobStatus = (id: number, status: string) =>
  requestJson<Job>(`/api/jobs/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });

export const fetchProfiles = () =>
  requestJson<ResumeProfile[]>("/api/profiles");

export const seedDevelopmentData = () =>
  requestJson<Record<string, number>>("/api/admin/seed", { method: "POST" });

export const importJobsManual = (payload: JobImportRequest) =>
  requestJson<JobImportResult>("/api/jobs/import", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const importJobsCsv = (file: File) => {
  const form = new FormData();
  form.append("file", file);
  return requestMultipart<JobImportResult>("/api/jobs/import/csv", form);
};

export const importJobsJson = (file: File) => {
  const form = new FormData();
  form.append("file", file);
  return requestMultipart<JobImportResult>("/api/jobs/import/json", form);
};

export const fetchImportHistory = () =>
  requestJson<JobImportHistoryItem[]>("/api/jobs/import/history");
