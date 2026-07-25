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
};
