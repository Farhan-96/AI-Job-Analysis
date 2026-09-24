"use client";

import { ResumeProfile, SearchProfile } from "@/lib/api";
import { Filters, INPUT_CLASS } from "@/components/jobs/types";

type Props = {
  filters: Filters;
  profiles: ResumeProfile[];
  searchProfiles?: SearchProfile[];
  onChange: (next: Filters) => void;
};

export const JobFilters = ({
  filters,
  profiles,
  searchProfiles = [],
  onChange,
}: Props) => {
  const set = (key: keyof Filters, value: string) =>
    onChange({ ...filters, [key]: value });

  return (
    <div className="grid gap-3 rounded-lg border border-border bg-card p-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-9">
      <select
        className={INPUT_CLASS}
        value={filters.search_profile_id}
        onChange={(e) => set("search_profile_id", e.target.value)}
      >
        <option value="">Search profile</option>
        {searchProfiles.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}
          </option>
        ))}
      </select>
      <select
        className={INPUT_CLASS}
        value={filters.profile_id}
        onChange={(e) => set("profile_id", e.target.value)}
      >
        <option value="">Matched profile</option>
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
        {[
          "manual",
          "mock",
          "indeed",
          "linkedin",
          "company-careers",
          "csv",
          "json",
        ].map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
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
        placeholder="Min match score"
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
        title="Collected on/after"
      />
      <select
        className={INPUT_CLASS}
        value={filters.sort}
        onChange={(e) => set("sort", e.target.value)}
      >
        <option value="newest">Newest</option>
        <option value="match_score">Highest match score</option>
      </select>
    </div>
  );
};
