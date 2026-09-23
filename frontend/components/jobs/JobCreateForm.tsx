"use client";

import { FormEvent } from "react";
import { INPUT_CLASS } from "@/components/jobs/types";

type Props = {
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export const JobCreateForm = ({ onSubmit }: Props) => (
  <form
    onSubmit={onSubmit}
    className="space-y-3 rounded-lg border border-border bg-card p-5 shadow-sm"
  >
    <h2 className="text-base font-semibold">Add job manually</h2>
    <div className="grid gap-3 sm:grid-cols-2">
      <input name="title" required placeholder="Title" className={INPUT_CLASS} />
      <input name="company" placeholder="Company" className={INPUT_CLASS} />
      <input name="location" placeholder="Location" className={INPUT_CLASS} />
      <input name="url" placeholder="URL" className={INPUT_CLASS} />
      <input
        name="source"
        defaultValue="manual"
        placeholder="Source"
        className={INPUT_CLASS}
      />
      <input
        name="source_job_id"
        placeholder="Source job id (optional)"
        className={INPUT_CLASS}
      />
      <input
        name="employment_type"
        placeholder="Employment type"
        className={INPUT_CLASS}
      />
    </div>
    <textarea
      name="description"
      required
      rows={6}
      placeholder="Paste job description…"
      className={`w-full ${INPUT_CLASS}`}
    />
    <button
      type="submit"
      className="rounded-md bg-accent px-3 py-2 text-sm font-medium text-white"
    >
      Save job
    </button>
  </form>
);
