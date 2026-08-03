import api from "@/lib/api";
import type { PaginatedResponse } from "@/types/api";
import type {
  ATSDetectResult,
  JobPosting,
  MatchedJob,
  WatchlistCompany,
  WatchlistRule,
} from "@/types/watchlist";

export const watchlistApi = {
  list: () =>
    api.get<PaginatedResponse<WatchlistCompany>>("/watchlist/"),

  get: (id: number) => api.get<WatchlistCompany>(`/watchlist/${id}/`),

  create: (data: { name: string; careers_url?: string }) =>
    api.post<WatchlistCompany>("/watchlist/", data),

  update: (id: number, data: Partial<WatchlistCompany>) =>
    api.patch<WatchlistCompany>(`/watchlist/${id}/`, data),

  delete: (id: number) => api.delete(`/watchlist/${id}/`),

  detectAts: (url: string) =>
    api.post<ATSDetectResult>("/watchlist/detect-ats/", { url }),

  probeByName: (name: string) =>
    api.post<{
      detected: boolean;
      provider?: string;
      slug?: string;
      board_url?: string;
    }>("/watchlist/probe/", { name }),

  getPostings: (companyId: number) =>
    api.get<PaginatedResponse<JobPosting>>(
      `/watchlist/${companyId}/postings/`
    ),

  getMatches: () =>
    api.get<PaginatedResponse<MatchedJob>>("/watchlist/matches/"),

  dismissMatch: (id: number) =>
    api.post<{ dismissed: boolean }>(`/watchlist/matches/${id}/dismiss/`),

  recheckMatches: () =>
    api.post<{ rechecked: number }>("/watchlist/recheck/"),

  createRule: (companyId: number, data: Omit<WatchlistRule, "id">) =>
    api.post<WatchlistRule>(`/watchlist/${companyId}/rules/`, data),

  updateRule: (
    companyId: number,
    ruleId: number,
    data: Partial<WatchlistRule>
  ) => api.patch<WatchlistRule>(`/watchlist/${companyId}/rules/${ruleId}/`, data),

  deleteRule: (companyId: number, ruleId: number) =>
    api.delete(`/watchlist/${companyId}/rules/${ruleId}/`),

  previewImport: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post<{
      headers: string[];
      detected_headers: string[];
      rows: Array<{ name: string; careers_url: string }>;
      row_count: number;
    }>("/watchlist/import/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  commitImport: (rows: Array<{ name: string; careers_url: string }>) => {
    const formData = new FormData();
    formData.append("commit", "true");
    formData.append("rows", JSON.stringify(rows));
    return api.post<{
      created: number;
      skipped_duplicates: number;
      skipped_over_limit?: number;
      message?: string;
    }>("/watchlist/import/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};
