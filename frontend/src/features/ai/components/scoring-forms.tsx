import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { useCVVersions } from "@/features/cv/hooks";
import { AlertCircle, FileSearch, Loader2, Target } from "lucide-react";
import { useState } from "react";

import { useComputeATSScore, useComputeFitScore, useTaskResult } from "../hooks";

interface FitResult {
  score?: number;
  strengths?: string[];
  gaps?: string[];
  recommendation?: string;
}

interface ATSResult {
  score?: number;
  matched_keywords?: string[];
  missing_keywords?: string[];
  suggestions?: string[];
}

function ScoreBadge({ score }: { score: number | undefined }) {
  const value = typeof score === "number" ? Math.round(score) : "—";
  return (
    <div className="text-4xl font-bold tabular-nums text-primary">
      {value}
      <span className="ml-1 text-lg font-normal text-muted-foreground">
        / 100
      </span>
    </div>
  );
}

function PendingCard({ label }: { label: string }) {
  return (
    <Card>
      <CardContent className="py-8 text-center">
        <Loader2 className="mx-auto mb-3 h-8 w-8 animate-spin text-primary" />
        <h3 className="font-semibold">Computing {label}…</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          This usually takes a few seconds.
        </p>
      </CardContent>
    </Card>
  );
}

function FailureCard({ error, onRetry }: { error?: string; onRetry: () => void }) {
  return (
    <Card>
      <CardContent className="py-8 text-center">
        <AlertCircle className="mx-auto mb-3 h-10 w-10 text-destructive" />
        <h3 className="font-semibold">Computation failed</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          {error ?? "The AI provider returned an error."}
        </p>
        <Button variant="outline" className="mt-3" onClick={onRetry}>
          Try Again
        </Button>
      </CardContent>
    </Card>
  );
}

