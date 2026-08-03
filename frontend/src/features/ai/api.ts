import api from "@/lib/api";
import type { PaginatedResponse } from "@/types/api";

export interface ProviderInfo {
  name: string;
  display_name: string;
  models: string[];
}

export interface CoverLetter {
  id: number;
  application: number | null;
  cv_version: number | null;
  content: string;
  job_description: string;
  provider: string;
  model: string;
  prompt_settings: Record<string, string>;
  version_number: number;
  created_at: string;
}

export interface TaskResult {
  task_id: string;
  status: string;
  /** Signed short-lived token for SSE streaming (cover letter only) */
  stream_token?: string;
  /** Remaining monthly quota for this feature */
  quota_remaining?: number | null;
}

export interface AIUsage {
  by_feature: Array<{
    feature: string;
    total_input: number;
    total_output: number;
    count: number;
  }>;
  by_month: Array<{
    month: string;
    total_input: number;
    total_output: number;
  }>;
}

export const aiApi = {
  getProviders: () =>
    api.get<ProviderInfo[]>("/ai/providers/"),

  generateCoverLetter: (data: {
    job_description: string;
    cv_version_id: number;
    company: string;
    job_title: string;
    tone?: string;
    length?: string;
    emphasis?: string;
    notes?: string;
    provider?: string;
    model?: string;
    application_id?: number;
  }) => api.post<TaskResult>("/ai/cover-letter/", data),

  listCoverLetters: () =>
    api.get<PaginatedResponse<CoverLetter>>("/ai/cover-letters/"),

  deleteCoverLetter: (id: number) =>
    api.delete(`/ai/cover-letters/${id}/`),

  answerQuestion: (data: {
    question: string;
    cv_version_id: number;
    job_context?: string;
    character_limit?: number;
    provider?: string;
    model?: string;
  }) => api.post<TaskResult>("/ai/question-answer/", data),

  computeFitScore: (data: {
    job_description: string;
    cv_version_id: number;
    company?: string;
    job_title?: string;
    provider?: string;
    model?: string;
  }) => api.post<TaskResult>("/ai/fit-score/", data),

  computeATSScore: (data: {
    job_description: string;
    cv_version_id: number;
    provider?: string;
    model?: string;
  }) => api.post<TaskResult>("/ai/ats-score/", data),

  getUsage: () => api.get<AIUsage>("/ai/usage/"),

  getTaskResult: (taskId: string) =>
    api.get<{
      status: "pending" | "success" | "failure";
      // Result shape varies by task; each caller casts:
      // Q&A → { answer: string }
      // Fit  → { score, ... }
      // ATS  → { score, keywords, ... }
      result?: Record<string, unknown>;
      error?: string;
    }>(`/ai/task/${taskId}/`),

  listGenerations: (feature?: "qa" | "fit_score" | "ats_score") =>
    api.get<PaginatedResponse<AIGeneration>>(
      `/ai/generations/${feature ? `?feature=${feature}` : ""}`
    ),

  deleteGeneration: (id: number) =>
    api.delete(`/ai/generations/${id}/`),
};

export interface AIGeneration {
  id: number;
  feature: "qa" | "fit_score" | "ats_score";
  title: string;
  input: Record<string, unknown>;
  result: Record<string, unknown>;
  provider: string;
  model: string;
  created_at: string;
}
