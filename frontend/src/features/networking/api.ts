import api from "@/lib/api";
import type { PaginatedResponse } from "@/types/api";
import type {
  Contact,
  CreateContactData,
  CreateInteractionData,
  Interaction,
} from "@/types/networking";

export const networkingApi = {
  listContacts: () =>
    api.get<PaginatedResponse<Contact>>("/contacts/"),

  getContact: (id: number) => api.get<Contact>(`/contacts/${id}/`),

  createContact: (data: CreateContactData) =>
    api.post<Contact>("/contacts/", data),

  updateContact: (id: number, data: Partial<CreateContactData>) =>
    api.patch<Contact>(`/contacts/${id}/`, data),

  deleteContact: (id: number) => api.delete(`/contacts/${id}/`),

  listInteractions: (contactId: number) =>
    api.get<Interaction[]>(`/contacts/${contactId}/interactions/`),

  createInteraction: (contactId: number, data: CreateInteractionData) =>
    api.post<Interaction>(`/contacts/${contactId}/interactions/`, data),

  deleteInteraction: (contactId: number, id: number) =>
    api.delete(`/contacts/${contactId}/interactions/${id}/`),
};
