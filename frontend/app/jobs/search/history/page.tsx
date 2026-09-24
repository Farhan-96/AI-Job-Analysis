import { Suspense } from "react";
import { SearchHistoryPage } from "@/components/SearchHistoryPage";

export default function SearchHistoryRoutePage() {
  return (
    <Suspense fallback={<p className="text-sm text-slate-500">Loading…</p>}>
      <SearchHistoryPage />
    </Suspense>
  );
}
