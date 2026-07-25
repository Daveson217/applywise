import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  formatUsage,
  isQuotaExhausted,
  useUsage,
} from "@/features/billing/usage-api";
import { cn } from "@/lib/utils";
import { Link } from "react-router-dom";

interface QuotaRowProps {
  label: string;
  used: number;
  limit: number | null;
}

function QuotaRow({ label, used, limit }: QuotaRowProps) {
  const exhausted = isQuotaExhausted({ used, limit });
  const percentage = limit === null ? 0 : Math.min(100, (used / limit) * 100);

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span
          className={cn(
            "font-medium",
            exhausted ? "text-destructive" : "text-foreground"
          )}
        >
          {formatUsage({ used, limit })}
          {limit === null && (
            <span className="ml-1 text-xs text-muted-foreground">
              (unlimited)
            </span>
          )}
        </span>
      </div>
      {limit !== null && (
        <div className="h-1.5 overflow-hidden rounded-full bg-muted">
          <div
            className={cn(
              "h-full transition-all",
              exhausted ? "bg-destructive" : "bg-primary"
            )}
            style={{ width: `${percentage}%` }}
          />
        </div>
      )}
    </div>
  );
}

export function UsagePanel() {
  const { data, isLoading } = useUsage();

  if (isLoading) {
    return (
      <div className="max-w-2xl space-y-4">
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="max-w-2xl space-y-4">
      {!data.payments_enabled && (
        <div className="rounded-md border border-primary/30 bg-primary/5 px-4 py-3 text-sm">
          <strong className="text-primary">Beta mode:</strong>{" "}
          <span className="text-muted-foreground">
            all features are unlocked. Usage is tracked but not capped.
          </span>
        </div>
      )}

      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Current plan:</span>
        <Badge variant="secondary" className="capitalize">
          {data.plan}
        </Badge>
        {data.payments_enabled && data.plan === "free" && (
          <Link to="/pricing" className="ml-auto text-sm text-primary hover:underline">
            Upgrade →
          </Link>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Resource Limits</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <QuotaRow
            label="Applications"
            used={data.resources.applications.used}
            limit={data.resources.applications.limit}
          />
          <QuotaRow
            label="Watchlist Companies"
            used={data.resources.watchlist.used}
            limit={data.resources.watchlist.limit}
          />
          <QuotaRow
            label="CV Versions"
            used={data.resources.cv_versions.used}
            limit={data.resources.cv_versions.limit}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">AI Usage This Month</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <QuotaRow
            label="Cover Letters"
            used={data.ai_monthly.cover_letter.used}
            limit={data.ai_monthly.cover_letter.limit}
          />
          <QuotaRow
            label="Q&A Answers"
            used={data.ai_monthly.qa.used}
            limit={data.ai_monthly.qa.limit}
          />
          <QuotaRow
            label="ATS Scores"
            used={data.ai_monthly.ats_score.used}
            limit={data.ai_monthly.ats_score.limit}
          />
          <div className="border-t pt-3 text-xs text-muted-foreground">
            Available LLM providers:{" "}
            {data.providers.map((p) => (
              <Badge key={p} variant="outline" className="ml-1 capitalize">
                {p}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
