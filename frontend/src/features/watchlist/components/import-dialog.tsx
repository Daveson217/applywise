import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { AlertCircle, CheckCircle, Loader2, Upload } from "lucide-react";
import { useRef, useState } from "react";

import {
  useCommitWatchlistImport,
  usePreviewWatchlistImport,
} from "../hooks";

interface ImportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface PreviewRow {
  name: string;
  careers_url: string;
}

interface PreviewData {
  headers: string[];
  detected_headers: string[];
  rows: PreviewRow[];
  row_count: number;
}

interface CommitResult {
  created: number;
  skipped_duplicates: number;
  skipped_over_limit?: number;
  message?: string;
}

export function ImportDialog({ open, onOpenChange }: ImportDialogProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const previewMutation = usePreviewWatchlistImport();
  const commitMutation = useCommitWatchlistImport();
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [result, setResult] = useState<CommitResult | null>(null);
  const [error, setError] = useState("");

  function handleClose(o: boolean) {
    if (!o) {
      setPreview(null);
      setResult(null);
      setError("");
      previewMutation.reset();
      commitMutation.reset();
    }
    onOpenChange(o);
  }

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError("");
    try {
      const data = await previewMutation.mutateAsync(file);
      setPreview(data);
    } catch (err: unknown) {
      const e = err as {
        response?: {
          data?: { error?: string; detected_headers?: string[] };
        };
      };
      const detected = e.response?.data?.detected_headers;
      const msg = e.response?.data?.error || "Could not read that file.";
      setError(
        detected
          ? `${msg} Detected columns: ${detected.join(", ") || "(none)"}`
          : msg,
      );
    } finally {
      // Reset so the same file can be re-selected after an error
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleCommit() {
    if (!preview) return;
    try {
      const res = await commitMutation.mutateAsync(preview.rows);
      setResult(res);
    } catch {
      setError("Failed to save companies. Please try again.");
    }
  }

  // ── Success state ──
  if (result) {
    return (
      <Dialog open={open} onOpenChange={handleClose}>
        <DialogContent className="sm:max-w-md">
          <div className="py-8 text-center">
            <CheckCircle className="mx-auto mb-3 h-10 w-10 text-green-500" />
            <h3 className="font-semibold">Import complete</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Added {result.created}{" "}
              {result.created === 1 ? "company" : "companies"} to your
              watchlist.
            </p>
            {result.skipped_duplicates > 0 && (
              <p className="mt-1 text-xs text-muted-foreground">
                Skipped {result.skipped_duplicates} duplicate
                {result.skipped_duplicates === 1 ? "" : "s"}.
              </p>
            )}
            {result.message && (
              <p className="mt-3 rounded-md bg-amber-500/10 p-3 text-xs text-amber-700 dark:text-amber-400">
                {result.message}
              </p>
            )}
            <Button className="mt-4" onClick={() => handleClose(false)}>
              Done
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  // ── Preview / upload state ──
  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-h-[80vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Import companies</DialogTitle>
          <DialogDescription>
            Upload a CSV or Excel file with one company per row. Required
            column: <code>name</code> (or <code>company</code>). Optional
            column: <code>careers_url</code> (or <code>website</code>).
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!preview ? (
          <div className="space-y-4">
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              className="hidden"
              onChange={handleFileChange}
            />
            <div
              className="cursor-pointer rounded-lg border-2 border-dashed p-12 text-center transition-colors hover:border-primary/50"
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="mx-auto mb-3 h-10 w-10 text-muted-foreground" />
              <p className="text-sm font-medium">Click to upload</p>
              <p className="text-xs text-muted-foreground">
                CSV or XLSX, up to 2 MB
              </p>
            </div>
            {previewMutation.isPending && (
              <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Parsing file…
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Detected <strong>{preview.row_count}</strong> companies. Preview:
            </p>
            <div className="max-h-64 overflow-auto rounded-lg border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50 text-left">
                    <th className="px-3 py-2 font-medium">Name</th>
                    <th className="px-3 py-2 font-medium">Careers URL</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.rows.slice(0, 10).map((row, i) => (
                    <tr key={i} className="border-b">
                      <td className="px-3 py-2 font-medium">{row.name}</td>
                      <td className="px-3 py-2 truncate text-muted-foreground">
                        {row.careers_url || (
                          <span className="italic">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {preview.rows.length > 10 && (
                <p className="border-t bg-muted/30 px-3 py-2 text-center text-xs text-muted-foreground">
                  … and {preview.rows.length - 10} more
                </p>
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              Duplicate names (matching companies already on your watchlist)
              will be skipped. ATS platform will be auto-detected from the
              careers URL where possible.
            </p>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => handleClose(false)}>
            Cancel
          </Button>
          {preview && (
            <Button
              onClick={handleCommit}
              disabled={commitMutation.isPending}
            >
              {commitMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Import {preview.row_count} companies
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
