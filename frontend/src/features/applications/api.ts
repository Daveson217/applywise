import api from "@/lib/api";
import type { PaginatedResponse } from "@/types/api";
import type {
  Application,
  ApplicationActivity,
  ApplicationFilters,
  CreateApplicationData,
  Tag,
} from "@/types/application";

export const applicationsApi = {
  list: (params?: ApplicationFilters) =>
    api.get<PaginatedResponse<Application>>("/applications/", { params }),

  get: (id: number) => api.get<Application>(`/applications/${id}/`),

  create: (data: CreateApplicationData) =>
    api.post<Application>("/applications/", data),

  update: (id: number, data: Partial<CreateApplicationData>) =>
    api.patch<Application>(`/applications/${id}/`, data),

  delete: (id: number) => api.delete(`/applications/${id}/`),

  getActivity: (id: number) =>
    api.get<PaginatedResponse<ApplicationActivity>>(
      `/applications/${id}/activity/`
    ),

  bulkAction: (
    action: "status_change" | "delete",
    ids: number[],
    status?: string
  ) =>
    api.post<{ updated?: number; deleted?: number }>(
      "/applications/bulk-action/",
      { action, ids, status }
    ),

  previewImport: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post<{
      headers: string[];
      rows: Record<string, string>[];
      row_count: number;
    }>("/applications/import-csv/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  commitImport: (rows: Record<string, string>[]) => {
    const formData = new FormData();
    formData.append("commit", "true");
    formData.append("rows", JSON.stringify(rows));
    return api.post<{ created: number }>(
      "/applications/import-csv/",
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
  },

  dailyCounts: (days = 365) =>
    api.get<Array<{ date: string; count: number }>>(
      `/applications/daily-counts/?days=${days}`
    ),
};

export const tagsApi = {
  list: () => api.get<PaginatedResponse<Tag>>("/tags/"),

  create: (data: Omit<Tag, "id">) => api.post<Tag>("/tags/", data),

  update: (id: number, data: Partial<Tag>) =>
    api.patch<Tag>(`/tags/${id}/`, data),

  delete: (id: number) => api.delete(`/tags/${id}/`),
};
