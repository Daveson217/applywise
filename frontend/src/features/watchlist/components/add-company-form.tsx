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
import { Loader2 } from "lucide-react";
import { useState } from "react";

import { useCreateWatchlistCompany } from "../hooks";

interface AddCompanyFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AddCompanyForm({ open, onOpenChange }: AddCompanyFormProps) {
  const [name, setName] = useState("");
  const [careersUrl, setCareersUrl] = useState("");
  const createMutation = useCreateWatchlistCompany();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;

    await createMutation.mutateAsync({
      name: name.trim(),
      careers_url: careersUrl.trim() || undefined,
    });

    setName("");
    setCareersUrl("");
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Company to Watchlist</DialogTitle>
          <DialogDescription>
            Enter a company name and optionally their careers page URL for
            automatic job monitoring.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="company-name">Company Name *</Label>
            <Input
              id="company-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Stripe"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="careers-url">Careers Page URL</Label>
            <Input
              id="careers-url"
              type="url"
              value={careersUrl}
              onChange={(e) => setCareersUrl(e.target.value)}
              placeholder="e.g. https://boards.greenhouse.io/stripe"
            />
            <p className="text-xs text-muted-foreground">
              We&apos;ll auto-detect the ATS platform and start monitoring for
              new postings.
            </p>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createMutation.isPending || !name.trim()}>
              {createMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Add Company
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
