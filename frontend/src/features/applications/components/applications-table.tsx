import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { STATUS_FILTER_GROUPS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { Application, ApplicationFilters } from "@/types/application";
import { format } from "date-fns";
import {
  ChevronLeft,
  ChevronRight,
  Edit,
  ExternalLink,
  MoreHorizontal,
  Plus,
  Search,
  Trash2,
} from "lucide-react";
import { useState } from "react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";

import { useApplications } from "../hooks";
import { ApplicationForm } from "./application-form";
import { ApplicationTimeline } from "./application-timeline";
import { BulkActionBar } from "./bulk-action-bar";
import { DeleteConfirmDialog } from "./delete-confirm-dialog";
import { ImportDialog } from "./import-dialog";
import { ExportButton } from "./export-button";
import { PriorityBadge } from "./priority-badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { StatusBadge } from "./status-badge";

export function ApplicationsTable() {
  const [filters, setFilters] = useState<ApplicationFilters>({});
  const [search, setSearch] = useState("");
  const [activeGroup, setActiveGroup] = useState(0);
  const [formOpen, setFormOpen] = useState(false);
  const [editingApp, setEditingApp] = useState<Application | null>(null);
  const [deleteApp, setDeleteApp] = useState<{
    id: number;
    name: string;
  } | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [importOpen, setImportOpen] = useState(false);
  const [timelineApp, setTimelineApp] = useState<Application | null>(null);

  const currentFilters: ApplicationFilters = {
    ...filters,
    search: search || undefined,
  };

  const { data, isLoading } = useApplications(currentFilters);

  function handleGroupChange(index: number) {
    setActiveGroup(index);
    const group = STATUS_FILTER_GROUPS[index];
    if (group.statuses.length === 0) {
      const { status: _, ...rest } = filters;
      setFilters(rest);
    } else if (group.statuses.length === 1) {
      setFilters({ ...filters, status: group.statuses[0] });
    } else {
      setFilters({ ...filters, status: group.statuses[0] });
    }
  }

  function handleEdit(app: Application) {
    setEditingApp(app);
    setFormOpen(true);
  }

  function handleAdd() {
    setEditingApp(null);
    setFormOpen(true);
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex gap-1 overflow-x-auto">
          {STATUS_FILTER_GROUPS.map((group, i) => (
            <button
              key={group.label}
              onClick={() => handleGroupChange(i)}
              className={cn(
                "whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                activeGroup === i
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted"
              )}
            >
              {group.label}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search company or role..."
              className="pl-9"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Button variant="outline" onClick={() => setImportOpen(true)}>
            Import
          </Button>
          <ExportButton />
          <Button onClick={handleAdd}>
            <Plus className="mr-2 h-4 w-4" />
            Add
          </Button>
        </div>
      </div>

      <div className="rounded-lg border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="w-10 px-3 py-3">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded"
                  checked={
                    (data?.results.length || 0) > 0 &&
                    data?.results.every((app) => selectedIds.has(app.id))
                  }
                  onChange={(e) => {
                    if (e.target.checked) {
                      const all = new Set(selectedIds);
                      data?.results.forEach((app) => all.add(app.id));
                      setSelectedIds(all);
                    } else {
                      setSelectedIds(new Set());
                    }
                  }}
                />
              </th>
              <th className="px-4 py-3 text-left font-medium">Company</th>
              <th className="px-4 py-3 text-left font-medium">Role</th>
              <th className="px-4 py-3 text-left font-medium">Status</th>
              <th className="hidden px-4 py-3 text-left font-medium md:table-cell">
                Type
              </th>
              <th className="hidden px-4 py-3 text-left font-medium lg:table-cell">
                Priority
              </th>
              <th className="hidden px-4 py-3 text-left font-medium lg:table-cell">
                Applied
              </th>
              <th className="px-4 py-3 text-right font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="border-b">
                  {Array.from({ length: 8 }).map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <Skeleton className="h-5 w-full" />
                    </td>
                  ))}
                </tr>
              ))
            ) : data?.results.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-12 text-center">
                  <p className="text-lg font-medium text-muted-foreground">
                    No applications yet
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Click &quot;Add&quot; to track your first application.
                  </p>
                  <Button onClick={handleAdd} className="mt-4">
                    <Plus className="mr-2 h-4 w-4" />
                    Add Application
                  </Button>
                </td>
              </tr>
            ) : (
              data?.results.map((app) => (
                <tr
                  key={app.id}
                  className="border-b transition-colors hover:bg-muted/30"
                >
                  <td className="w-10 px-3 py-3">
                    <input
                      type="checkbox"
                      className="h-4 w-4 rounded"
                      checked={selectedIds.has(app.id)}
                      onChange={(e) => {
                        const next = new Set(selectedIds);
                        if (e.target.checked) next.add(app.id);
                        else next.delete(app.id);
                        setSelectedIds(next);
                      }}
                    />
                  </td>
                  <td className="px-4 py-3 font-medium">{app.company}</td>
                  <td className="px-4 py-3">{app.role}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={app.status} />
                  </td>
                  <td className="hidden px-4 py-3 capitalize md:table-cell">
                    {app.job_type.replace("_", " ")}
                  </td>
                  <td className="hidden px-4 py-3 lg:table-cell">
                    <PriorityBadge priority={app.priority} />
                  </td>
                  <td className="hidden px-4 py-3 lg:table-cell">
                    {app.applied_date
                      ? format(new Date(app.applied_date), "MMM d, yyyy")
                      : "-"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <button className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground">
                          <MoreHorizontal className="h-4 w-4" />
                        </button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleEdit(app)}>
                          <Edit className="mr-2 h-4 w-4" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => setTimelineApp(app)}>
                          <MoreHorizontal className="mr-2 h-4 w-4" />
                          View Timeline
                        </DropdownMenuItem>
                        {app.url && (
                          <DropdownMenuItem
                            onClick={() => window.open(app.url, "_blank")}
                          >
                            <ExternalLink className="mr-2 h-4 w-4" />
                            Open URL
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() =>
                            setDeleteApp({
                              id: app.id,
                              name: `${app.company} - ${app.role}`,
                            })
                          }
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

      {data && data.count > 20 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {data.results.length} of {data.count} applications
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={!data.previous}
              onClick={() =>
                setFilters({ ...filters, page: (filters.page || 1) - 1 })
              }
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={!data.next}
              onClick={() =>
                setFilters({ ...filters, page: (filters.page || 1) + 1 })
              }
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      <ApplicationForm
        open={formOpen}
        onOpenChange={setFormOpen}
        application={editingApp}
      />

      <DeleteConfirmDialog
        open={!!deleteApp}
        onOpenChange={() => setDeleteApp(null)}
        applicationId={deleteApp?.id || null}
        applicationName={deleteApp?.name || ""}
      />

      <ImportDialog open={importOpen} onOpenChange={setImportOpen} />

      <Dialog
        open={!!timelineApp}
        onOpenChange={(o) => !o && setTimelineApp(null)}
      >
        <DialogContent className="max-h-[80vh] overflow-y-auto sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>
              Timeline — {timelineApp?.company} ({timelineApp?.role})
            </DialogTitle>
          </DialogHeader>
          {timelineApp && (
            <ApplicationTimeline applicationId={timelineApp.id} />
          )}
        </DialogContent>
      </Dialog>

      <BulkActionBar
        selectedIds={Array.from(selectedIds)}
        onClear={() => setSelectedIds(new Set())}
      />
    </div>
  );
}
