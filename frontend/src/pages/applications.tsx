import { Button } from "@/components/ui/button";
import { ApplicationsTable } from "@/features/applications/components/applications-table";
import { KanbanBoard } from "@/features/applications/components/kanban-board";
import { useUIStore } from "@/store/ui-store";
import { Kanban, List } from "lucide-react";

export function ApplicationsPage() {
  const view = useUIStore((s) => s.applicationsView);
  const setView = useUIStore((s) => s.setApplicationsView);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-[family-name:var(--font-display)] text-2xl font-bold">
            Applications
          </h1>
          <p className="text-muted-foreground">
            Track and manage your job applications.
          </p>
        </div>
        <div className="flex rounded-lg border p-1">
          <Button
            variant={view === "list" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => setView("list")}
            aria-label="List view"
          >
            <List className="h-4 w-4" />
          </Button>
          <Button
            variant={view === "kanban" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => setView("kanban")}
            aria-label="Kanban view"
          >
            <Kanban className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {view === "list" ? <ApplicationsTable /> : <KanbanBoard />}
    </div>
  );
}
