import { MatchedJobsTable } from "@/features/watchlist/components/matched-jobs-table";
import { WatchlistTable } from "@/features/watchlist/components/watchlist-table";
import { cn } from "@/lib/utils";
import { useState } from "react";

const tabs = [
  { id: "companies", label: "Companies" },
  { id: "matches", label: "Matched Jobs" },
];

export function WatchlistPage() {
  const [activeTab, setActiveTab] = useState("companies");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-[family-name:var(--font-display)] text-2xl font-bold">
          Watchlist
        </h1>
        <p className="text-muted-foreground">
          Monitor companies for new job postings.
        </p>
      </div>

      <div className="flex gap-2 border-b">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "border-b-2 px-4 py-2 text-sm font-medium transition-colors",
              activeTab === tab.id
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "companies" && <WatchlistTable />}
      {activeTab === "matches" && <MatchedJobsTable />}
    </div>
  );
}
