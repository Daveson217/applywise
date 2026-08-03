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
import { CheckCircle, Loader2, Sparkles } from "lucide-react";
import { useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useUsage } from "@/features/billing/usage-api";

import { useGenerateCoverLetter, useProviders } from "../hooks";

const API_BASE = import.meta.env.VITE_API_URL || "/api";

export function CoverLetterForm() {
  const { data: providers } = useProviders();
  const { data: cvData } = useCVVersions();
  const { data: usage } = useUsage();
  const generateMutation = useGenerateCoverLetter();
  const queryClient = useQueryClient();

  const [company, setCompany] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [cvVersionId, setCvVersionId] = useState<number | "">("");
  const [tone, setTone] = useState("formal");
  const [length, setLength] = useState("standard");
  const [emphasis, setEmphasis] = useState("skills");
  const [provider, setProvider] = useState("");
  const [model, setModel] = useState("");
  const [streamedText, setStreamedText] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [done, setDone] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  const cvVersions = cvData?.results || [];
  const selectedProvider = providers?.find((p) => p.name === provider);

  function connectStream(taskId: string, streamToken: string) {
    // Stream token authenticates the SSE connection — required by backend.
    // Carried in query string because EventSource can't send headers.
    const url = `${API_BASE}/ai/cover-letter/stream/${taskId}/?token=${encodeURIComponent(streamToken)}`;
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.chunk) {
          setStreamedText((prev) => prev + payload.chunk);
        }
        if (payload.done) {
          setStreaming(false);
          setDone(true);
          es.close();
          // A new CoverLetter row was created server-side; refresh history.
          queryClient.invalidateQueries({ queryKey: ["ai", "cover-letters"] });
        }
      } catch {
        // ignore parse errors
      }
    };

    es.onerror = () => {
      setStreaming(false);
      es.close();
    };
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!cvVersionId || !company || !jobTitle || !jobDescription) return;

    setStreamedText("");
    setStreaming(true);
    setDone(false);

    try {
      const res = await generateMutation.mutateAsync({
        job_description: jobDescription,
        cv_version_id: Number(cvVersionId),
        company,
        job_title: jobTitle,
        tone,
        length,
        emphasis,
        provider: provider || undefined,
        model: model || undefined,
      });

      if (res?.task_id && res?.stream_token) {
        connectStream(res.task_id, res.stream_token);
      }
    } catch (err: unknown) {
      // 403 from quota / provider gating — surfaced to user
      setStreaming(false);
    }
  }

  function handleReset() {
    eventSourceRef.current?.close();
    setStreamedText("");
    setStreaming(false);
    setDone(false);
    generateMutation.reset();
  }

  // Show streaming output
  if (streaming || done) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Sparkles className="h-4 w-4 text-primary" />
            {streaming ? "Generating your cover letter..." : "Cover Letter Ready"}
            {streaming && (
              <Loader2 className="ml-auto h-4 w-4 animate-spin text-muted-foreground" />
            )}
            {done && (
              <CheckCircle className="ml-auto h-4 w-4 text-green-500" />
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border bg-muted/30 p-4">
            <pre className="whitespace-pre-wrap font-[family-name:var(--font-body)] text-sm leading-relaxed">
              {streamedText || (
                <span className="text-muted-foreground italic">
                  Waiting for first token...
                </span>
              )}
              {streaming && streamedText && (
                <span className="ml-0.5 inline-block h-4 w-2 animate-pulse bg-primary" />
              )}
            </pre>
          </div>
          {done && (
            <div className="mt-4 flex gap-2">
              <Button
                onClick={() => navigator.clipboard.writeText(streamedText)}
                variant="outline"
              >
                Copy to Clipboard
              </Button>
              <Button onClick={handleReset}>Generate Another</Button>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Sparkles className="h-4 w-4 text-primary" />
          Cover Letter Generator
        </CardTitle>
        <CardDescription>
          Generate a personalized cover letter using AI.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Company *</Label>
              <Input
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="e.g. Google"
              />
            </div>
            <div className="space-y-2">
              <Label>Job Title *</Label>
              <Input
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                placeholder="e.g. Software Engineer Intern"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Job Description *</Label>
            <textarea
              rows={5}
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the full job description here..."
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
              <Label>Tone</Label>
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={tone}
                onChange={(e) => setTone(e.target.value)}
              >
                <option value="formal">Formal</option>
                <option value="conversational">Conversational</option>
                <option value="enthusiastic">Enthusiastic</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label>Length</Label>
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={length}
                onChange={(e) => setLength(e.target.value)}
              >
                <option value="brief">Brief (~250 words)</option>
                <option value="standard">Standard (~400 words)</option>
                <option value="detailed">Detailed (~600 words)</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label>Emphasis</Label>
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={emphasis}
                onChange={(e) => setEmphasis(e.target.value)}
              >
                <option value="skills">Skills</option>
                <option value="achievements">Achievements</option>
                <option value="culture_fit">Culture Fit</option>
              </select>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>AI Provider</Label>
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={provider}
                onChange={(e) => {
                  setProvider(e.target.value);
                  setModel("");
                }}
              >
                <option value="">Use default</option>
                {providers?.map((p) => (
                  <option key={p.name} value={p.name}>
                    {p.display_name}
                  </option>
                ))}
              </select>
            </div>
            {selectedProvider && (
              <div className="space-y-2">
                <Label>Model</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                >
                  <option value="">Default</option>
                  {selectedProvider.models.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {generateMutation.isError && (
            <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {(generateMutation.error as { response?: { data?: { error?: string } } })
                ?.response?.data?.error ||
                "Something went wrong. Please try again."}
              {(generateMutation.error as { response?: { data?: { upgrade_url?: string } } })
                ?.response?.data?.upgrade_url && (
                <a
                  href="/pricing"
                  className="ml-2 underline hover:no-underline"
                >
                  See plans →
                </a>
              )}
            </div>
          )}

          {usage && usage.ai_monthly.cover_letter.limit !== null && (
            <div className="rounded-md border bg-muted/30 px-3 py-2 text-xs text-muted-foreground">
              <strong className="text-foreground">
                {usage.ai_monthly.cover_letter.used} /{" "}
                {usage.ai_monthly.cover_letter.limit}
              </strong>{" "}
              cover letters used this month on the{" "}
              <strong className="capitalize text-foreground">
                {usage.plan}
              </strong>{" "}
              plan.{" "}
              {usage.ai_monthly.cover_letter.used >=
                usage.ai_monthly.cover_letter.limit && (
                <a href="/pricing" className="text-primary hover:underline">
                  Upgrade for more →
                </a>
              )}
            </div>
          )}

          <Button
            type="submit"
            disabled={
              generateMutation.isPending ||
              !company ||
              !jobTitle ||
              !jobDescription ||
              !cvVersionId ||
              (usage?.ai_monthly.cover_letter.limit !== null &&
                usage !== undefined &&
                usage.ai_monthly.cover_letter.used >=
                  (usage.ai_monthly.cover_letter.limit ?? Infinity))
            }
            className="w-full"
          >
            {generateMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="mr-2 h-4 w-4" />
            )}
            Generate Cover Letter
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
