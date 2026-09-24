"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  SearchProfile,
  fetchSearchProfiles,
  runSearchProfile,
  updateSearchProfile,
} from "@/lib/api";

const CARD = "rounded-lg border border-border bg-card p-4";

export const JobSearchPage = () => {
  const [profiles, setProfiles] = useState<SearchProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const result = await fetchSearchProfiles();
    if (!result.ok) {
      setError(result.error);
      setLoading(false);
      return;
    }
    setProfiles(result.data);
    setLoading(false);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const handleRun = async (id: number) => {
    setBusyId(id);
    setMessage(null);
    const result = await runSearchProfile(id);
    setBusyId(null);
    if (!result.ok) {
      setMessage(result.error);
      return;
    }
    setMessage(
      `Search started (run #${result.data.run_id}). Jobs will appear as new for the worker to analyze.`,
    );
    // Refresh after a short delay so background task can finish for mock source
    window.setTimeout(() => void load(), 800);
  };

  const handleToggle = async (profile: SearchProfile) => {
    setBusyId(profile.id);
    const result = await updateSearchProfile(profile.id, {
      enabled: !profile.enabled,
    });
    setBusyId(null);
    if (!result.ok) {
      setMessage(result.error);
      return;
    }
    await load();
  };

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-accent">Phase 3 Step 2</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight">
            Job Search
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-600">
            Each search profile runs independently with its own keywords and
            locations. Discovered jobs are imported as status=new; the worker
            analyzes them. No applications are sent.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/jobs/search/new"
            className="rounded-md bg-accent px-3 py-2 text-sm font-medium text-white"
          >
            New profile
          </Link>
          <Link
            href="/jobs/search/history"
            className="rounded-md border border-border bg-card px-3 py-2 text-sm"
          >
            Search history
          </Link>
        </div>
      </header>

      {message && <p className="text-sm text-slate-600">{message}</p>}
      {error && <p className="text-sm text-danger">{error}</p>}
      {loading && <p className="text-sm text-slate-500">Loading profiles…</p>}

      <div className="overflow-x-auto rounded-lg border border-border bg-card shadow-sm">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-border bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2">Search profile</th>
              <th className="px-3 py-2">Source</th>
              <th className="px-3 py-2">Enabled</th>
              <th className="px-3 py-2">Last run</th>
              <th className="px-3 py-2">Jobs found</th>
              <th className="px-3 py-2">Imported</th>
              <th className="px-3 py-2">Duplicates</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {profiles.map((p) => (
              <tr key={p.id} className="border-b border-border last:border-0">
                <td className="px-3 py-3">
                  <div className="font-medium">{p.name}</div>
                  <div className="text-xs text-slate-500">
                    {p.keywords.length} keywords · {p.locations.length}{" "}
                    locations
                    {p.schedule_enabled
                      ? ` · every ${p.schedule_interval_minutes}m`
                      : ""}
                  </div>
                </td>
                <td className="px-3 py-3">{p.source}</td>
                <td className="px-3 py-3">{p.enabled ? "Yes" : "No"}</td>
                <td className="px-3 py-3">
                  {p.last_run_at
                    ? new Date(p.last_run_at).toLocaleString()
                    : "—"}
                </td>
                <td className="px-3 py-3">{p.last_jobs_found ?? "—"}</td>
                <td className="px-3 py-3">{p.last_jobs_imported ?? "—"}</td>
                <td className="px-3 py-3">{p.last_duplicates ?? "—"}</td>
                <td className="px-3 py-3">{p.last_run_status || "—"}</td>
                <td className="px-3 py-3">
                  <div className="flex flex-wrap gap-1">
                    <button
                      type="button"
                      disabled={busyId === p.id || !p.enabled}
                      className="rounded border border-border bg-white px-2 py-1 text-xs disabled:opacity-50"
                      onClick={() => void handleRun(p.id)}
                    >
                      Run now
                    </button>
                    <button
                      type="button"
                      disabled={busyId === p.id}
                      className="rounded border border-border bg-white px-2 py-1 text-xs"
                      onClick={() => void handleToggle(p)}
                    >
                      {p.enabled ? "Disable" : "Enable"}
                    </button>
                    <Link
                      href={`/jobs/search/${p.id}`}
                      className="rounded border border-border bg-white px-2 py-1 text-xs"
                    >
                      Edit
                    </Link>
                    <Link
                      href={`/jobs/search/history?profile=${p.id}`}
                      className="rounded border border-border bg-white px-2 py-1 text-xs"
                    >
                      History
                    </Link>
                  </div>
                </td>
              </tr>
            ))}
            {!loading && profiles.length === 0 && (
              <tr>
                <td colSpan={9} className="px-3 py-8 text-center text-slate-500">
                  No search profiles yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className={`${CARD} text-sm text-slate-600`}>
        <p className="font-medium text-slate-800">Source notes</p>
        <p className="mt-1">
          <strong>mock</strong> — local development catalog (not real jobs).{" "}
          <strong>indeed</strong> — approved feed/import only; HTML scraping is
          not supported. Use CSV/JSON import when an external API is unavailable.
        </p>
      </div>
    </div>
  );
};
