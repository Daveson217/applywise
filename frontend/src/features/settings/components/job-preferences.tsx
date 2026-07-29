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

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {saved ? "Saved!" : "Save Preferences"}
      </Button>
    </form>
  );
}
