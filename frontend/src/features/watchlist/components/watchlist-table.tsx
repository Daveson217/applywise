import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { WatchlistCompany } from "@/types/watchlist";
import { formatDistanceToNow } from "date-fns";
import {
  AlertCircle,
  CheckCircle,
  Clock,
  ExternalLink,
  MoreHorizontal,
  Plus,
  Trash2,
  Upload,
} from "lucide-react";
import { useState } from "react";

import { useDeleteWatchlistCompany, useWatchlist } from "../hooks";
import { AddCompanyForm } from "./add-company-form";
import { ImportDialog } from "./import-dialog";

const atsLabels: Record<string, string> = {
  greenhouse: "Greenhouse",
  lever: "Lever",
  ashby: "Ashby",
  workable: "Workable",
  smartrecruiters: "SmartRecruiters",
};

function StatusIcon({ status }: { status: string }) {
  if (status === "active")
    return <CheckCircle className="h-4 w-4 text-green-500" />;
  if (status === "error")
    return <AlertCircle className="h-4 w-4 text-red-500" />;
  return <Clock className="h-4 w-4 text-yellow-500" />;
}

export function WatchlistTable() {
  const { data, isLoading } = useWatchlist();
  const deleteMutation = useDeleteWatchlistCompany();
  const [addOpen, setAddOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);

  const companies = data?.results || [];

  return (
    <div className="space-y-4">
      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={() => setImportOpen(true)}>
          <Upload className="mr-2 h-4 w-4" />
          Import
        </Button>
        <Button onClick={() => setAddOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Company
        </Button>
      </div>

      <div className="rounded-lg border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-4 py-3 text-left font-medium">Company</th>
              <th className="hidden px-4 py-3 text-left font-medium md:table-cell">
                ATS
              </th>
              <th className="px-4 py-3 text-left font-medium">Status</th>
              <th className="hidden px-4 py-3 text-left font-medium lg:table-cell">
                Active Jobs
              </th>
              <th className="hidden px-4 py-3 text-left font-medium lg:table-cell">
                Last Checked
              </th>
              <th className="px-4 py-3 text-right font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <tr key={i} className="border-b">
                  {Array.from({ length: 6 }).map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <Skeleton className="h-5 w-full" />
                    </td>
                  ))}
                </tr>
              ))
            ) : companies.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center">
                  <p className="text-lg font-medium text-muted-foreground">
                    No companies on your watchlist
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Add companies to monitor for new job postings.
                  </p>
                  <Button onClick={() => setAddOpen(true)} className="mt-4">
                    <Plus className="mr-2 h-4 w-4" />
                    Add Company
                  </Button>
                </td>
              </tr>
            ) : (
              companies.map((company) => (
                <tr
                  key={company.id}
                  className="border-b transition-colors hover:bg-muted/30"
                >
                  <td className="px-4 py-3">
                    <div>
                      <span className="font-medium">{company.name}</span>
                      {company.careers_url && (
                        <a
                          href={company.careers_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="ml-2 inline-flex text-muted-foreground hover:text-foreground"
                        >
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                  </td>
                  <td className="hidden px-4 py-3 md:table-cell">
                    {company.ats_provider ? (
                      <Badge variant="secondary">
                        {atsLabels[company.ats_provider] ||
                          company.ats_provider}
                      </Badge>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1.5">
                      <StatusIcon status={company.scrape_status} />
                      <span className="capitalize">
                        {company.scrape_status}
                      </span>
                    </div>
                  </td>
                  <td className="hidden px-4 py-3 lg:table-cell">
                    {company.active_postings_count}
                  </td>
                  <td className="hidden px-4 py-3 lg:table-cell">
                    {company.last_checked_at
                      ? formatDistanceToNow(
                          new Date(company.last_checked_at),
                          { addSuffix: true }
                        )
                      : "Never"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <button className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground">
                          <MoreHorizontal className="h-4 w-4" />
                        </button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() =>
                            deleteMutation.mutate(company.id)
                          }
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Remove
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

      <AddCompanyForm open={addOpen} onOpenChange={setAddOpen} />
      <ImportDialog open={importOpen} onOpenChange={setImportOpen} />
    </div>
  );
}
