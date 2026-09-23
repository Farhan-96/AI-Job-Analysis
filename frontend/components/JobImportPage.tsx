"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  JobImportHistoryItem,
  JobImportResult,
  fetchImportHistory,
  importJobsCsv,
  importJobsJson,
  importJobsManual,
} from "@/lib/api";

const INPUT =
  "mt-1 w-full rounded-md border border-border bg-white px-3 py-2 text-sm";
const LABEL = "block text-xs font-medium uppercase tracking-wide text-slate-500";
const CARD = "rounded-lg border border-border bg-card p-5";

const ResultBanner = ({ result }: { result: JobImportResult | null }) => {
  if (!result) return null;
  return (
    <div className="rounded-md border border-border bg-white px-4 py-3 text-sm">
      <p>
        Imported: <strong>{result.imported}</strong>
        {" · "}
        Duplicates: <strong>{result.duplicates}</strong>
        {" · "}
        Failed: <strong>{result.failed}</strong>
        {result.total_rows != null && (
          <>
            {" · "}
            Total rows: <strong>{result.total_rows}</strong>
          </>
        )}
      </p>
      {result.errors.length > 0 && (
        <ul className="mt-2 list-disc pl-5 text-danger">
          {result.errors.slice(0, 5).map((err) => (
            <li key={err}>{err}</li>
          ))}
        </ul>
      )}
    </div>
  );
};

