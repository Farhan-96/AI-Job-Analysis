export type ServiceHealth = {
  status: string;
  service: string;
};

export type DatabaseHealth = {
  status: string;
  database: string;
};

export type HealthCheckResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

export type JobMatchSummary = {
  id: number;
  profile_id: number;
  profile_name: string | null;
  profile_slug: string | null;
  match_score: number;
  role_match: string;
  recommendation: string;
};

export type JobListItem = {
  id: number;
  title: string;
  company: string | null;
  location: string | null;
  source: string;
  remote_type: string;
  status: string;
  discovered_at: string;
  posted_at: string | null;
  url: string | null;
  search_profile_id: number | null;
  search_profile_name: string | null;
  collected_automatically: boolean;
  top_match: JobMatchSummary | null;
};

export type JobSkill = {
  id: number;
  skill: string;
  source: string;
  confidence: number;
};

export type Job = {
  id: number;
  source: string;
  source_job_id: string;
  title: string;
  company: string | null;
  location: string | null;
  remote_type: string;
  url: string | null;
  description: string;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  employment_type: string | null;
  posted_at: string | null;
  discovered_at: string;
  status: string;
  normalized_title: string | null;
  extracted_experience_years: number | null;
  extracted_education: string | null;
  skills: JobSkill[];
  created_at: string;
  updated_at: string;
};

export type JobMatch = {
  id: number;
  job_id: number;
  profile_id: number;
  profile_name: string | null;
  profile_slug: string | null;
  match_score: number;
  matching_skills: string[];
  missing_skills: string[];
  matching_keywords: string[];
  missing_keywords: string[];
  experience_match: string;
  education_match: string;
  role_match: string;
  location_match: string;
  salary_match: string;
  analysis: string;
  recommendation: string;
  score_breakdown: Record<string, number> | null;
  created_at: string;
};

export type JobStats = {
  total: number;
  new: number;
  analyzed: number;
  reviewed: number;
  shortlisted: number;
  rejected: number;
  applied: number;
};

export type ResumeProfile = {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  resume_file: string;
  active: boolean;
};

export type JobCreateInput = {
  title: string;
  company?: string;
  location?: string;
  url?: string;
  description: string;
  source?: string;
  source_job_id?: string;
  employment_type?: string;
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;
};

export type ImportJobItem = {
  source_job_id?: string;
  title: string;
  company?: string;
  location?: string;
  url?: string;
  description?: string;
  employment_type?: string;
  remote_type?: string;
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;
};

export type JobImportRequest = {
  source: string;
  jobs: ImportJobItem[];
};

export type JobImportResult = {
  imported: number;
  duplicates: number;
  failed: number;
  total_rows: number | null;
  errors: string[];
  import_id: number | null;
};

export type JobImportHistoryItem = {
  id: number;
  source: string;
  import_type: string;
  total_count: number;
  imported_count: number;
  duplicate_count: number;
  failed_count: number;
  error_summary: string | null;
  created_at: string;
};

export type SearchProfile = {
  id: number;
  name: string;
  slug: string;
  enabled: boolean;
  keywords: string[];
  locations: string[];
  remote_types: string[];
  source: string;
  schedule_enabled: boolean;
  schedule_interval_minutes: number;
  last_run_at: string | null;
  resume_profile_id: number | null;
  resume_profile_name: string | null;
  resume_profile_slug: string | null;
  created_at: string;
  updated_at: string;
  last_run_status: string | null;
  last_jobs_found: number | null;
  last_jobs_imported: number | null;
  last_duplicates: number | null;
};

export type SearchProfileInput = {
  name: string;
  slug?: string;
  keywords: string[];
  locations: string[];
  remote_types?: string[];
  source?: string;
  enabled?: boolean;
  schedule_enabled?: boolean;
  schedule_interval_minutes?: number;
  resume_profile_id?: number | null;
};

export type SearchProfileUpdate = Partial<SearchProfileInput> & {
  clear_resume_profile?: boolean;
};

export type SearchRun = {
  id: number;
  search_profile_id: number;
  search_profile_name: string | null;
  search_profile_slug: string | null;
  source: string;
  started_at: string;
  completed_at: string | null;
  status: "running" | "completed" | "failed";
  jobs_found: number;
  jobs_imported: number;
  duplicates: number;
  failed: number;
  error_message: string | null;
  duration_seconds: number | null;
};

export type SearchRunAccepted = {
  run_id: number;
  status: string;
  message: string;
};
