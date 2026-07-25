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
import { CheckCircle, Loader2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  // Show the same success state whether the email exists or not — the
  // backend won't tell us, and neither should this UI.
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;
    setSubmitting(true);
    setError("");
    try {
      await authApi.requestPasswordReset(email.trim());
      setSent(true);
    } catch (err: unknown) {
      const e = err as { response?: { status?: number } };
      if (e.response?.status === 429) {
        setError("Too many requests. Please try again in a minute.");
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (sent) {
    return (
      <Card>
        <CardContent className="py-10 text-center">
          <CheckCircle className="mx-auto mb-4 h-12 w-12 text-green-500" />
          <h3 className="text-lg font-semibold">Check your inbox</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            If an account exists for <strong>{email}</strong>, we&apos;ve sent
            a password reset link. It expires in 1 hour.
          </p>
          <Link
            to="/login"
            className="mt-4 inline-block text-sm text-primary hover:underline"
          >
            ← Back to sign in
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Reset your password</CardTitle>
        <CardDescription>
          Enter your email and we&apos;ll send you a link to choose a new one.
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
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
        </CardContent>
        <CardFooter className="flex-col gap-3">
          <Button
            type="submit"
            className="w-full"
            disabled={submitting || !email.trim()}
          >
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Send reset link
          </Button>
          <Link
            to="/login"
            className="text-sm text-muted-foreground hover:underline"
          >
            Back to sign in
          </Link>
        </CardFooter>
      </form>
    </Card>
  );
}
