"use client";

import Link from "next/link";
import { JobListItem } from "@/lib/api";
import { ACTION_BTN_CLASS } from "@/components/jobs/types";

type Props = {
  jobs: JobListItem[];
  loading: boolean;
  onAnalyze: (id: number) => void;
  onStatus: (id: number, status: string) => void;
  onDelete: (id: number) => void;
};

export const JobsTable = ({
  jobs,
  loading,
  onAnalyze,
  onStatus,
  onDelete,
}: Props) => (
  <div className="overflow-x-auto rounded-lg border border-border bg-card shadow-sm">
    <table className="min-w-full text-left text-sm">
      <thead className="border-b border-border bg-slate-50 text-xs uppercase text-slate-500">
        <tr>
          <th className="px-3 py-2">Title</th>
          <th className="px-3 py-2">Company</th>
          <th className="px-3 py-2">Location</th>
          <th className="px-3 py-2">Source</th>
          <th className="px-3 py-2">Profile</th>
          <th className="px-3 py-2">Score</th>
          <th className="px-3 py-2">Status</th>
          <th className="px-3 py-2">Discovered</th>
          <th className="px-3 py-2">Actions</th>
        </tr>
      </thead>
      <tbody>
        {jobs.map((job) => (
          <tr key={job.id} className="border-b border-border last:border-0">
            <td className="px-3 py-2 font-medium">{job.title}</td>
            <td className="px-3 py-2">{job.company || "—"}</td>
            <td className="px-3 py-2">{job.location || "—"}</td>
            <td className="px-3 py-2">{job.source}</td>
            <td className="px-3 py-2">{job.top_match?.profile_name || "—"}</td>
            <td className="px-3 py-2">
              {job.top_match ? `${job.top_match.match_score}/100` : "—"}
            </td>
            <td className="px-3 py-2">{job.status}</td>
            <td className="px-3 py-2">
              {new Date(job.discovered_at).toLocaleDateString()}
            </td>
            <td className="px-3 py-2">
              <div className="flex flex-wrap gap-1">
                <Link className={ACTION_BTN_CLASS} href={`/jobs/${job.id}`}>
                  View
                </Link>
                <button
                  type="button"
                  className={ACTION_BTN_CLASS}
                  onClick={() => void onAnalyze(job.id)}
                >
                  Analyze
                </button>
                <button
                  type="button"
                  className={ACTION_BTN_CLASS}
                  onClick={() => void onStatus(job.id, "shortlisted")}
                >
                  Shortlist
                </button>
                <button
                  type="button"
                  className={ACTION_BTN_CLASS}
                  onClick={() => void onStatus(job.id, "rejected")}
                >
                  Reject
                </button>
                <button
                  type="button"
                  className={`${ACTION_BTN_CLASS} text-danger`}
                  onClick={() => void onDelete(job.id)}
                >
                  Delete
                </button>
              </div>
            </td>
          </tr>
        ))}
        {!loading && jobs.length === 0 && (
          <tr>
            <td colSpan={9} className="px-3 py-8 text-center text-slate-500">
              No jobs yet. Add one manually or seed sample data.
            </td>
          </tr>
        )}
      </tbody>
    </table>
  </div>
);
