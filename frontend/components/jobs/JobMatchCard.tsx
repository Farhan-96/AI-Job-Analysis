"use client";

import { JobMatch } from "@/lib/api";
import { InfoField, TagList } from "@/components/jobs/InfoField";

type Props = {
  match: JobMatch;
};

export const JobMatchCard = ({ match }: Props) => (
  <article className="rounded-lg border border-border bg-card p-5 shadow-sm">
    <div className="flex flex-wrap items-baseline justify-between gap-2">
      <h3 className="text-lg font-semibold">
        {match.profile_name || `Profile #${match.profile_id}`}
      </h3>
      <p className="text-2xl font-semibold text-accent">
        {match.match_score}/100
      </p>
    </div>
    <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
      <InfoField label="Role Match" value={match.role_match} />
      <InfoField label="Experience" value={match.experience_match} />
      <InfoField label="Education" value={match.education_match} />
      <InfoField label="Location" value={match.location_match} />
      <InfoField label="Recommendation" value={match.recommendation} />
    </div>
    <div className="mt-4 grid gap-4 sm:grid-cols-2">
      <TagList title="Matching Skills" items={match.matching_skills} />
      <TagList title="Missing Skills" items={match.missing_skills} tone="warn" />
      <TagList title="Matching Keywords" items={match.matching_keywords} />
      <TagList title="Missing Keywords" items={match.missing_keywords} />
    </div>
    {match.score_breakdown && (
      <div className="mt-4">
        <h4 className="text-sm font-medium text-slate-500">Score breakdown</h4>
        <ul className="mt-2 grid gap-1 text-sm sm:grid-cols-5">
          {Object.entries(match.score_breakdown).map(([key, value]) => (
            <li key={key}>
              {key}: {value}
            </li>
          ))}
        </ul>
      </div>
    )}
    <p className="mt-4 text-sm leading-relaxed text-slate-700">
      {match.analysis}
    </p>
  </article>
);
