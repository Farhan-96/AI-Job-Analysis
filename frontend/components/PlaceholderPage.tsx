type PlaceholderPageProps = {
  title: string;
  description: string;
};

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight text-foreground">
        {title}
      </h1>
      <p className="mt-2 max-w-xl text-sm text-slate-600">{description}</p>
      <div className="mt-8 rounded-lg border border-dashed border-border bg-card p-8 text-sm text-slate-500">
        Placeholder — not implemented in Phase 1.
      </div>
    </div>
  );
}
