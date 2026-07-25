import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2 } from "lucide-react";
import { useState } from "react";

import { useCreateContact } from "../hooks";

const RELATIONSHIP_OPTIONS = [
  { value: "recruiter", label: "Recruiter" },
  { value: "referral", label: "Referral" },
  { value: "peer", label: "Peer" },
  { value: "mentor", label: "Mentor" },
  { value: "alumni", label: "Alumni" },
  { value: "manager", label: "Hiring Manager" },
  { value: "other", label: "Other" },
];

interface AddContactFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AddContactForm({ open, onOpenChange }: AddContactFormProps) {
  const createMutation = useCreateContact();
  const [form, setForm] = useState({
    name: "",
    company: "",
    role: "",
    email: "",
    linkedin_url: "",
    relationship_type: "peer",
    notes: "",
  });

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) return;
    await createMutation.mutateAsync(form);
    setForm({
      name: "",
      company: "",
      role: "",
      email: "",
      linkedin_url: "",
      relationship_type: "peer",
      notes: "",
    });
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Contact</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Name *</Label>
            <Input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g. Jane Smith"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Company</Label>
              <Input
                value={form.company}
                onChange={(e) => setForm({ ...form, company: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Role</Label>
              <Input
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label>Relationship</Label>
            <select
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={form.relationship_type}
              onChange={(e) =>
                setForm({ ...form, relationship_type: e.target.value })
              }
            >
              {RELATIONSHIP_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <Label>Email</Label>
            <Input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label>LinkedIn URL</Label>
            <Input
              type="url"
              value={form.linkedin_url}
              onChange={(e) =>
                setForm({ ...form, linkedin_url: e.target.value })
              }
            />
          </div>
          <div className="space-y-2">
            <Label>Notes</Label>
            <textarea
              rows={2}
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
            />
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createMutation.isPending || !form.name.trim()}
            >
              {createMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Add Contact
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
