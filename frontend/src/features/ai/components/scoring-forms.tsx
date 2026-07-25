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
import { CheckCircle, Loader2, Target, FileSearch } from "lucide-react";
import { useState } from "react";

import { useComputeATSScore, useComputeFitScore } from "../hooks";

export function FitScoreForm() {
  const { data: cvData } = useCVVersions();
  const fitMutation = useComputeFitScore();

  const [jobDescription, setJobDescription] = useState("");
  const [cvVersionId, setCvVersionId] = useState<number | "">("");
  const [submitted, setSubmitted] = useState(false);

  const cvVersions = cvData?.results || [];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!cvVersionId || !jobDescription) return;

    await fitMutation.mutateAsync({
      job_description: jobDescription,
      cv_version_id: Number(cvVersionId),
    });
    setSubmitted(true);
  }

  if (submitted && fitMutation.isSuccess) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <CheckCircle className="mx-auto mb-3 h-10 w-10 text-green-500" />
          <h3 className="font-semibold">Fit Score Queued</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Results will be available shortly.
          </p>
          <Button
            variant="outline"
            className="mt-3"
            onClick={() => {
              setSubmitted(false);
              fitMutation.reset();
            }}
          >
            Score Another
          </Button>
        </CardContent>
      </Card>
    );
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
  const [submitted, setSubmitted] = useState(false);

  const cvVersions = cvData?.results || [];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!cvVersionId || !jobDescription) return;

    await atsMutation.mutateAsync({
      job_description: jobDescription,
      cv_version_id: Number(cvVersionId),
    });
    setSubmitted(true);
  }

  if (submitted && atsMutation.isSuccess) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <CheckCircle className="mx-auto mb-3 h-10 w-10 text-green-500" />
          <h3 className="font-semibold">ATS Score Queued</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Results will be available shortly.
          </p>
          <Button
            variant="outline"
            className="mt-3"
            onClick={() => {
              setSubmitted(false);
              atsMutation.reset();
            }}
          >
            Score Another
          </Button>
        </CardContent>
      </Card>
    );
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
