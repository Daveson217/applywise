import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { authApi } from "@/features/auth/api";
import { useProviders } from "@/features/ai/hooks";
import { useAuthStore } from "@/store/auth-store";
import { Loader2 } from "lucide-react";
import { useMemo, useState } from "react";

export function AIModelSettings() {
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const { data: providers, isLoading } = useProviders();
  const [saved, setSaved] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [provider, setProvider] = useState(
    user?.profile?.default_llm_provider ?? "gemini"
  );
  const [model, setModel] = useState(
    user?.profile?.default_llm_model ?? "gemini-3.5-flash-lite"
  );

  // Models available for the currently selected provider.
  const availableModels = useMemo(() => {
    const p = providers?.find((x) => x.name === provider);
    return p?.models ?? [];
  }, [providers, provider]);

  function handleProviderChange(next: string) {
    setProvider(next);
    // Reset model to the first available for the new provider so we never
    // send an invalid provider/model combination.
    const p = providers?.find((x) => x.name === next);
    if (p?.models?.length) {
      setModel(p.models[0]);
    }
  }

  async function handleSave() {
    setSubmitting(true);
    try {
      const res = await authApi.updateMe({
        profile: {
          default_llm_provider: provider,
          default_llm_model: model,
        },
      });
      setUser(res.data);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-2xl space-y-6">
      <p className="text-sm text-muted-foreground">
        Choose which model powers your AI features (cover letters, Q&amp;A,
        fit scoring, ATS scoring, watchlist relevance scoring). Free tier is
        limited to Gemini; Pro unlocks OpenAI and Anthropic.
      </p>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading providers…</p>
      ) : (
        <>
          <div className="space-y-2">
            <Label htmlFor="ai-provider">Provider</Label>
            <select
              id="ai-provider"
              value={provider}
              onChange={(e) => handleProviderChange(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {providers?.map((p) => (
                <option key={p.name} value={p.name}>
                  {p.display_name}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="ai-model">Model</Label>
            <select
              id="ai-model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {availableModels.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
            <p className="text-xs text-muted-foreground">
              If a model returns 404 in the logs, it may have been deprecated
              by the provider. Pick another from the list.
            </p>
          </div>

          <Button onClick={handleSave} disabled={submitting}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {saved ? "Saved!" : "Save"}
          </Button>
        </>
      )}
    </div>
  );
}
