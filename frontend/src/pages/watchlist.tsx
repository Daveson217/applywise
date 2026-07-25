import { WatchlistTable } from "@/features/watchlist/components/watchlist-table";

export function WatchlistPage() {
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

      <WatchlistTable />
    </div>
  );
}