export const JobImportPage = () => {
  const [manualResult, setManualResult] = useState<JobImportResult | null>(null);
  const [csvResult, setCsvResult] = useState<JobImportResult | null>(null);
  const [jsonResult, setJsonResult] = useState<JobImportResult | null>(null);
  const [history, setHistory] = useState<JobImportHistoryItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const loadHistory = useCallback(async () => {
    const result = await fetchImportHistory();
    if (result.ok) setHistory(result.data);
  }, []);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  const handleManual = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setManualResult(null);
    const form = new FormData(event.currentTarget);
    const salaryRaw = String(form.get("salary") || "").trim();
    let salary_min: number | undefined;
    let salary_max: number | undefined;
    if (salaryRaw.includes("-")) {
      const [lo, hi] = salaryRaw.split("-").map((p) => p.trim());
      salary_min = lo ? Number(lo) : undefined;
      salary_max = hi ? Number(hi) : undefined;
    } else if (salaryRaw) {
      salary_min = Number(salaryRaw);
    }

    const result = await importJobsManual({
      source: String(form.get("source") || "manual"),
      jobs: [
        {
          source_job_id: String(form.get("source_job_id") || "") || undefined,
          title: String(form.get("title") || ""),
          company: String(form.get("company") || "") || undefined,
          location: String(form.get("location") || "") || undefined,
          url: String(form.get("url") || "") || undefined,
          description: String(form.get("description") || ""),
          employment_type: String(form.get("employment_type") || "") || undefined,
          salary_min: Number.isFinite(salary_min) ? salary_min : undefined,
          salary_max: Number.isFinite(salary_max) ? salary_max : undefined,
        },
      ],
    });
    setBusy(false);
    if (!result.ok) {
      setError(result.error);
      return;
    }
    setManualResult(result.data);
    event.currentTarget.reset();
    await loadHistory();
  };

  const handleFile = async (
    kind: "csv" | "json",
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    const file = form.get("file");
    if (!(file instanceof File) || file.size === 0) {
      setError("Choose a file first");
      setBusy(false);
      return;
    }
    const result =
      kind === "csv" ? await importJobsCsv(file) : await importJobsJson(file);
    setBusy(false);
    if (!result.ok) {
      setError(result.error);
      return;
    }
    if (kind === "csv") setCsvResult(result.data);
    else setJsonResult(result.data);
    event.currentTarget.reset();
    await loadHistory();
  };

  return (
    <div className="space-y-8">
      <header>
        <p className="text-sm font-medium text-accent">Phase 3 · Step 1</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight">Job Import</h1>
        <p className="mt-2 max-w-2xl text-sm text-slate-600">
          Import jobs from manual entry, CSV, or JSON. New jobs are stored with
          status <code className="text-xs">new</code> and analyzed later by the
          worker — large imports stay fast.
        </p>
      </header>

      {error && <p className="text-sm text-danger">{error}</p>}

      <section className={CARD}>
        <h2 className="text-lg font-semibold">Manual Job</h2>
        <form className="mt-4 grid gap-3 sm:grid-cols-2" onSubmit={(e) => void handleManual(e)}>
          <label className={LABEL}>
            Source
            <select name="source" className={INPUT} defaultValue="indeed">
              <option value="manual">manual</option>
              <option value="indeed">indeed</option>
              <option value="linkedin">linkedin</option>
              <option value="company-careers">company-careers</option>
            </select>
          </label>
          <label className={LABEL}>
            Job ID
            <input name="source_job_id" className={INPUT} placeholder="12345" />
          </label>
          <label className={LABEL}>
            Title
            <input name="title" className={INPUT} required placeholder="React Native Developer" />
          </label>
          <label className={LABEL}>
            Company
            <input name="company" className={INPUT} placeholder="Example Company" />
          </label>
          <label className={LABEL}>
            Location
            <input name="location" className={INPUT} placeholder="Islamabad" />
          </label>
          <label className={LABEL}>
            Employment Type
            <input name="employment_type" className={INPUT} placeholder="Full-time" />
          </label>
          <label className={`${LABEL} sm:col-span-2`}>
            URL
            <input name="url" className={INPUT} placeholder="https://example.com/job" />
          </label>
          <label className={LABEL}>
            Salary
            <input name="salary" className={INPUT} placeholder="80000-120000" />
          </label>
          <label className={`${LABEL} sm:col-span-2`}>
            Description
            <textarea name="description" className={INPUT} rows={4} required />
          </label>
          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={busy}
              className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
            >
              Import Job
            </button>
          </div>
        </form>
        <div className="mt-4">
          <ResultBanner result={manualResult} />
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className={CARD}>
          <h2 className="text-lg font-semibold">CSV Import</h2>
          <p className="mt-1 text-sm text-slate-600">
            Columns: source, source_job_id, title, company, location, remote_type,
            url, description, salary_*, employment_type, posted_at
          </p>
          <form className="mt-4 space-y-3" onSubmit={(e) => void handleFile("csv", e)}>
            <input name="file" type="file" accept=".csv,text/csv" className="text-sm" />
            <button
              type="submit"
              disabled={busy}
              className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
            >
              Import CSV
            </button>
          </form>
          <div className="mt-4">
            <ResultBanner result={csvResult} />
          </div>
        </section>

        <section className={CARD}>
          <h2 className="text-lg font-semibold">JSON Import</h2>
          <p className="mt-1 text-sm text-slate-600">
            Accepts an array of jobs or {"{ source, jobs: [...] }"}.
          </p>
          <form className="mt-4 space-y-3" onSubmit={(e) => void handleFile("json", e)}>
            <input
              name="file"
              type="file"
              accept=".json,application/json"
              className="text-sm"
            />
            <button
              type="submit"
              disabled={busy}
              className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
            >
              Import JSON
            </button>
          </form>
          <div className="mt-4">
            <ResultBanner result={jsonResult} />
          </div>
        </section>
      </div>

      <section className={CARD}>
        <h2 className="text-lg font-semibold">Import History</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-border text-xs uppercase text-slate-500">
              <tr>
                <th className="px-2 py-2">Date</th>
                <th className="px-2 py-2">Source</th>
                <th className="px-2 py-2">Type</th>
                <th className="px-2 py-2">Total</th>
                <th className="px-2 py-2">Imported</th>
                <th className="px-2 py-2">Duplicates</th>
                <th className="px-2 py-2">Failed</th>
              </tr>
            </thead>
            <tbody>
              {history.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-2 py-4 text-slate-500">
                    No imports yet.
                  </td>
                </tr>
              )}
              {history.map((row) => (
                <tr key={row.id} className="border-b border-border/60">
                  <td className="px-2 py-2 whitespace-nowrap">
                    {new Date(row.created_at).toLocaleString()}
                  </td>
                  <td className="px-2 py-2">{row.source}</td>
                  <td className="px-2 py-2">{row.import_type}</td>
                  <td className="px-2 py-2">{row.total_count}</td>
                  <td className="px-2 py-2">{row.imported_count}</td>
                  <td className="px-2 py-2">{row.duplicate_count}</td>
                  <td className="px-2 py-2">{row.failed_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
