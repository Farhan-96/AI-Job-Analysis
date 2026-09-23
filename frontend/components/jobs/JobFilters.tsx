"use client";

import { ResumeProfile } from "@/lib/api";
import { Filters, INPUT_CLASS } from "@/components/jobs/types";

type Props = {
  filters: Filters;
  profiles: ResumeProfile[];
  onChange: (next: Filters) => void;
};

export const JobFilters = ({ filters, profiles, onChange }: Props) => {
  const set = (key: keyof Filters, value: string) =>
    onChange({ ...filters, [key]: value });

  return (
    <div className="grid gap-3 rounded-lg border border-border bg-card p-4 sm:grid-cols-3 lg:grid-cols-7">
      <select
        className={INPUT_CLASS}
        value={filters.profile_id}
        onChange={(e) => set("profile_id", e.target.value)}
      >
        <option value="">Profile</option>
        {profiles.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}
          </option>
        ))}
      </select>
      <select
        className={INPUT_CLASS}
        value={filters.source}
        onChange={(e) => set("source", e.target.value)}
      >
        <option value="">Source</option>
        {["manual", "indeed", "linkedin", "company-careers", "csv", "json"].map(
          (s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ),
        )}
      </select>
      <select
        className={INPUT_CLASS}
        value={filters.status}
        onChange={(e) => set("status", e.target.value)}
      >
        <option value="">Status</option>
        {["new", "analyzed", "reviewed", "shortlisted", "rejected"].map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>
      <input
        className={INPUT_CLASS}
        placeholder="Location"
        value={filters.location}
        onChange={(e) => set("location", e.target.value)}
      />
      <select
        className={INPUT_CLASS}
        value={filters.remote_type}
        onChange={(e) => set("remote_type", e.target.value)}
      >
        <option value="">Remote type</option>
        {["remote", "hybrid", "onsite", "unknown"].map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>
      <input
        className={INPUT_CLASS}
        placeholder="Min score"
        type="number"
        min={0}
        max={100}
        value={filters.min_score}
        onChange={(e) => set("min_score", e.target.value)}
      />
      <input
        className={INPUT_CLASS}
        type="date"
        value={filters.date_from}
        onChange={(e) => set("date_from", e.target.value)}
        title="Discovered on/after"
      />
    </div>
  );
};
