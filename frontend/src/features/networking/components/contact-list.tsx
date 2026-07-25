import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import type { Contact } from "@/types/networking";
import { format } from "date-fns";
import { ExternalLink, MoreHorizontal, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { useContacts, useDeleteContact } from "../hooks";
import { AddContactForm } from "./add-contact-form";
import { InteractionTimeline } from "./interaction-timeline";

const RELATIONSHIP_LABELS: Record<string, string> = {
  recruiter: "Recruiter",
  referral: "Referral",
  peer: "Peer",
  mentor: "Mentor",
  alumni: "Alumni",
  manager: "Hiring Manager",
  other: "Other",
};

export function ContactList() {
  const { data, isLoading } = useContacts();
  const deleteMutation = useDeleteContact();
  const [addOpen, setAddOpen] = useState(false);
  const [selected, setSelected] = useState<Contact | null>(null);

  const contacts = data?.results || [];

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setAddOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Contact
        </Button>
      </div>

      <div className="rounded-lg border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-4 py-3 text-left font-medium">Name</th>
              <th className="hidden px-4 py-3 text-left font-medium md:table-cell">
                Company
              </th>
              <th className="hidden px-4 py-3 text-left font-medium lg:table-cell">
                Role
              </th>
              <th className="px-4 py-3 text-left font-medium">Relationship</th>
              <th className="hidden px-4 py-3 text-left font-medium lg:table-cell">
                Last Touch
              </th>
              <th className="px-4 py-3 text-right font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <tr key={i} className="border-b">
                  {Array.from({ length: 6 }).map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <Skeleton className="h-5 w-full" />
                    </td>
                  ))}
                </tr>
              ))
            ) : contacts.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center">
                  <p className="text-lg font-medium text-muted-foreground">
                    No contacts yet
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Track recruiters, referrals, and networking contacts.
                  </p>
                  <Button onClick={() => setAddOpen(true)} className="mt-4">
                    <Plus className="mr-2 h-4 w-4" />
                    Add Your First Contact
                  </Button>
                </td>
              </tr>
            ) : (
              contacts.map((contact) => (
                <tr
                  key={contact.id}
                  className="cursor-pointer border-b transition-colors hover:bg-muted/30"
                  onClick={() => setSelected(contact)}
                >
                  <td className="px-4 py-3 font-medium">{contact.name}</td>
                  <td className="hidden px-4 py-3 md:table-cell">
                    {contact.company || "—"}
                  </td>
                  <td className="hidden px-4 py-3 text-muted-foreground lg:table-cell">
                    {contact.role || "—"}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant="secondary">
                      {RELATIONSHIP_LABELS[contact.relationship_type] ||
                        contact.relationship_type}
                    </Badge>
                  </td>
                  <td className="hidden px-4 py-3 text-muted-foreground lg:table-cell">
                    {contact.last_interaction_date
                      ? format(
                          new Date(contact.last_interaction_date),
                          "MMM d, yyyy"
                        )
                      : "—"}
                  </td>
                  <td
                    className="px-4 py-3 text-right"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <button className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground">
                          <MoreHorizontal className="h-4 w-4" />
                        </button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        {contact.linkedin_url && (
                          <DropdownMenuItem
                            onClick={() =>
                              window.open(contact.linkedin_url, "_blank")
                            }
                          >
                            <ExternalLink className="mr-2 h-4 w-4" />
                            Open LinkedIn
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => deleteMutation.mutate(contact.id)}
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <AddContactForm open={addOpen} onOpenChange={setAddOpen} />

      <Dialog open={!!selected} onOpenChange={(o) => !o && setSelected(null)}>
        <DialogContent className="max-h-[80vh] overflow-y-auto sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{selected?.name}</DialogTitle>
          </DialogHeader>
          {selected && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-xs text-muted-foreground">Company</p>
                  <p>{selected.company || "—"}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Role</p>
                  <p>{selected.role || "—"}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Email</p>
                  <p className="truncate">{selected.email || "—"}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Relationship</p>
                  <Badge variant="secondary">
                    {RELATIONSHIP_LABELS[selected.relationship_type]}
                  </Badge>
                </div>
              </div>
              {selected.notes && (
                <div>
                  <p className="mb-1 text-xs text-muted-foreground">Notes</p>
                  <p className="text-sm">{selected.notes}</p>
                </div>
              )}
              <InteractionTimeline contactId={selected.id} />
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
