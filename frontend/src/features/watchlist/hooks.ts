import type { WatchlistRule } from "@/types/watchlist";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { watchlistApi } from "./api";

export function useWatchlist() {
  return useQuery({
    queryKey: ["watchlist"],
    queryFn: () => watchlistApi.list().then((r) => r.data),
  });
}

export function useWatchlistCompany(id: number) {
  return useQuery({
    queryKey: ["watchlist", id],
    queryFn: () => watchlistApi.get(id).then((r) => r.data),
    enabled: !!id,
  });
}

export function useCreateWatchlistCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; careers_url?: string }) =>
      watchlistApi.create(data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlist"] });
    },
  });
}

export function useDeleteWatchlistCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => watchlistApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlist"] });
    },
  });
}

export function useWatchlistPostings(companyId: number) {
  return useQuery({
    queryKey: ["watchlist", companyId, "postings"],
    queryFn: () => watchlistApi.getPostings(companyId).then((r) => r.data),
    enabled: !!companyId,
  });
}

export function usePreviewWatchlistImport() {
  return useMutation({
    mutationFn: (file: File) =>
      watchlistApi.previewImport(file).then((r) => r.data),
  });
}

export function useCommitWatchlistImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (rows: Array<{ name: string; careers_url: string }>) =>
      watchlistApi.commitImport(rows).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlist"] });
    },
  });
}

export function useCreateRule(companyId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Omit<WatchlistRule, "id">) =>
      watchlistApi.createRule(companyId, data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlist"] });
    },
  });
}

export function useUpdateRule(companyId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ ruleId, data }: { ruleId: number; data: Partial<WatchlistRule> }) =>
      watchlistApi.updateRule(companyId, ruleId, data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlist"] });
    },
  });
}

export function useDeleteRule(companyId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (ruleId: number) => watchlistApi.deleteRule(companyId, ruleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlist"] });
    },
  });
}

export function useUpdateWatchlistCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: number;
      data: { name?: string; careers_url?: string };
    }) => watchlistApi.update(id, data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlist"] });
    },
  });
}

export function useProbeByName() {
  return useMutation({
    mutationFn: (name: string) => watchlistApi.probeByName(name).then((r) => r.data),
  });
}

export function useMatchedJobs() {
  return useQuery({
    queryKey: ["watchlist", "matches"],
    queryFn: () => watchlistApi.getMatches().then((r) => r.data),
    // Keep the feed fresh while monitoring runs in the background.
    refetchInterval: 30000,
  });
}

export function useDismissMatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => watchlistApi.dismissMatch(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlist", "matches"] });
    },
  });
}

export function useRecheckMatches() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => watchlistApi.recheckMatches().then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlist", "matches"] });
    },
  });
}
