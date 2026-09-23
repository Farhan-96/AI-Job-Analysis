"use client";

import { JobStats } from "@/lib/api";

type Props = {
  stats: JobStats;
};

export const JobStatsCards = ({ stats }: Props) => {
  const items: [string, number][] = [
    ["Total Jobs", stats.total],
    ["New", stats.new],
    ["Analyzed", stats.analyzed],
    ["Shortlisted", stats.shortlisted],
    ["Rejected", stats.rejected],
  ];

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
      {items.map(([label, value]) => (
        <div
          key={label}
          className="rounded-lg border border-border bg-card p-4 shadow-sm"
        >
          <p className="text-xs text-slate-500">{label}</p>
          <p className="mt-1 text-2xl font-semibold">{value}</p>
        </div>
      ))}
    </div>
  );
};
