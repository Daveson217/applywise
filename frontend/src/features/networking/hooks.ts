import type {
  CreateContactData,
  CreateInteractionData,
} from "@/types/networking";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { networkingApi } from "./api";

export function useContacts() {
  return useQuery({
    queryKey: ["contacts"],
    queryFn: () => networkingApi.listContacts().then((r) => r.data),
  });
}

export function useContact(id: number) {
  return useQuery({
    queryKey: ["contacts", id],
    queryFn: () => networkingApi.getContact(id).then((r) => r.data),
    enabled: !!id,
  });
}

export function useCreateContact() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateContactData) =>
      networkingApi.createContact(data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["contacts"] });
    },
  });
}

export function useDeleteContact() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => networkingApi.deleteContact(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["contacts"] });
    },
  });
}

export function useInteractions(contactId: number) {
  return useQuery({
    queryKey: ["contacts", contactId, "interactions"],
    queryFn: () => networkingApi.listInteractions(contactId).then((r) => r.data),
    enabled: !!contactId,
  });
}

export function useCreateInteraction(contactId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateInteractionData) =>
      networkingApi.createInteraction(contactId, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["contacts", contactId, "interactions"] });
      qc.invalidateQueries({ queryKey: ["contacts"] });
    },
  });
}
