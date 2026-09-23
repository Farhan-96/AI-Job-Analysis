import { requestJson } from "@/lib/api/client";
import type {
  DatabaseHealth,
  Job,
  JobCreateInput,
  JobListItem,
  JobMatch,
  JobStats,
  ResumeProfile,
  ServiceHealth,
} from "@/lib/api/types";

export type * from "@/lib/api/types";
export { getApiBaseUrl } from "@/lib/api/client";

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
