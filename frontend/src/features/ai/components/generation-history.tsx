import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { formatDistanceToNow } from "date-fns";
import { ChevronDown, ChevronRight, History, Trash2 } from "lucide-react";
import { useState } from "react";

import { useDeleteGeneration, useGenerations } from "../hooks";
import type { AIGeneration } from "../api";

interface Props {
  feature: "qa" | "fit_score" | "ats_score";
}

function summaryLine(g: AIGeneration): string {
  if (g.feature === "qa") {
    const answer = (g.result as { answer?: string }).answer;
    return answer ? answer.slice(0, 120) + (answer.length > 120 ? "…" : "") : "(no answer)";
  }
  const score = (g.result as { score?: number }).score;
  return typeof score === "number" ? `Score: ${Math.round(score)} / 100` : "(no score)";
}

function ResultBody({ g }: { g: AIGeneration }) {
  if (g.feature === "qa") {
    const answer = (g.result as { answer?: string }).answer;
    return (
      <div className="whitespace-pre-wrap rounded-md border bg-muted/30 p-3 text-sm">
        {answer ?? "(no answer)"}
      </div>
    );
  }
  // Both scoring features: dump the JSON prettily. The main form renders it
  // fully; here we just give a peek so users don't need round trips.
  return (
    <pre className="overflow-x-auto rounded-md border bg-muted/30 p-3 text-xs">
      {JSON.stringify(g.result, null, 2)}
    </pre>
  );
}

export function GenerationHistory({ feature }: Props) {
  const { data, isLoading, refetch } = useGenerations(feature);
  const deleteMutation = useDeleteGeneration();
  const [expanded, setExpanded] = useState<number | null>(null);

  const items = data?.results ?? [];

  async function handleDelete(id: number) {
    await deleteMutation.mutateAsync(id);
    refetch();
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <History className="h-4 w-4 text-muted-foreground" />
          History
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No previous runs yet. Results you generate here will appear in this
            list.
          </p>
        ) : (
          <ul className="divide-y">
            {items.map((g) => {
              const open = expanded === g.id;
              return (
                <li key={g.id} className="py-2">
                  <div className="flex items-start gap-2">
                    <button
                      type="button"
                      onClick={() => setExpanded(open ? null : g.id)}
                      className="mt-0.5 text-muted-foreground hover:text-foreground"
                    >
                      {open ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </button>
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium">
                        {g.title || "(untitled)"}
                      </div>
                      <div className="truncate text-xs text-muted-foreground">
                        {summaryLine(g)}
                      </div>
                      <div className="mt-0.5 text-xs text-muted-foreground">
                        {formatDistanceToNow(new Date(g.created_at), {
                          addSuffix: true,
                        })}{" "}
                        · {g.provider} / {g.model}
                      </div>
                    </div>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      className="text-destructive hover:text-destructive"
                      onClick={() => handleDelete(g.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                  {open && (
                    <div className="ml-6 mt-2">
                      <ResultBody g={g} />
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
