import type {
  ApplicationFilters,
  CreateApplicationData,
} from "@/types/application";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { applicationsApi, tagsApi } from "./api";

export function useApplications(filters?: ApplicationFilters) {
  return useQuery({
    queryKey: ["applications", filters],
    queryFn: () => applicationsApi.list(filters).then((r) => r.data),
  });
}

export function useApplication(id: number) {
  return useQuery({
    queryKey: ["applications", id],
    queryFn: () => applicationsApi.get(id).then((r) => r.data),
    enabled: !!id,
  });
}

export function useCreateApplication() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateApplicationData) =>
      applicationsApi.create(data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
  });
}

export function useUpdateApplication() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: number;
      data: Partial<CreateApplicationData>;
    }) => applicationsApi.update(id, data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
  });
}

export function useDeleteApplication() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => applicationsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
  });
}

export function useApplicationActivity(id: number) {
  return useQuery({
    queryKey: ["applications", id, "activity"],
    queryFn: () => applicationsApi.getActivity(id).then((r) => r.data),
    enabled: !!id,
  });
}

export function useTags() {
  return useQuery({
    queryKey: ["tags"],
    queryFn: () => tagsApi.list().then((r) => r.data),
  });
}

export function useBulkAction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      action,
      ids,
      status,
    }: {
      action: "status_change" | "delete";
      ids: number[];
      status?: string;
    }) => applicationsApi.bulkAction(action, ids, status).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
  });
}

export function useDailyCounts(days = 365) {
  return useQuery({
    queryKey: ["applications", "daily-counts", days],
    queryFn: () => applicationsApi.dailyCounts(days).then((r) => r.data),
  });
}

export function usePreviewImport() {
  return useMutation({
    mutationFn: (file: File) =>
      applicationsApi.previewImport(file).then((r) => r.data),
  });
}

export function useCommitImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (rows: Record<string, string>[]) =>
      applicationsApi.commitImport(rows).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
  });
}
