"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ResumeProfile,
  SearchProfile,
  createSearchProfile,
  fetchProfiles,
  fetchSearchProfile,
  updateSearchProfile,
} from "@/lib/api";

const INPUT =
  "mt-1 w-full rounded-md border border-border bg-white px-3 py-2 text-sm";
const LABEL = "block text-xs font-medium uppercase tracking-wide text-slate-500";
const CARD = "rounded-lg border border-border bg-card p-5";

const linesToList = (value: string) =>
  value
    .split(/\n|,/)
    .map((part) => part.trim())
    .filter(Boolean);

type Props = {
  profileId?: number;
};

export const SearchProfileEditor = ({ profileId }: Props) => {
  const router = useRouter();
  const [resumeProfiles, setResumeProfiles] = useState<ResumeProfile[]>([]);
  const [loading, setLoading] = useState(Boolean(profileId));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [keywords, setKeywords] = useState("");
  const [locations, setLocations] = useState("");
  const [remoteTypes, setRemoteTypes] = useState("remote\nhybrid\nonsite\nunknown");
  const [source, setSource] = useState("mock");
  const [enabled, setEnabled] = useState(true);
  const [scheduleEnabled, setScheduleEnabled] = useState(false);
  const [intervalMinutes, setIntervalMinutes] = useState(60);
  const [resumeProfileId, setResumeProfileId] = useState("");

  const applyProfile = useCallback((profile: SearchProfile) => {
    setName(profile.name);
    setSlug(profile.slug);
    setKeywords(profile.keywords.join("\n"));
    setLocations(profile.locations.join("\n"));
    setRemoteTypes(profile.remote_types.join("\n"));
    setSource(profile.source);
    setEnabled(profile.enabled);
    setScheduleEnabled(profile.schedule_enabled);
    setIntervalMinutes(profile.schedule_interval_minutes);
    setResumeProfileId(
      profile.resume_profile_id != null ? String(profile.resume_profile_id) : "",
    );
  }, []);

  useEffect(() => {
    void (async () => {
      const profilesResult = await fetchProfiles();
      if (profilesResult.ok) setResumeProfiles(profilesResult.data);

      if (!profileId) {
        setLoading(false);
        return;
      }
      const result = await fetchSearchProfile(profileId);
      if (!result.ok) {
        setError(result.error);
        setLoading(false);
        return;
      }
      applyProfile(result.data);
      setLoading(false);
    })();
  }, [profileId, applyProfile]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setMessage(null);

    const payload = {
      name,
      slug: slug || undefined,
      keywords: linesToList(keywords),
      locations: linesToList(locations),
      remote_types: linesToList(remoteTypes),
      source,
      enabled,
      schedule_enabled: scheduleEnabled,
      schedule_interval_minutes: intervalMinutes,
      resume_profile_id: resumeProfileId ? Number(resumeProfileId) : null,
      clear_resume_profile: !resumeProfileId,
    };

    const result = profileId
      ? await updateSearchProfile(profileId, payload)
      : await createSearchProfile(payload);

    setSaving(false);
    if (!result.ok) {
      setError(result.error);
      return;
    }
    setMessage("Saved");
    if (!profileId) {
      router.push(`/jobs/search/${result.data.id}`);
      return;
    }
    applyProfile(result.data);
  };

  if (loading) {
    return <p className="text-sm text-slate-500">Loading profile…</p>;
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-accent">Job Search</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight">
            {profileId ? "Edit search profile" : "New search profile"}
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            Configure keywords, locations, source, and schedule. One profile =
            one independent search.
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
      {message && <p className="text-sm text-slate-600">{message}</p>}

      <form className={`${CARD} space-y-4`} onSubmit={(e) => void handleSubmit(e)}>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block">
            <span className={LABEL}>Name</span>
            <input
              className={INPUT}
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </label>
          <label className="block">
            <span className={LABEL}>Slug</span>
            <input
              className={INPUT}
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              disabled={Boolean(profileId)}
              placeholder="auto from name if empty"
            />
          </label>
        </div>

        <label className="block">
          <span className={LABEL}>Keywords (one per line)</span>
          <textarea
            className={INPUT}
            rows={8}
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            required
          />
        </label>

        <label className="block">
          <span className={LABEL}>Locations (one per line)</span>
          <textarea
            className={INPUT}
            rows={4}
            value={locations}
            onChange={(e) => setLocations(e.target.value)}
          />
        </label>

        <label className="block">
          <span className={LABEL}>Remote types (one per line)</span>
          <textarea
            className={INPUT}
            rows={3}
            value={remoteTypes}
            onChange={(e) => setRemoteTypes(e.target.value)}
          />
        </label>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <label className="block">
            <span className={LABEL}>Source</span>
            <select
              className={INPUT}
              value={source}
              onChange={(e) => setSource(e.target.value)}
            >
              <option value="mock">mock</option>
              <option value="indeed">indeed</option>
            </select>
          </label>
          <label className="block">
            <span className={LABEL}>Primary resume profile</span>
            <select
              className={INPUT}
              value={resumeProfileId}
              onChange={(e) => setResumeProfileId(e.target.value)}
            >
              <option value="">None</option>
              {resumeProfiles.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className={LABEL}>Schedule interval (minutes)</span>
            <input
              className={INPUT}
              type="number"
              min={1}
              value={intervalMinutes}
              onChange={(e) => setIntervalMinutes(Number(e.target.value) || 60)}
            />
          </label>
          <div className="flex flex-col justify-end gap-2 pb-1">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={enabled}
                onChange={(e) => setEnabled(e.target.checked)}
              />
              Enabled
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={scheduleEnabled}
                onChange={(e) => setScheduleEnabled(e.target.checked)}
              />
              Schedule enabled
            </label>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={saving}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </form>
    </div>
  );
};
