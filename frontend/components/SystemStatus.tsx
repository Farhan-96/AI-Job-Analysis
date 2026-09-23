"use client";

import { useEffect, useState } from "react";
import { StatusCard } from "@/components/StatusCard";
import {
  fetchDatabaseHealth,
  fetchServiceHealth,
} from "@/lib/api";

type CheckState = "loading" | "ok" | "error";

type ServiceState = {
  state: CheckState;
  detail: string;
};

const INITIAL: ServiceState = {
  state: "loading",
  detail: "Checking...",
};

export function SystemStatus() {
  const [backend, setBackend] = useState<ServiceState>(INITIAL);
  const [database, setDatabase] = useState<ServiceState>(INITIAL);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const [serviceResult, databaseResult] = await Promise.all([
        fetchServiceHealth(),
        fetchDatabaseHealth(),
      ]);

      if (cancelled) {
        return;
      }

      if (serviceResult.ok && serviceResult.data.status === "ok") {
        setBackend({
          state: "ok",
          detail: `Service: ${serviceResult.data.service}`,
        });
      } else {
        setBackend({
          state: "error",
          detail:
            !serviceResult.ok
              ? serviceResult.error
              : "Unexpected health response",
        });
      }

      if (
        databaseResult.ok &&
        databaseResult.data.status === "ok" &&
        databaseResult.data.database === "connected"
      ) {
        setDatabase({
          state: "ok",
          detail: "PostgreSQL connection verified",
        });
      } else {
        setDatabase({
          state: "error",
          detail:
            !databaseResult.ok
              ? databaseResult.error
              : "Database reported disconnected",
        });
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section>
      <h2 className="text-base font-semibold text-foreground">System Status</h2>
      <p className="mt-1 text-sm text-slate-600">
        Live checks against the FastAPI backend and PostgreSQL.
      </p>
      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <StatusCard
          title="Frontend"
          state="ok"
          detail="Next.js dashboard is running"
        />
        <StatusCard
          title="Backend"
          state={backend.state}
          detail={backend.detail}
        />
        <StatusCard
          title="Database"
          state={database.state}
          detail={database.detail}
        />
        <StatusCard
          title="Worker"
          state="ok"
          detail="Worker process is configured to run via Docker Compose"
        />
      </div>
    </section>
  );
}
