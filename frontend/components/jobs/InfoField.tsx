"use client";

type InfoProps = {
  label: string;
  value: React.ReactNode;
};

export const InfoField = ({ label, value }: InfoProps) => (
  <div>
    <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
    <div className="mt-1 text-sm font-medium">{value}</div>
  </div>
);

type TagListProps = {
  title: string;
  items: string[];
  tone?: "warn";
};

export const TagList = ({ title, items, tone }: TagListProps) => (
  <div>
    <h4 className="text-sm font-medium text-slate-500">{title}</h4>
    <div className="mt-2 flex flex-wrap gap-2">
      {items.length === 0 && (
        <span className="text-xs text-slate-400">None</span>
      )}
      {items.map((item) => (
        <span
          key={item}
          className={`rounded-md border px-2 py-1 text-xs ${
            tone === "warn"
              ? "border-amber-200 bg-amber-50 text-amber-900"
              : "border-border bg-slate-50"
          }`}
        >
          {item}
        </span>
      ))}
    </div>
  </div>
);
