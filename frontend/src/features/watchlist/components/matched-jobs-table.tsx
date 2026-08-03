import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDistanceToNow } from "date-fns";
import { ExternalLink, RefreshCw, X } from "lucide-react";

import { useDismissMatch, useMatchedJobs, useRecheckMatches } from "../hooks";

export function MatchedJobsTable() {
  const { data, isLoading } = useMatchedJobs();
  const dismiss = useDismissMatch();
  const recheck = useRecheckMatches();

  const jobs = data?.results ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Jobs matching your alert filters across all watched companies. New
          matches appear here as monitoring runs; you also get a periodic
          email digest.
        </p>
        <Button
          variant="outline"
          size="sm"
          onClick={() => recheck.mutate()}
          disabled={recheck.isPending}
        >
          <RefreshCw
            className={`mr-2 h-4 w-4 ${recheck.isPending ? "animate-spin" : ""}`}
          />
          Re-check
        </Button>
      </div>

      <div className="rounded-lg border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-4 py-3 text-left font-medium">Role</th>
              <th className="hidden px-4 py-3 text-left font-medium md:table-cell">
                Company
              </th>
              <th className="hidden px-4 py-3 text-left font-medium lg:table-cell">
                Location
              </th>
              <th className="hidden px-4 py-3 text-left font-medium lg:table-cell">
                Match
              </th>
              <th className="hidden px-4 py-3 text-left font-medium lg:table-cell">
                Found
              </th>
              <th className="px-4 py-3 text-right font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <tr key={i} className="border-b">
                  {Array.from({ length: 6 }).map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <Skeleton className="h-5 w-full" />
                    </td>
                  ))}
                </tr>
              ))
            ) : jobs.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center">
                  <p className="text-lg font-medium text-muted-foreground">
                    No matching jobs yet
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Set your filters in Settings → Job Preferences, then wait
                    for monitoring to run (or hit Re-check).
                  </p>
                </td>
              </tr>
            ) : (
              jobs.map((job) => (
                <tr
                  key={job.id}
                  className="border-b transition-colors hover:bg-muted/30"
                >
                  <td className="px-4 py-3">
                    <a
                      href={job.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 font-medium text-primary hover:underline"
                    >
                      {job.title}
                      <ExternalLink className="h-3 w-3 shrink-0" />
                    </a>
                    <div className="text-xs text-muted-foreground md:hidden">
                      {job.company_name}
                    </div>
                  </td>
                  <td className="hidden px-4 py-3 md:table-cell">
                    {job.company_name}
                  </td>
                  <td className="hidden px-4 py-3 lg:table-cell">
                    {job.location || "—"}
                  </td>
                  <td className="hidden px-4 py-3 lg:table-cell">
                    {job.ai_relevance_score != null
                      ? `${Math.round(job.ai_relevance_score * 100)}%`
                      : "—"}
                  </td>
                  <td className="hidden px-4 py-3 text-muted-foreground lg:table-cell">
                    {job.matched_at
                      ? formatDistanceToNow(new Date(job.matched_at), {
                          addSuffix: true,
                        })
                      : "—"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => dismiss.mutate(job.id)}
                      title="Dismiss"
                      className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
