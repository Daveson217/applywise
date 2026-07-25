import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { CheckCircle, Loader2, Upload } from "lucide-react";
import { useRef, useState } from "react";

import { useCommitImport, usePreviewImport } from "../hooks";

interface ImportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface PreviewData {
  headers: string[];
  rows: Record<string, string>[];
  row_count: number;
}

export function ImportDialog({ open, onOpenChange }: ImportDialogProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const previewMutation = usePreviewImport();
  const commitMutation = useCommitImport();
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [result, setResult] = useState<number | null>(null);

  function handleClose(o: boolean) {
    if (!o) {
      setPreview(null);
      setResult(null);
      previewMutation.reset();
      commitMutation.reset();
    }
    onOpenChange(o);
  }

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const data = await previewMutation.mutateAsync(file);
    setPreview(data);
  }

  async function handleCommit() {
    if (!preview) return;
    const res = await commitMutation.mutateAsync(preview.rows);
    setResult(res.created);
  }

  if (result !== null) {
    return (
      <Dialog open={open} onOpenChange={handleClose}>
        <DialogContent className="sm:max-w-md">
          <div className="py-8 text-center">
            <CheckCircle className="mx-auto mb-3 h-10 w-10 text-green-500" />
            <h3 className="font-semibold">Import Complete</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {result} applications created.
            </p>
            <Button className="mt-4" onClick={() => handleClose(false)}>
              Done
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-h-[80vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Import Applications from CSV</DialogTitle>
          <DialogDescription>
            Upload a CSV with columns like company, role, status, applied_date.
            Compatible with LinkedIn and Handshake exports.
          </DialogDescription>
        </DialogHeader>

        {!preview ? (
          <div className="space-y-4">
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={handleFileChange}
            />
            <div
              className="cursor-pointer rounded-lg border-2 border-dashed p-12 text-center hover:border-primary/50"
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="mx-auto mb-3 h-10 w-10 text-muted-foreground" />
              <p className="text-sm font-medium">Click to upload CSV</p>
              <p className="text-xs text-muted-foreground">
                Maximum 100 rows per preview
              </p>
            </div>
            {previewMutation.isPending && (
              <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Parsing CSV...
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Detected {preview.row_count} rows. Preview:
            </p>
            <div className="max-h-64 overflow-auto rounded-lg border">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b bg-muted/50">
                    {preview.headers.slice(0, 6).map((h) => (
                      <th key={h} className="px-2 py-2 text-left font-medium">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.rows.slice(0, 5).map((row, i) => (
                    <tr key={i} className="border-b">
                      {preview.headers.slice(0, 6).map((h) => (
                        <td key={h} className="truncate px-2 py-2">
                          {row[h] || "—"}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
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
              Import {preview.row_count} Applications
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