export function FitScoreForm() {
  const { data: cvData } = useCVVersions();
  const fitMutation = useComputeFitScore();

  const [jobDescription, setJobDescription] = useState("");
  const [cvVersionId, setCvVersionId] = useState<number | "">("");
  const [taskId, setTaskId] = useState<string | null>(null);

  const cvVersions = cvData?.results || [];
  const taskQuery = useTaskResult(taskId);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!cvVersionId || !jobDescription) return;
    const response = await fitMutation.mutateAsync({
      job_description: jobDescription,
      cv_version_id: Number(cvVersionId),
    });
    setTaskId(response.data.task_id);
  }

  function reset() {
    setTaskId(null);
    fitMutation.reset();
  }

  if (taskId) {
    const status = taskQuery.data?.status;
    const result = taskQuery.data?.result as FitResult | undefined;

    if (status === "success" && result) {
      return (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Target className="h-4 w-4 text-primary" />
              Fit Score
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <ScoreBadge score={result.score} />
            {result.strengths && result.strengths.length > 0 && (
              <div>
                <h4 className="mb-1 text-sm font-medium">Strengths</h4>
                <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                  {result.strengths.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
            )}
            {result.gaps && result.gaps.length > 0 && (
              <div>
                <h4 className="mb-1 text-sm font-medium">Gaps</h4>
                <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                  {result.gaps.map((g, i) => (
                    <li key={i}>{g}</li>
                  ))}
                </ul>
              </div>
            )}
            {result.recommendation && (
              <div>
                <h4 className="mb-1 text-sm font-medium">Recommendation</h4>
                <p className="whitespace-pre-wrap text-sm text-muted-foreground">
                  {result.recommendation}
                </p>
              </div>
            )}
            <Button variant="outline" onClick={reset}>
              Score Another
            </Button>
          </CardContent>
        </Card>
      );
    }
    if (status === "failure") {
      return <FailureCard error={taskQuery.data?.error} onRetry={reset} />;
    }
    return <PendingCard label="fit score" />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Target className="h-4 w-4 text-primary" />
          Job Fit Score
        </CardTitle>
        <CardDescription>
          Get an AI assessment of how well you match a job.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Job Description *</Label>
            <textarea
              rows={4}
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the job description..."
            />
          </div>
          <div className="space-y-2">
            <Label>Resume Version *</Label>
            <select
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={cvVersionId}
              onChange={(e) => setCvVersionId(Number(e.target.value) || "")}
            >
              <option value="">Select resume</option>
              {cvVersions.map((cv) => (
                <option key={cv.id} value={cv.id}>
                  {cv.name}
                </option>
              ))}
            </select>
          </div>
          <Button
            type="submit"
            disabled={fitMutation.isPending || !jobDescription || !cvVersionId}
          >
            {fitMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            Compute Fit Score
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

export function ATSScoreForm() {
  const { data: cvData } = useCVVersions();
  const atsMutation = useComputeATSScore();

  const [jobDescription, setJobDescription] = useState("");
  const [cvVersionId, setCvVersionId] = useState<number | "">("");
  const [taskId, setTaskId] = useState<string | null>(null);

  const cvVersions = cvData?.results || [];
  const taskQuery = useTaskResult(taskId);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!cvVersionId || !jobDescription) return;
    const response = await atsMutation.mutateAsync({
      job_description: jobDescription,
      cv_version_id: Number(cvVersionId),
    });
    setTaskId(response.data.task_id);
  }

  function reset() {
    setTaskId(null);
    atsMutation.reset();
  }

  if (taskId) {
    const status = taskQuery.data?.status;
    const result = taskQuery.data?.result as ATSResult | undefined;

    if (status === "success" && result) {
      return (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <FileSearch className="h-4 w-4 text-primary" />
              ATS Score
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <ScoreBadge score={result.score} />
            {result.matched_keywords && result.matched_keywords.length > 0 && (
              <div>
                <h4 className="mb-1 text-sm font-medium">Matched keywords</h4>
                <div className="flex flex-wrap gap-1">
                  {result.matched_keywords.map((k, i) => (
                    <span
                      key={i}
                      className="rounded bg-green-100 px-2 py-0.5 text-xs text-green-900 dark:bg-green-900/30 dark:text-green-200"
                    >
                      {k}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {result.missing_keywords && result.missing_keywords.length > 0 && (
              <div>
                <h4 className="mb-1 text-sm font-medium">Missing keywords</h4>
                <div className="flex flex-wrap gap-1">
                  {result.missing_keywords.map((k, i) => (
                    <span
                      key={i}
                      className="rounded bg-yellow-100 px-2 py-0.5 text-xs text-yellow-900 dark:bg-yellow-900/30 dark:text-yellow-200"
                    >
                      {k}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {result.suggestions && result.suggestions.length > 0 && (
              <div>
                <h4 className="mb-1 text-sm font-medium">Suggestions</h4>
                <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                  {result.suggestions.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
            )}
            <Button variant="outline" onClick={reset}>
              Score Another
            </Button>
          </CardContent>
        </Card>
      );
    }
    if (status === "failure") {
      return <FailureCard error={taskQuery.data?.error} onRetry={reset} />;
    }
    return <PendingCard label="ATS score" />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <FileSearch className="h-4 w-4 text-primary" />
          ATS Resume Score
        </CardTitle>
        <CardDescription>
          Check how your resume scores against ATS keyword filters.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Job Description *</Label>
            <textarea
              rows={4}
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the job description..."
            />
          </div>
          <div className="space-y-2">
            <Label>Resume Version *</Label>
            <select
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={cvVersionId}
              onChange={(e) => setCvVersionId(Number(e.target.value) || "")}
            >
              <option value="">Select resume</option>
              {cvVersions.map((cv) => (
                <option key={cv.id} value={cv.id}>
                  {cv.name}
                </option>
              ))}
            </select>
          </div>
          <Button
            type="submit"
            disabled={atsMutation.isPending || !jobDescription || !cvVersionId}
          >
            {atsMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            Compute ATS Score
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
