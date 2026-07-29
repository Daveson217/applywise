import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { WatchlistCompany, WatchlistRule } from "@/types/watchlist";
import { Loader2, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { useCreateRule, useDeleteRule, useUpdateRule } from "../hooks";

const JOB_TYPE_OPTIONS = [
  { value: "internship", label: "Internship" },
  { value: "new_grad", label: "New Grad" },
  { value: "full_time", label: "Full-Time" },
  { value: "contract", label: "Contract" },
  { value: "part_time", label: "Part-Time" },
] as const;

interface RulesDialogProps {
  company: WatchlistCompany | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function splitList(v: string): string[] {
  return v
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

function joinList(v: string[] | undefined): string {
  return (v ?? []).join(", ");
}

// Form state kept as strings so users can type commas freely; converted on save.
interface FormState {
  keywords: string;
  exclude_keywords: string;
  locations: string;
  job_types: string[];
  search_description: boolean;
  is_active: boolean;
}

const EMPTY_FORM: FormState = {
  keywords: "",
  exclude_keywords: "",
  locations: "",
  job_types: [],
  search_description: false,
  is_active: true,
};

function ruleToForm(rule: WatchlistRule): FormState {
  return {
    keywords: joinList(rule.keywords),
    exclude_keywords: joinList(rule.exclude_keywords),
    locations: joinList(rule.locations),
    job_types: rule.job_types ?? [],
    search_description: rule.search_description,
    is_active: rule.is_active,
  };
}

function formToPayload(form: FormState): Omit<WatchlistRule, "id"> {
  return {
    keywords: splitList(form.keywords),
    exclude_keywords: splitList(form.exclude_keywords),
    locations: splitList(form.locations),
    job_types: form.job_types,
    search_description: form.search_description,
    is_active: form.is_active,
  };
}

export function RulesDialog({ company, open, onOpenChange }: RulesDialogProps) {
  // Editing state: null = "adding new", number = editing rule id.
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);

  const companyId = company?.id ?? 0;
  const createMutation = useCreateRule(companyId);
  const updateMutation = useUpdateRule(companyId);
  const deleteMutation = useDeleteRule(companyId);

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  function resetForm() {
    setEditingId(null);
    setForm(EMPTY_FORM);
  }

  function startEdit(rule: WatchlistRule) {
    setEditingId(rule.id);
    setForm(ruleToForm(rule));
  }

  function toggleJobType(value: string) {
    setForm((f) => ({
      ...f,
      job_types: f.job_types.includes(value)
        ? f.job_types.filter((v) => v !== value)
        : [...f.job_types, value],
    }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!company) return;
    const payload = formToPayload(form);
    if (editingId === null) {
      await createMutation.mutateAsync(payload);
    } else {
      await updateMutation.mutateAsync({ ruleId: editingId, data: payload });
    }
    resetForm();
  }

  if (!company) return null;

  const rules = company.rules ?? [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Alert rules — {company.name}</DialogTitle>
          <DialogDescription>
            Rules narrow which new postings trigger a notification. Empty
            fields fall back to your global Job Preferences.
          </DialogDescription>
        </DialogHeader>

        {rules.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium">Existing rules</h3>
            <ul className="space-y-2">
              {rules.map((rule) => (
                <li
                  key={rule.id}
                  className="flex items-start justify-between gap-3 rounded-md border p-3 text-sm"
                >
                  <div className="min-w-0 space-y-0.5">
                    <div>
                      <span className="text-muted-foreground">Keywords:</span>{" "}
                      {rule.keywords.length ? rule.keywords.join(", ") : "—"}
                    </div>
                    {rule.exclude_keywords?.length > 0 && (
                      <div>
                        <span className="text-muted-foreground">Exclude:</span>{" "}
                        {rule.exclude_keywords.join(", ")}
                      </div>
                    )}
                    {rule.locations.length > 0 && (
                      <div>
                        <span className="text-muted-foreground">
                          Locations:
                        </span>{" "}
                        {rule.locations.join(", ")}
                      </div>
                    )}
                    {rule.job_types.length > 0 && (
                      <div>
                        <span className="text-muted-foreground">Types:</span>{" "}
                        {rule.job_types.join(", ")}
                      </div>
                    )}
                    <div className="flex gap-2 pt-1 text-xs text-muted-foreground">
                      {rule.is_active ? "Active" : "Paused"}
                      {rule.search_description && " · searches description"}
                    </div>
                  </div>
                  <div className="flex shrink-0 gap-1">
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => startEdit(rule)}
                    >
                      Edit
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      className="text-destructive hover:text-destructive"
                      onClick={() => {
                        if (editingId === rule.id) resetForm();
                        deleteMutation.mutate(rule.id);
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 border-t pt-4">
          <h3 className="text-sm font-medium">
            {editingId === null ? "Add a rule" : "Edit rule"}
          </h3>

          <div className="space-y-2">
            <Label htmlFor="rule-keywords">Keywords</Label>
            <Input
              id="rule-keywords"
              placeholder="e.g. ml, backend"
              value={form.keywords}
              onChange={(e) =>
                setForm({ ...form, keywords: e.target.value })
              }
            />
            <p className="text-xs text-muted-foreground">
              Comma-separated. Synonyms expand automatically.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="rule-exclude">Exclude keywords</Label>
            <Input
              id="rule-exclude"
              placeholder="e.g. senior, staff"
              value={form.exclude_keywords}
              onChange={(e) =>
                setForm({ ...form, exclude_keywords: e.target.value })
              }
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="rule-locations">Locations</Label>
            <Input
              id="rule-locations"
              placeholder="e.g. remote, new york"
              value={form.locations}
              onChange={(e) =>
                setForm({ ...form, locations: e.target.value })
              }
            />
          </div>

          <div className="space-y-2">
            <Label>Job types</Label>
            <div className="flex flex-wrap gap-2">
              {JOB_TYPE_OPTIONS.map((opt) => {
                const checked = form.job_types.includes(opt.value);
                return (
                  <label
                    key={opt.value}
                    className="flex cursor-pointer items-center gap-2 rounded-md border border-input bg-background px-3 py-1.5 text-xs hover:bg-accent"
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleJobType(opt.value)}
                      className="h-3.5 w-3.5"
                    />
                    {opt.label}
                  </label>
                );
              })}
            </div>
          </div>

          <div className="space-y-2">
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.search_description}
                onChange={(e) =>
                  setForm({ ...form, search_description: e.target.checked })
                }
                className="h-4 w-4"
              />
              Also search inside job descriptions
            </label>
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(e) =>
                  setForm({ ...form, is_active: e.target.checked })
                }
                className="h-4 w-4"
              />
              Rule active
            </label>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            {editingId !== null && (
              <Button type="button" variant="outline" onClick={resetForm}>
                Cancel
              </Button>
            )}
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              {editingId === null ? (
                <>
                  <Plus className="mr-2 h-4 w-4" />
                  Add rule
                </>
              ) : (
                "Save changes"
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
