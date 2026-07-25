import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { Interaction } from "@/types/networking";
import { format } from "date-fns";
import {
  Coffee,
  ExternalLink,
  Mail,
  MessageCircle,
  MessageSquare,
  Phone,
  Plus,
  RefreshCw,
} from "lucide-react";
import { useState } from "react";

import { useCreateInteraction, useInteractions } from "../hooks";

const TYPE_ICONS: Record<string, typeof Coffee> = {
  coffee_chat: Coffee,
  email: Mail,
  call: Phone,
  referral: ExternalLink,
  interview_prep: MessageSquare,
  follow_up: RefreshCw,
  linkedin: MessageCircle,
  other: MessageSquare,
};

const TYPE_LABELS: Record<string, string> = {
  coffee_chat: "Coffee Chat",
  email: "Email",
  call: "Phone Call",
  referral: "Referral",
  interview_prep: "Interview Prep",
  follow_up: "Follow Up",
  linkedin: "LinkedIn",
  other: "Other",
};

interface InteractionTimelineProps {
  contactId: number;
}

export function InteractionTimeline({ contactId }: InteractionTimelineProps) {
  const { data, isLoading } = useInteractions(contactId);
  const createMutation = useCreateInteraction(contactId);
  const [adding, setAdding] = useState(false);
  const [newInteraction, setNewInteraction] = useState({
    type: "coffee_chat",
    date: new Date().toISOString().split("T")[0],
    notes: "",
  });

  async function handleAdd() {
    if (!newInteraction.date) return;
    await createMutation.mutateAsync(newInteraction);
    setAdding(false);
    setNewInteraction({
      type: "coffee_chat",
      date: new Date().toISOString().split("T")[0],
      notes: "",
    });
  }

  if (isLoading) {
    return <Skeleton className="h-32 w-full" />;
  }

  const interactions = (data || []) as Interaction[];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Interactions</h3>
        {!adding && (
          <Button size="sm" variant="outline" onClick={() => setAdding(true)}>
            <Plus className="mr-1 h-3 w-3" />
            Log Interaction
          </Button>
        )}
      </div>

      {adding && (
        <div className="space-y-3 rounded-lg border bg-muted/30 p-3">
          <div className="grid grid-cols-2 gap-2">
            <select
              className="h-9 rounded-md border border-input bg-background px-2 text-sm"
              value={newInteraction.type}
              onChange={(e) =>
                setNewInteraction({ ...newInteraction, type: e.target.value })
              }
            >
              {Object.entries(TYPE_LABELS).map(([v, l]) => (
                <option key={v} value={v}>
                  {l}
                </option>
              ))}
            </select>
            <input
              type="date"
              className="h-9 rounded-md border border-input bg-background px-2 text-sm"
              value={newInteraction.date}
              onChange={(e) =>
                setNewInteraction({ ...newInteraction, date: e.target.value })
              }
            />
          </div>
          <textarea
            rows={2}
            placeholder="Notes (optional)"
            className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
            value={newInteraction.notes}
            onChange={(e) =>
              setNewInteraction({ ...newInteraction, notes: e.target.value })
            }
          />
          <div className="flex gap-2">
            <Button size="sm" onClick={handleAdd} disabled={createMutation.isPending}>
              Save
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setAdding(false)}>
              Cancel
            </Button>
          </div>
        </div>
      )}

      {interactions.length === 0 && !adding ? (
        <p className="text-sm text-muted-foreground">
          No interactions logged yet.
        </p>
      ) : (
        <div className="space-y-3">
          {interactions.map((interaction) => {
            const Icon = TYPE_ICONS[interaction.type] || MessageSquare;
            return (
              <div
                key={interaction.id}
                className="flex gap-3 rounded-lg border p-3"
              >
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
                  <Icon className="h-4 w-4 text-primary" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">
                      {TYPE_LABELS[interaction.type] || interaction.type}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {format(new Date(interaction.date), "MMM d, yyyy")}
                    </span>
                  </div>
                  {interaction.notes && (
                    <p className="mt-1 text-sm text-muted-foreground">
                      {interaction.notes}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
