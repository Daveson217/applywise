import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { aiApi } from "./api";

export function useProviders() {
  return useQuery({
    queryKey: ["ai", "providers"],
    queryFn: () => aiApi.getProviders().then((r) => r.data),
  });
}

export function useCoverLetters() {
  return useQuery({
    queryKey: ["ai", "cover-letters"],
    queryFn: () => aiApi.listCoverLetters().then((r) => r.data),
  });
}

export function useGenerateCoverLetter() {
  return useMutation({
    mutationFn: (data: Parameters<typeof aiApi.generateCoverLetter>[0]) =>
      aiApi.generateCoverLetter(data).then((r) => r.data),
  });
}

export function useAnswerQuestion() {
  return useMutation({
    mutationFn: aiApi.answerQuestion,
  });
}

export function useComputeFitScore() {
  return useMutation({
    mutationFn: aiApi.computeFitScore,
  });
}

export function useComputeATSScore() {
  return useMutation({
    mutationFn: aiApi.computeATSScore,
  });
}

export function useTaskResult(taskId: string | null) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["ai", "task", taskId],
    queryFn: () => aiApi.getTaskResult(taskId!).then((r) => r.data),
    enabled: !!taskId,
    // Poll every 2s while pending; stop once we have a terminal state.
    refetchInterval: (q) => {
      const data = q.state.data;
      if (!data) return 2000;
      return data.status === "pending" ? 2000 : false;
    },
    // Don't cache a stale result under the same taskId if the user resubmits.
    gcTime: 0,
  });

  // When a task succeeds, refresh any AI history lists so the new row shows up.
  useEffect(() => {
    if (query.data?.status === "success") {
      queryClient.invalidateQueries({ queryKey: ["ai", "generations"] });
    }
  }, [query.data?.status, queryClient]);

  return query;
}

export function useAIUsage() {
  return useQuery({
    queryKey: ["ai", "usage"],
    queryFn: () => aiApi.getUsage().then((r) => r.data),
  });
}

export function useDeleteCoverLetter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => aiApi.deleteCoverLetter(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai", "cover-letters"] });
    },
  });
}

export function useGenerations(feature?: "qa" | "fit_score" | "ats_score") {
  return useQuery({
    queryKey: ["ai", "generations", feature ?? "all"],
    queryFn: () => aiApi.listGenerations(feature).then((r) => r.data),
  });
}

export function useDeleteGeneration() {
  return useMutation({
    mutationFn: (id: number) => aiApi.deleteGeneration(id),
  });
}
