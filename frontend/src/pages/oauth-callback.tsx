import api from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";
import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

export function OAuthCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [error, setError] = useState("");

  useEffect(() => {
    const code = searchParams.get("code");
    const provider = searchParams.get("provider") || "google";

    if (!code) {
      setError("No authorization code received.");
      return;
    }

    const redirectUri = `${window.location.origin}/auth/callback?provider=${provider}`;
    const endpoint =
      provider === "linkedin"
        ? "/auth/social/linkedin/"
        : "/auth/social/google/";

    api
      .post(endpoint, { code, redirect_uri: redirectUri })
      .then((res) => {
        const { user, tokens } = res.data;
        setAuth(user, tokens.access, tokens.refresh);
        navigate(res.data.created ? "/onboarding" : "/dashboard");
      })
      .catch(() => {
        setError("Authentication failed. Please try again.");
      });
  }, [searchParams, navigate, setAuth]);

  if (error) {
    return (
      <div className="flex min-h-svh items-center justify-center">
        <div className="text-center">
          <p className="text-destructive">{error}</p>
          <a href="/login" className="mt-2 text-primary hover:underline">
            Back to login
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-svh items-center justify-center">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
        <span>Completing sign in...</span>
      </div>
    </div>
  );
}
