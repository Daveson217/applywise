import api from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

export interface ResourceQuota {
  used: number;
  limit: number | null;
}

export interface UsageSummary {
  /** True when tier limits are enforced. False in beta / testing mode. */
  payments_enabled: boolean;
  plan: string;
  resources: {
    applications: ResourceQuota;
    watchlist: ResourceQuota;
    cv_versions: ResourceQuota;
  };
  ai_monthly: {
    cover_letter: ResourceQuota;
    qa: ResourceQuota;
    ats_score: ResourceQuota;
  };
  providers: string[];
}

export function useUsage() {
  return useQuery({
    queryKey: ["billing", "usage"],
    queryFn: () => api.get<UsageSummary>("/billing/usage/").then((r) => r.data),
    refetchInterval: 60_000,
  });
}

/** Returns true if the resource is at or over its limit (null = unlimited). */
export function isQuotaExhausted(q: ResourceQuota | undefined): boolean {
  if (!q || q.limit === null) return false;
  return q.used >= q.limit;
}

/** Display string like "12 / 25" or "12" if unlimited. */
export function formatUsage(q: ResourceQuota | undefined): string {
  if (!q) return "—";
  if (q.limit === null) return String(q.used);
  return `${q.used} / ${q.limit}`;
}
