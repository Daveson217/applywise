import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { cvApi } from "./api";

export function useCVVersions() {
  return useQuery({
    queryKey: ["cv"],
    queryFn: () => cvApi.list().then((r) => r.data),
  });
}

export function useUploadCV() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ name, file }: { name: string; file: File }) =>
      cvApi.upload(name, file).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cv"] });
    },
  });
}

export function useDeleteCV() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => cvApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cv"] });
    },
  });
}

export function useSetDefaultCV() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => cvApi.setDefault(id).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cv"] });
    },
  });
}
