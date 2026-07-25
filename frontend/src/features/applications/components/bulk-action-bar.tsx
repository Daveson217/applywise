import { Button } from "@/components/ui/button";
import { STATUS_OPTIONS } from "@/lib/constants";
import { Loader2, Trash2, X } from "lucide-react";
import { useState } from "react";

import { useBulkAction } from "../hooks";

interface BulkActionBarProps {
  selectedIds: number[];
  onClear: () => void;
}

export function BulkActionBar({ selectedIds, onClear }: BulkActionBarProps) {
  const bulkMutation = useBulkAction();
  const [newStatus, setNewStatus] = useState("");

  if (selectedIds.length === 0) return null;

  async function handleStatusChange() {
    if (!newStatus) return;
    await bulkMutation.mutateAsync({
      action: "status_change",
      ids: selectedIds,
      status: newStatus,
    });
    setNewStatus("");
    onClear();
  }

  async function handleDelete() {
    if (!confirm(`Delete ${selectedIds.length} applications?`)) return;
    await bulkMutation.mutateAsync({
      action: "delete",
      ids: selectedIds,
    });
    onClear();
  }

  return (
    <div className="fixed bottom-20 left-1/2 z-40 flex -translate-x-1/2 items-center gap-3 rounded-full border bg-card px-4 py-2 shadow-lg md:bottom-6">
      <span className="text-sm font-medium">
        {selectedIds.length} selected
      </span>
      <select
        className="h-9 rounded-md border border-input bg-background px-2 text-sm"
        value={newStatus}
        onChange={(e) => setNewStatus(e.target.value)}
      >
        <option value="">Change status to...</option>
        {STATUS_OPTIONS.map((s) => (
          <option key={s.value} value={s.value}>
            {s.label}
          </option>
        ))}
      </select>
      <Button
        size="sm"
        onClick={handleStatusChange}
        disabled={!newStatus || bulkMutation.isPending}
      >
        {bulkMutation.isPending && (
          <Loader2 className="mr-1 h-3 w-3 animate-spin" />
        )}
        Apply
      </Button>
      <Button
        size="sm"
        variant="destructive"
        onClick={handleDelete}
        disabled={bulkMutation.isPending}
      >
        <Trash2 className="mr-1 h-3 w-3" />
        Delete
      </Button>
      <button
        onClick={onClear}
        className="rounded p-1 text-muted-foreground hover:text-foreground"
        aria-label="Clear selection"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
