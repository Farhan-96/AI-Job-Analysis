import { SystemStatus } from "@/components/SystemStatus";

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <header>
        <p className="text-sm font-medium text-accent">Overview</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-foreground">
          AI Job Assistant
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-slate-600">
          Phase 1 foundation — verify that the frontend, backend, database, and
          worker stack are wired correctly before adding job automation.
        </p>
      </header>
      <SystemStatus />
    </div>
  );
}
