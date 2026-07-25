import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authApi } from "@/features/auth/api";
import { AlertCircle, CheckCircle, Eye, EyeOff, Loader2 } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

export function ResetPasswordPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const token = params.get("token") || "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  if (!token) {
    return (
      <Card>
        <CardContent className="py-10 text-center">
          <AlertCircle className="mx-auto mb-4 h-12 w-12 text-destructive" />
          <h3 className="text-lg font-semibold">Invalid link</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            This password reset link is missing its token. Request a new one.
          </p>
          <Link
            to="/forgot-password"
            className="mt-4 inline-block text-sm text-primary hover:underline"
          >
            Request a new reset link
          </Link>
        </CardContent>
      </Card>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords don't match.");
      return;
    }

    setSubmitting(true);
    try {
      await authApi.confirmPasswordReset(token, password);
      setSuccess(true);
      // Redirect to login after a moment
      setTimeout(() => navigate("/login"), 2500);
    } catch (err: unknown) {
      const e = err as {
        response?: {
          status?: number;
          data?: { error?: string; new_password?: string[] };
        };
      };
      const data = e.response?.data;
      if (data?.new_password?.length) {
        setError(data.new_password[0]);
      } else if (data?.error) {
        setError(data.error);
      } else if (e.response?.status === 429) {
        setError("Too many attempts. Please try again in a minute.");
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (success) {
    return (
      <Card>
        <CardContent className="py-10 text-center">
          <CheckCircle className="mx-auto mb-4 h-12 w-12 text-green-500" />
          <h3 className="text-lg font-semibold">Password updated</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Redirecting you to sign in…
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Choose a new password</CardTitle>
        <CardDescription>
          Pick a strong password you don&apos;t use elsewhere.
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {error && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="password">New password</Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                placeholder="At least 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                tabIndex={-1}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirm">Confirm password</Label>
            <Input
              id="confirm"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
            />
          </div>
        </CardContent>
        <CardFooter>
          <Button
            type="submit"
            className="w-full"
            disabled={submitting || !password || !confirm}
          >
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Update password
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
