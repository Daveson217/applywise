import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authApi } from "@/features/auth/api";
import { useAuthStore } from "@/store/auth-store";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";

const JOB_TYPE_OPTIONS = [
  { value: "internship", label: "Internship" },
  { value: "new_grad", label: "New Grad / Entry Level" },
  { value: "full_time", label: "Full-Time" },
  { value: "contract", label: "Contract" },
  { value: "part_time", label: "Part-Time" },
] as const;

interface FormData {
  target_roles: string;
  excluded_keywords: string;
  preferred_locations: string;
}

// Parse a comma-separated string into a trimmed, non-empty string list.
function splitList(v: string): string[] {
  return v
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

export function JobPreferences() {
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const [saved, setSaved] = useState(false);
  const [jobTypes, setJobTypes] = useState<string[]>(
    user?.profile?.target_job_types ?? []
  );
  const [aiEnabled, setAiEnabled] = useState<boolean>(
    user?.profile?.ai_relevance_enabled ?? false
  );
  const [aiThreshold, setAiThreshold] = useState<number>(
    user?.profile?.ai_relevance_threshold ?? 0.6
  );
  const [digestFrequency, setDigestFrequency] = useState<
    "off" | "daily" | "weekly"
  >(user?.profile?.watchlist_digest_frequency ?? "daily");

  const {
    register,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<FormData>({
    defaultValues: {
      target_roles: (user?.profile?.target_roles ?? []).join(", "),
      excluded_keywords: (user?.profile?.excluded_keywords ?? []).join(", "),
      preferred_locations: (user?.profile?.preferred_locations ?? []).join(
        ", "
      ),
    },
  });

  function toggleJobType(value: string) {
    setJobTypes((cur) =>
      cur.includes(value) ? cur.filter((v) => v !== value) : [...cur, value]
    );
  }

  async function onSubmit(data: FormData) {
    const res = await authApi.updateMe({
      profile: {
        target_roles: splitList(data.target_roles),
        excluded_keywords: splitList(data.excluded_keywords),
        preferred_locations: splitList(data.preferred_locations),
        target_job_types: jobTypes,
        ai_relevance_enabled: aiEnabled,
        ai_relevance_threshold: aiThreshold,
        watchlist_digest_frequency: digestFrequency,
      },
    });
    setUser(res.data);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="max-w-2xl space-y-6">
      <div>
        <p className="text-sm text-muted-foreground">
          These preferences filter job alerts across every company on your
          watchlist. Rules on individual companies override these when set;
          excluded keywords always apply.
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="target_roles">Target roles / keywords</Label>
        <Input
          id="target_roles"
          placeholder="e.g. ML, backend, data engineer"
          {...register("target_roles")}
        />
        <p className="text-xs text-muted-foreground">
          Comma-separated. Synonyms are expanded automatically — "ML" also
          matches "Machine Learning".
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="excluded_keywords">Excluded keywords</Label>
        <Input
          id="excluded_keywords"
          placeholder="e.g. senior, staff, principal"
          {...register("excluded_keywords")}
        />
        <p className="text-xs text-muted-foreground">
          Postings containing any of these words are skipped.
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="preferred_locations">Preferred locations</Label>
        <Input
          id="preferred_locations"
          placeholder="e.g. remote, new york, london"
          {...register("preferred_locations")}
        />
      </div>

      <div className="space-y-2">
        <Label>Job types</Label>
        <div className="flex flex-wrap gap-3">
          {JOB_TYPE_OPTIONS.map((opt) => {
            const checked = jobTypes.includes(opt.value);
            return (
              <label
                key={opt.value}
                className="flex cursor-pointer items-center gap-2 rounded-md border border-input bg-background px-3 py-2 text-sm hover:bg-accent"
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggleJobType(opt.value)}
                  className="h-4 w-4"
                />
                {opt.label}
              </label>
            );
          })}
        </div>
        <p className="text-xs text-muted-foreground">
          Leave empty to receive alerts for any job type.
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="digest_frequency">Email digest</Label>
        <select
          id="digest_frequency"
          value={digestFrequency}
          onChange={(e) =>
            setDigestFrequency(e.target.value as "off" | "daily" | "weekly")
          }
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="off">Off — no emails</option>
          <option value="daily">Daily summary</option>
          <option value="weekly">Weekly summary</option>
        </select>
        <p className="text-xs text-muted-foreground">
          Matched jobs always appear in the Watchlist → Matched Jobs tab.
          This controls how often we email you a summary of new matches.
        </p>
      </div>

      <div className="space-y-2 rounded-md border border-input bg-muted/30 p-4">
        <label className="flex cursor-pointer items-start gap-3">
          <input
            type="checkbox"
            checked={aiEnabled}
            onChange={(e) => setAiEnabled(e.target.checked)}
            className="mt-1 h-4 w-4"
          />
          <div>
            <div className="text-sm font-medium">
              AI relevance scoring{" "}
              <span className="ml-1 rounded bg-primary/10 px-1.5 py-0.5 text-xs text-primary">
                Pro
              </span>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              After keyword matching, each new posting is scored by an LLM
              against your preferences. Only postings that clear the
              relevance threshold trigger a notification.
            </p>
          </div>
        </label>

        {aiEnabled && (
          <div className="ml-7 space-y-1 pt-1">
            <div className="flex items-center justify-between text-sm">
              <Label htmlFor="ai-threshold">Relevance threshold</Label>
              <span className="tabular-nums text-muted-foreground">
                {aiThreshold.toFixed(2)}
              </span>
            </div>
            <input
              id="ai-threshold"
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={aiThreshold}
              onChange={(e) => setAiThreshold(Number(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              Lower = more alerts, some off-target. Higher = fewer alerts,
              stricter fit. Default 0.60.
            </p>
          </div>
        )}
      </div>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {saved ? "Saved!" : "Save Preferences"}
      </Button>
    </form>
  );
}
