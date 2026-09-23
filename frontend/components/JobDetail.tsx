"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { JobMatchCard } from "@/components/jobs/JobMatchCard";
import { InfoField } from "@/components/jobs/InfoField";
import {
  Job,
  JobMatch,
  analyzeJob,
  fetchJob,
  fetchJobMatches,
} from "@/lib/api";

type Props = {
  jobId: number;
};

export const JobDetail = ({ jobId }: Props) => {
  const [job, setJob] = useState<Job | null>(null);
  const [matches, setMatches] = useState<JobMatch[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const [jobResult, matchesResult] = await Promise.all([
      fetchJob(jobId),
      fetchJobMatches(jobId),
    ]);
    if (!jobResult.ok) {
      setError(jobResult.error);
      setLoading(false);
      return;
    }
    setJob(jobResult.data);
    if (matchesResult.ok) {
      setMatches(
        [...matchesResult.data].sort((a, b) => b.match_score - a.match_score),
      );
    }
    setLoading(false);
  }, [jobId]);

  useEffect(() => {
    void load();
  }, [load]);

  const handleAnalyze = async () => {
    const result = await analyzeJob(jobId);
    if (!result.ok) {
      setError(result.error);
      return;
    }
    setJob(result.data.job);
    setMatches(
      [...result.data.matches].sort((a, b) => b.match_score - a.match_score),
    );
  };

  if (loading) {
    return <p className="text-sm text-slate-500">Loading job…</p>;
  }
  if (error && !job) {
    return <p className="text-sm text-danger">{error}</p>;
  }
  if (!job) {
    return <p className="text-sm text-slate-500">Job not found.</p>;
  }

  const salary =
    job.salary_min || job.salary_max
      ? `${job.salary_currency || ""} ${job.salary_min ?? "?"} – ${job.salary_max ?? "?"}`.trim()
      : "—";

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link href="/jobs" className="text-sm text-accent">
            ← Back to jobs
          </Link>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">
            {job.title}
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            {job.company || "Unknown company"} · {job.location || "—"} ·{" "}
            {job.remote_type}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void handleAnalyze()}
          className="rounded-md bg-accent px-3 py-2 text-sm font-medium text-white"
        >
          Analyze
        </button>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      <section className="grid gap-4 rounded-lg border border-border bg-card p-5 shadow-sm sm:grid-cols-2">
        <InfoField label="Employment" value={job.employment_type || "—"} />
        <InfoField label="Salary" value={salary} />
        <InfoField label="Source" value={job.source} />
        <InfoField label="Status" value={job.status} />
        <InfoField
          label="URL"
          value={
            job.url ? (
              <a
                href={job.url}
                target="_blank"
                rel="noreferrer"
                className="text-accent underline"
              >
                Open listing
              </a>
            ) : (
              "—"
            )
          }
        />
        <InfoField
          label="Discovered"
          value={new Date(job.discovered_at).toLocaleString()}
        />
        <InfoField
          label="Experience (extracted)"
          value={
            job.extracted_experience_years != null
              ? `${job.extracted_experience_years}+ years`
              : "unknown"
          }
        />
        <InfoField
          label="Education (extracted)"
          value={job.extracted_education || "unknown"}
        />
      </section>

      <section className="rounded-lg border border-border bg-card p-5 shadow-sm">
        <h2 className="text-base font-semibold">Description</h2>
        <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
          {job.description || "No description provided."}
        </p>
        {job.skills.length > 0 && (
          <div className="mt-4">
            <h3 className="text-sm font-medium text-slate-500">
              Extracted skills
            </h3>
            <div className="mt-2 flex flex-wrap gap-2">
              {job.skills.map((skill) => (
                <span
                  key={skill.id}
                  className="rounded-md border border-border bg-slate-50 px-2 py-1 text-xs"
                >
                  {skill.skill}
                </span>
              ))}
            </div>
          </div>
        )}
      </section>

      <section className="space-y-4">
        <h2 className="text-base font-semibold">Profile Match Analysis</h2>
        <p className="text-sm text-slate-600">
          Scores are transparent Profile Match Scores (not hiring probability).
        </p>
        {matches.length === 0 && (
          <p className="text-sm text-slate-500">
            No matches yet. Click Analyze to run the pipeline.
          </p>
        )}
        {matches.map((match) => (
          <JobMatchCard key={match.id} match={match} />
        ))}
      </section>
    </div>
  );
};
