import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { formatDistanceToNow } from "date-fns";
import { ChevronDown, ChevronRight, Copy, History, Trash2 } from "lucide-react";
import { useState } from "react";

import { useCoverLetters, useDeleteCoverLetter } from "../hooks";

export function CoverLetterHistory() {
  const { data, isLoading } = useCoverLetters();
  const deleteMutation = useDeleteCoverLetter();
  const [expanded, setExpanded] = useState<number | null>(null);
  const [copiedId, setCopiedId] = useState<number | null>(null);

  const items = data?.results ?? [];

  async function copy(id: number, text: string) {
    await navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1500);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <History className="h-4 w-4 text-muted-foreground" />
          Cover Letter History
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No cover letters yet. Ones you generate will appear here.
          </p>
        ) : (
          <ul className="divide-y">
            {items.map((cl) => {
              const open = expanded === cl.id;
              const preview =
                cl.content.slice(0, 140).replace(/\s+/g, " ") +
                (cl.content.length > 140 ? "…" : "");
              return (
                <li key={cl.id} className="py-2">
                  <div className="flex items-start gap-2">
                    <button
                      type="button"
                      onClick={() => setExpanded(open ? null : cl.id)}
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
                        {`v${cl.version_number}`}
                        {cl.application ? ` · Application #${cl.application}` : ""}
                      </div>
                      <div className="truncate text-xs text-muted-foreground">
                        {preview}
                      </div>
                      <div className="mt-0.5 text-xs text-muted-foreground">
                        {formatDistanceToNow(new Date(cl.created_at), {
                          addSuffix: true,
                        })}{" "}
                        · {cl.provider} / {cl.model}
                      </div>
                    </div>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => copy(cl.id, cl.content)}
                      title="Copy to clipboard"
                    >
                      <Copy className="h-4 w-4" />
                      {copiedId === cl.id && (
                        <span className="ml-1 text-xs">Copied</span>
                      )}
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      className="text-destructive hover:text-destructive"
                      onClick={() => deleteMutation.mutate(cl.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                  {open && (
                    <div className="ml-6 mt-2 whitespace-pre-wrap rounded-md border bg-muted/30 p-3 text-sm">
                      {cl.content}
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
