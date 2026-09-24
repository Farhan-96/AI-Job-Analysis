"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { SearchRun, fetchSearchRun, fetchSearchRuns } from "@/lib/api";

const formatDuration = (seconds: number | null) => {
  if (seconds == null) return "—";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  return `${Math.round(seconds / 60)}m`;
};

export const SearchHistoryPage = () => {
  const searchParams = useSearchParams();
  const profileFilter = searchParams.get("profile");
  const [runs, setRuns] = useState<SearchRun[]>([]);
  const [selected, setSelected] = useState<SearchRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const profileId = useMemo(() => {
    if (!profileFilter) return undefined;
    const n = Number(profileFilter);
    return Number.isFinite(n) ? n : undefined;
  }, [profileFilter]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const result = await fetchSearchRuns(
      profileId ? { search_profile_id: profileId } : undefined,
    );
    if (!result.ok) {
      setError(result.error);
      setLoading(false);
      return;
    }
    setRuns(result.data);
    setLoading(false);
  }, [profileId]);

  useEffect(() => {
    void load();
  }, [load]);

  const openRun = async (id: number) => {
    const result = await fetchSearchRun(id);
    if (result.ok) setSelected(result.data);
  };

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-accent">Job Search</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight">
            Search History
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            Every manual or scheduled search run is recorded here.
          </p>
        </div>
        <Link
          href="/jobs/search"
          className="rounded-md border border-border bg-card px-3 py-2 text-sm"
        >
          Back to Job Search
        </Link>
      </header>

      {error && <p className="text-sm text-danger">{error}</p>}
      {loading && <p className="text-sm text-slate-500">Loading history…</p>}

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className="overflow-x-auto rounded-lg border border-border bg-card shadow-sm">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-border bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2">Date</th>
                <th className="px-3 py-2">Search profile</th>
                <th className="px-3 py-2">Source</th>
                <th className="px-3 py-2">Found</th>
                <th className="px-3 py-2">Imported</th>
                <th className="px-3 py-2">Duplicates</th>
                <th className="px-3 py-2">Failed</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Duration</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr
                  key={run.id}
                  className="cursor-pointer border-b border-border last:border-0 hover:bg-slate-50"
                  onClick={() => void openRun(run.id)}
                >
                  <td className="px-3 py-2">
                    {new Date(run.started_at).toLocaleString()}
                  </td>
                  <td className="px-3 py-2">
                    {run.search_profile_name || `#${run.search_profile_id}`}
                  </td>
                  <td className="px-3 py-2">{run.source}</td>
                  <td className="px-3 py-2">{run.jobs_found}</td>
                  <td className="px-3 py-2">{run.jobs_imported}</td>
                  <td className="px-3 py-2">{run.duplicates}</td>
                  <td className="px-3 py-2">{run.failed}</td>
                  <td className="px-3 py-2">{run.status}</td>
                  <td className="px-3 py-2">
                    {formatDuration(run.duration_seconds)}
                  </td>
                </tr>
              ))}
              {!loading && runs.length === 0 && (
                <tr>
                  <td
                    colSpan={9}
                    className="px-3 py-8 text-center text-slate-500"
                  >
                    No search runs yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <aside className="rounded-lg border border-border bg-card p-4 text-sm">
          <h2 className="font-semibold">Run details</h2>
          {!selected && (
            <p className="mt-2 text-slate-500">Click a run to view details.</p>
          )}
          {selected && (
            <dl className="mt-3 space-y-2">
              <div>
                <dt className="text-xs uppercase text-slate-500">Profile</dt>
                <dd>{selected.search_profile_name}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase text-slate-500">Source</dt>
                <dd>{selected.source}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase text-slate-500">Status</dt>
                <dd>{selected.status}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase text-slate-500">Counts</dt>
                <dd>
                  Found {selected.jobs_found} · Imported {selected.jobs_imported}{" "}
                  · Dupes {selected.duplicates} · Failed {selected.failed}
                </dd>
              </div>
              <div>
                <dt className="text-xs uppercase text-slate-500">Duration</dt>
                <dd>{formatDuration(selected.duration_seconds)}</dd>
              </div>
              {selected.error_message && (
                <div>
                  <dt className="text-xs uppercase text-slate-500">Error</dt>
                  <dd className="text-danger">{selected.error_message}</dd>
                </div>
              )}
              <Link
                href={`/jobs?search_profile_id=${selected.search_profile_id}`}
                className="inline-block text-accent underline"
              >
                View collected jobs
              </Link>
            </dl>
          )}
        </aside>
      </div>
    </div>
  );
};
