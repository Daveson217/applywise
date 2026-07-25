import { Badge } from "@/components/ui/badge";
import { STATUS_LABELS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { Application } from "@/types/application";
import {
  DndContext,
  type DragEndEvent,
  DragOverlay,
  type DragStartEvent,
  PointerSensor,
  closestCorners,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical } from "lucide-react";
import { useState } from "react";

import { useApplications, useUpdateApplication } from "../hooks";
import { PriorityBadge } from "./priority-badge";

const KANBAN_COLUMNS = [
  { status: "saved", label: "Saved", color: "#6B7280" },
  { status: "applied", label: "Applied", color: "#3B82F6" },
  { status: "oa_assessment", label: "OA/Assessment", color: "#8B5CF6" },
  { status: "phone_screen", label: "Phone Screen", color: "#06B6D4" },
  { status: "interview", label: "Interview", color: "#F59E0B" },
  { status: "final_round", label: "Final Round", color: "#F97316" },
  { status: "offer_received", label: "Offer", color: "#10B981" },
  { status: "accepted", label: "Accepted", color: "#059669" },
  { status: "rejected", label: "Rejected", color: "#EF4444" },
];

interface KanbanCardProps {
  application: Application;
}

function KanbanCard({ application }: KanbanCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: application.id, data: { application } });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        "rounded-lg border bg-card p-3 shadow-sm transition-shadow hover:shadow-md",
        isDragging && "opacity-50 shadow-lg"
      )}
    >
      <div className="flex items-start gap-2">
        <button
          {...attributes}
          {...listeners}
          className="mt-0.5 cursor-grab text-muted-foreground hover:text-foreground active:cursor-grabbing"
        >
          <GripVertical className="h-4 w-4" />
        </button>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{application.company}</p>
          <p className="truncate text-xs text-muted-foreground">
            {application.role}
          </p>
          <div className="mt-2 flex items-center gap-1.5">
            <PriorityBadge priority={application.priority} />
            {application.location && (
              <span className="truncate text-xs text-muted-foreground">
                {application.location}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function DragOverlayCard({ application }: { application: Application }) {
  return (
    <div className="rounded-lg border bg-card p-3 shadow-xl">
      <div className="flex items-start gap-2">
        <GripVertical className="mt-0.5 h-4 w-4 text-muted-foreground" />
        <div>
          <p className="text-sm font-medium">{application.company}</p>
          <p className="text-xs text-muted-foreground">{application.role}</p>
        </div>
      </div>
    </div>
  );
}

interface KanbanColumnProps {
  status: string;
  label: string;
  color: string;
  applications: Application[];
}

function KanbanColumn({
  status,
  label,
  color,
  applications,
}: KanbanColumnProps) {
  return (
    <div className="flex w-64 shrink-0 flex-col rounded-lg bg-muted/30">
      <div className="flex items-center gap-2 border-b px-3 py-2.5">
        <div
          className="h-2.5 w-2.5 rounded-full"
          style={{ backgroundColor: color }}
        />
        <span className="text-sm font-medium">{label}</span>
        <Badge variant="secondary" className="ml-auto text-xs">
          {applications.length}
        </Badge>
      </div>
      <SortableContext
        items={applications.map((a) => a.id)}
        strategy={verticalListSortingStrategy}
      >
        <div className="flex flex-1 flex-col gap-2 overflow-y-auto p-2">
          {applications.map((app) => (
            <KanbanCard key={app.id} application={app} />
          ))}
          {applications.length === 0 && (
            <div className="flex h-20 items-center justify-center rounded-lg border-2 border-dashed border-muted text-xs text-muted-foreground">
              Drop here
            </div>
          )}
        </div>
      </SortableContext>
    </div>
  );
}

export function KanbanBoard() {
  const { data, isLoading } = useApplications();
  const updateMutation = useUpdateApplication();
  const [activeApp, setActiveApp] = useState<Application | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } })
  );

  const applications = data?.results || [];

  function getColumnApps(status: string) {
    return applications.filter((a) => a.status === status);
  }

  function handleDragStart(event: DragStartEvent) {
    const app = applications.find((a) => a.id === event.active.id);
    setActiveApp(app || null);
  }

  function handleDragEnd(event: DragEndEvent) {
    setActiveApp(null);
    const { active, over } = event;
    if (!over) return;

    const draggedApp = applications.find((a) => a.id === active.id);
    if (!draggedApp) return;

    let targetStatus: string | null = null;

    const overApp = applications.find((a) => a.id === over.id);
    if (overApp) {
      targetStatus = overApp.status;
    } else {
      const col = KANBAN_COLUMNS.find((c) => c.status === String(over.id));
      if (col) targetStatus = col.status;
    }

    if (targetStatus && targetStatus !== draggedApp.status) {
      updateMutation.mutate({
        id: draggedApp.id,
        data: { status: targetStatus },
      });
    }
  }

  if (isLoading) {
    return (
      <div className="flex gap-4 overflow-x-auto pb-4">
        {KANBAN_COLUMNS.slice(0, 5).map((col) => (
          <div
            key={col.status}
            className="h-64 w-64 shrink-0 animate-pulse rounded-lg bg-muted/30"
          />
        ))}
      </div>
    );
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="flex gap-4 overflow-x-auto pb-4">
        {KANBAN_COLUMNS.map((col) => (
          <KanbanColumn
            key={col.status}
            status={col.status}
            label={col.label}
            color={col.color}
            applications={getColumnApps(col.status)}
          />
        ))}
      </div>
      <DragOverlay>
        {activeApp && <DragOverlayCard application={activeApp} />}
      </DragOverlay>
    </DndContext>
  );
}
