import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCVVersions } from "@/features/cv/hooks";
import { AlertCircle, Loader2, MessageSquare } from "lucide-react";
import { useState } from "react";

import { useAnswerQuestion, useTaskResult } from "../hooks";

export function QAForm() {
  const { data: cvData } = useCVVersions();
  const answerMutation = useAnswerQuestion();

  const [question, setQuestion] = useState("");
  const [cvVersionId, setCvVersionId] = useState<number | "">("");
  const [jobContext, setJobContext] = useState("");
  const [charLimit, setCharLimit] = useState("");
  const [taskId, setTaskId] = useState<string | null>(null);

  const cvVersions = cvData?.results || [];

  const taskQuery = useTaskResult(taskId);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!cvVersionId || !question) return;

    const response = await answerMutation.mutateAsync({
      question,
      cv_version_id: Number(cvVersionId),
      job_context: jobContext || undefined,
      character_limit: charLimit ? Number(charLimit) : undefined,
    });
    setTaskId(response.data.task_id);
  }

  function reset() {
    setTaskId(null);
    answerMutation.reset();
  }

  // Result / pending / error views
  if (taskId) {
    const status = taskQuery.data?.status;
    const answer = (taskQuery.data?.result as { answer?: string } | undefined)
      ?.answer;

    if (status === "success" && answer) {
      return (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <MessageSquare className="h-4 w-4 text-primary" />
              Answer
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="whitespace-pre-wrap rounded-md border bg-muted/30 p-4 text-sm">
              {answer}
            </div>
            <Button variant="outline" onClick={reset}>
              Ask Another Question
            </Button>
          </CardContent>
        </Card>
      );
    }
    if (status === "failure") {
      return (
        <Card>
          <CardContent className="py-8 text-center">
            <AlertCircle className="mx-auto mb-3 h-10 w-10 text-destructive" />
            <h3 className="font-semibold">Generation failed</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {taskQuery.data?.error ?? "The AI provider returned an error."}
            </p>
            <Button variant="outline" className="mt-3" onClick={reset}>
              Try Again
            </Button>
          </CardContent>
        </Card>
      );
    }
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <Loader2 className="mx-auto mb-3 h-8 w-8 animate-spin text-primary" />
          <h3 className="font-semibold">Generating your answer…</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            This usually takes a few seconds.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <MessageSquare className="h-4 w-4 text-primary" />
          Question Answerer
        </CardTitle>
        <CardDescription>
          Get AI-generated answers for application questions.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Question *</Label>
            <textarea
              rows={3}
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. Why do you want to work at our company?"
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
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
            <div className="space-y-2">
              <Label>Character Limit</Label>
              <Input
                type="number"
                value={charLimit}
                onChange={(e) => setCharLimit(e.target.value)}
                placeholder="Optional"
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label>Job Context</Label>
            <Input
              value={jobContext}
              onChange={(e) => setJobContext(e.target.value)}
              placeholder="Optional: job URL or company info"
            />
          </div>
          <Button
            type="submit"
            disabled={answerMutation.isPending || !question || !cvVersionId}
          >
            {answerMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            Generate Answers
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
