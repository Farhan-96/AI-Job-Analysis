"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { JobCreateForm } from "@/components/jobs/JobCreateForm";
import { JobFilters } from "@/components/jobs/JobFilters";
import { JobStatsCards } from "@/components/jobs/JobStatsCards";
import { JobsTable } from "@/components/jobs/JobsTable";
import { EMPTY_FILTERS, Filters } from "@/components/jobs/types";
import {
  JobListItem,
  JobStats,
  ResumeProfile,
  analyzeJob,
  createJob,
  deleteJob,
  fetchJobStats,
  fetchJobs,
  fetchProfiles,
  seedDevelopmentData,
  updateJobStatus,
} from "@/lib/api";

export const JobsDashboard = () => {
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [stats, setStats] = useState<JobStats | null>(null);
  const [profiles, setProfiles] = useState<ResumeProfile[]>([]);
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const params = {
      status: filters.status || undefined,
      source: filters.source || undefined,
      remote_type: filters.remote_type || undefined,
      location: filters.location || undefined,
      profile_id: filters.profile_id ? Number(filters.profile_id) : undefined,
      min_score: filters.min_score ? Number(filters.min_score) : undefined,
    };
    const [jobsResult, statsResult, profilesResult] = await Promise.all([
      fetchJobs(params),
      fetchJobStats(),
      fetchProfiles(),
    ]);
    if (!jobsResult.ok) {
      setError(jobsResult.error);
      setLoading(false);
      return;
    }
    setJobs(jobsResult.data);
    if (statsResult.ok) setStats(statsResult.data);
    if (profilesResult.ok) setProfiles(profilesResult.data);
    setLoading(false);
  }, [filters]);

  useEffect(() => {
    void load();
  }, [load]);

  const handleAnalyze = async (id: number) => {
    setActionMessage(null);
    const result = await analyzeJob(id);
    if (!result.ok) {
      setActionMessage(`Analyze failed: ${result.error}`);
      return;
    }
    setActionMessage(`Analyzed job #${id}`);
    await load();
  };

  const handleStatus = async (id: number, status: string) => {
    const result = await updateJobStatus(id, status);
    if (!result.ok) {
      setActionMessage(result.error);
      return;
    }
    setActionMessage(`Job #${id} marked ${status}`);
    await load();
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Delete this job?")) return;
    const result = await deleteJob(id);
    if (!result.ok) {
      setActionMessage(result.error);
      return;
    }
    setActionMessage(`Deleted job #${id}`);
    await load();
  };

  const handleSeed = async () => {
    const result = await seedDevelopmentData();
    if (!result.ok) {
      setActionMessage(result.error);
      return;
    }
    setActionMessage(
      `Seeded profiles=${result.data.profiles}, jobs=${result.data.jobs}`,
    );
    await load();
  };

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const result = await createJob({
      title: String(form.get("title") || ""),
      company: String(form.get("company") || "") || undefined,
      location: String(form.get("location") || "") || undefined,
      url: String(form.get("url") || "") || undefined,
      description: String(form.get("description") || ""),
      source: String(form.get("source") || "manual"),
      source_job_id: String(form.get("source_job_id") || "") || undefined,
      employment_type: String(form.get("employment_type") || "") || undefined,
    });
    if (!result.ok) {
      setActionMessage(result.error);
      return;
    }
    setShowForm(false);
    setActionMessage(`Created job #${result.data.id}`);
    event.currentTarget.reset();
    await load();
  };

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-accent">Phase 2</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight">
            Job Dashboard
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            Manually add jobs, run analysis, and review profile match scores.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setShowForm((v) => !v)}
            className="rounded-md bg-accent px-3 py-2 text-sm font-medium text-white"
          >
            {showForm ? "Close form" : "Add job"}
          </button>
          <button
            type="button"
            onClick={() => void handleSeed()}
            className="rounded-md border border-border bg-card px-3 py-2 text-sm"
          >
            Seed sample data
          </button>
        </div>
      </header>

      {stats && <JobStatsCards stats={stats} />}
      {showForm && <JobCreateForm onSubmit={(e) => void handleCreate(e)} />}
      <JobFilters filters={filters} profiles={profiles} onChange={setFilters} />

      {actionMessage && (
        <p className="text-sm text-slate-600">{actionMessage}</p>
      )}
      {error && <p className="text-sm text-danger">{error}</p>}
      {loading && <p className="text-sm text-slate-500">Loading jobs…</p>}

      <JobsTable
        jobs={jobs}
        loading={loading}
        onAnalyze={handleAnalyze}
        onStatus={handleStatus}
        onDelete={handleDelete}
      />
    </div>
  );
};
