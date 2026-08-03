import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { WatchlistCompany } from "@/types/watchlist";
import { AlertCircle, Loader2, Wand2 } from "lucide-react";
import { useEffect, useState } from "react";

import {
  useCreateWatchlistCompany,
  useProbeByName,
  useUpdateWatchlistCompany,
} from "../hooks";

interface CompanyFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  // If provided → edit mode. Omit / null → create mode.
  company?: WatchlistCompany | null;
}

// Kept as `AddCompanyForm` name for backwards compat with existing callers,
// but this component handles both create and edit.
export function AddCompanyForm({
  open,
  onOpenChange,
  company = null,
}: CompanyFormProps) {
  const isEdit = company !== null;
  const [name, setName] = useState(company?.name ?? "");
  const [careersUrl, setCareersUrl] = useState(company?.careers_url ?? "");
  const [warning, setWarning] = useState<string | null>(null);

  const createMutation = useCreateWatchlistCompany();
  const updateMutation = useUpdateWatchlistCompany();
  const probeMutation = useProbeByName();

  const submitting = createMutation.isPending || updateMutation.isPending;

  // Reset local state whenever the dialog opens for a different company (or fresh create).
  useEffect(() => {
    if (open) {
      setName(company?.name ?? "");
      setCareersUrl(company?.careers_url ?? "");
      setWarning(null);
    }
  }, [open, company]);

  async function handleAutoDetect() {
    if (!name.trim()) return;
    setWarning(null);
    const result = await probeMutation.mutateAsync(name.trim());
    if (result.detected && result.board_url) {
      setCareersUrl(result.board_url);
    } else {
      setWarning(
        `Couldn't auto-detect an ATS for "${name}". Try pasting the URL from the company's careers page.`
      );
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setWarning(null);

    const payload = {
      name: name.trim(),
      careers_url: careersUrl.trim() || undefined,
    };

    const saved = isEdit
      ? await updateMutation.mutateAsync({ id: company.id, data: payload })
      : await createMutation.mutateAsync(payload);

    // Nudge user if the backend still couldn't figure out an ATS.
    if (!saved.ats_provider) {
      setWarning(
        "Saved, but we couldn't detect an ATS. This company won't be scraped until you provide a supported URL (e.g. boards.greenhouse.io/…, jobs.lever.co/…) or a name that matches a known provider."
      );
      // Leave the dialog open so the user sees the warning and can retry.
      return;
    }

    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Edit company" : "Add company to watchlist"}
          </DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Update the name or careers URL. Changing either re-runs ATS detection."
              : "Enter a company name and optionally their careers page URL for automatic job monitoring."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="company-name">Company name *</Label>
            <Input
              id="company-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Stripe"
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="careers-url">Careers page URL</Label>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                className="h-7 text-xs"
                disabled={!name.trim() || probeMutation.isPending}
                onClick={handleAutoDetect}
              >
                {probeMutation.isPending ? (
                  <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                ) : (
                  <Wand2 className="mr-1 h-3 w-3" />
                )}
                Try auto-detect
              </Button>
            </div>
            <Input
              id="careers-url"
              type="url"
              value={careersUrl}
              onChange={(e) => setCareersUrl(e.target.value)}
              placeholder="e.g. https://boards.greenhouse.io/stripe"
            />
            <p className="text-xs text-muted-foreground">
              Supported: Greenhouse, Lever, Ashby, Workable, SmartRecruiters.
              Auto-detect probes those providers using the company name.
            </p>
          </div>

          {warning && (
            <div className="flex items-start gap-2 rounded-md border border-yellow-200 bg-yellow-50 p-3 text-xs text-yellow-900 dark:border-yellow-900/50 dark:bg-yellow-900/20 dark:text-yellow-200">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <p>{warning}</p>
            </div>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={submitting || !name.trim()}>
              {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isEdit ? "Save changes" : "Add company"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
