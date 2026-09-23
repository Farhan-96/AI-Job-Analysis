type StatusState = "loading" | "ok" | "error";

type StatusCardProps = {
  title: string;
  state: StatusState;
  detail: string;
};

const STATE_STYLES: Record<
  StatusState,
  { badge: string; label: string; color: string }
> = {
  loading: {
    badge: "Checking...",
    label: "…",
    color: "text-warning border-amber-200 bg-amber-50",
  },
  ok: {
    badge: "Connected",
    label: "✓",
    color: "text-success border-green-200 bg-green-50",
  },
  error: {
    badge: "Unavailable",
    label: "✗",
    color: "text-danger border-red-200 bg-red-50",
  },
};

export const StatusCard = ({ title, state, detail }: StatusCardProps) => {
  const styles = STATE_STYLES[state];

  return (
    <div className="rounded-lg border border-border bg-card p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-medium text-slate-500">{title}</h3>
          <p className="mt-2 text-lg font-semibold text-foreground">
            <span className="mr-2" aria-hidden>
              {styles.label}
            </span>
            {styles.badge}
          </p>
        </div>
        <span
          className={`rounded-md border px-2 py-1 text-xs font-medium ${styles.color}`}
        >
          {state === "loading" ? "pending" : state === "ok" ? "ok" : "error"}
        </span>
      </div>
      <p className="mt-3 text-sm text-slate-600">{detail}</p>
    </div>
  );
};
