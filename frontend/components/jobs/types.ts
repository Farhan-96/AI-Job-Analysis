export type Filters = {
  status: string;
  source: string;
  remote_type: string;
  location: string;
  profile_id: string;
  min_score: string;
  date_from: string;
};

export const EMPTY_FILTERS: Filters = {
  status: "",
  source: "",
  remote_type: "",
  location: "",
  profile_id: "",
  min_score: "",
  date_from: "",
};

export const INPUT_CLASS =
  "rounded-md border border-border bg-white px-3 py-2 text-sm";

export const ACTION_BTN_CLASS =
  "rounded border border-border bg-white px-1.5 py-0.5 text-xs";
