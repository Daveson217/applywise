import { useMutation, useQuery } from "@tanstack/react-query";

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

export function useAIUsage() {
  return useQuery({
    queryKey: ["ai", "usage"],
    queryFn: () => aiApi.getUsage().then((r) => r.data),
  });
}
