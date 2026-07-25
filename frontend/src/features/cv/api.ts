import api from "@/lib/api";
import type { PaginatedResponse } from "@/types/api";

export interface CVVersion {
  id: number;
  name: string;
  file: string;
  file_size: number;
  extracted_text: string;
  parsed_json: Record<string, unknown>;
  tags: string[];
  is_default: boolean;
  created_at: string;
}

export const cvApi = {
  list: () => api.get<PaginatedResponse<CVVersion>>("/cv/"),

  get: (id: number) => api.get<CVVersion>(`/cv/${id}/`),

  upload: (name: string, file: File) => {
    const formData = new FormData();
    formData.append("name", name);
    formData.append("file", file);
    return api.post<CVVersion>("/cv/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  delete: (id: number) => api.delete(`/cv/${id}/`),

  setDefault: (id: number) =>
    api.post<CVVersion>(`/cv/${id}/set_default/`),
};
