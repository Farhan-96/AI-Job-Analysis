import { SystemStatus } from "@/components/SystemStatus";

const DashboardPage = () => (
  <div className="space-y-8">
    <header>
      <p className="text-sm font-medium text-accent">Overview</p>
      <h1 className="mt-1 text-3xl font-semibold tracking-tight text-foreground">
        AI Job Assistant
      </h1>
      <p className="mt-2 max-w-2xl text-sm text-slate-600">
        Phase 2 — verify services and review job matches from the Jobs page.
      </p>
    </header>
    <SystemStatus />
  </div>
);

export default DashboardPage;
