import { Sidebar } from "@/components/Sidebar";

type AppShellProps = {
  children: React.ReactNode;
};

export const AppShell = ({ children }: AppShellProps) => (
  <div className="flex min-h-screen bg-background">
    <Sidebar />
    <main className="flex-1 overflow-auto">
      <div className="mx-auto max-w-5xl px-6 py-8">{children}</div>
    </main>
  </div>
);
