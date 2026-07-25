import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authApi } from "@/features/auth/api";
import { useAuthStore } from "@/store/auth-store";
import { CheckCircle, Eye, EyeOff, Loader2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

export function AccountSettings() {
  const user = useAuthStore((s) => s.user);
  const refreshToken = useAuthStore((s) => s.refreshToken);

  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [show, setShow] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [success, setSuccess] = useState(false);

  async function handleChange(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});
    setSuccess(false);

    if (next.length < 8) {
      setErrors({ new_password: "Password must be at least 8 characters." });
      return;
    }
    if (next !== confirm) {
      setErrors({ confirm: "Passwords don't match." });
      return;
    }
    if (next === current) {
      setErrors({
        new_password: "New password must be different from the current one.",
      });
      return;
    }

    setSubmitting(true);
    try {
      await authApi.changePassword(current, next, refreshToken || undefined);
      setSuccess(true);
      setCurrent("");
      setNext("");
      setConfirm("");
    } catch (err: unknown) {
      const e = err as {
        response?: {
          status?: number;
          data?: Record<string, string[] | string>;
        };
      };
      const data = e.response?.data || {};
      const collected: Record<string, string> = {};
      // API returns field errors as arrays; flatten first message per field
      for (const [key, value] of Object.entries(data)) {
        if (Array.isArray(value)) collected[key] = value[0] as string;
        else if (typeof value === "string") collected[key] = value;
      }
      if (e.response?.status === 429) {
        collected.__form =
          "Too many attempts. Please try again in a minute.";
      } else if (!Object.keys(collected).length) {
        collected.__form = "Something went wrong. Please try again.";
      }
      setErrors(collected);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-2xl space-y-8">
      <div>
        <h3 className="text-sm font-medium">Email</h3>
        <p className="mt-1 text-sm text-muted-foreground">{user?.email}</p>
      </div>

      <div>
        <h3 className="text-sm font-medium">Change password</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Enter your current password and choose a new one. Other active
          sessions will be signed out.
        </p>

        <form onSubmit={handleChange} className="mt-4 space-y-4">
          {success && (
            <div className="flex items-start gap-2 rounded-md border border-green-500/30 bg-green-500/10 p-3 text-sm text-green-600 dark:text-green-400">
              <CheckCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>
                Password updated. Any other sessions have been signed out.
              </span>
            </div>
          )}

          {errors.__form && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {errors.__form}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="current_password">Current password</Label>
            <Input
              id="current_password"
              type={show ? "text" : "password"}
              autoComplete="current-password"
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
              required
            />
            {errors.current_password && (
              <p className="text-xs text-destructive">
                {errors.current_password}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="new_password">New password</Label>
            <div className="relative">
              <Input
                id="new_password"
                type={show ? "text" : "password"}
                autoComplete="new-password"
                placeholder="At least 8 characters"
                value={next}
                onChange={(e) => setNext(e.target.value)}
                required
              />
              <button
                type="button"
                onClick={() => setShow(!show)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                tabIndex={-1}
                aria-label={show ? "Hide passwords" : "Show passwords"}
              >
                {show ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
            {errors.new_password && (
              <p className="text-xs text-destructive">{errors.new_password}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirm_password">Confirm new password</Label>
            <Input
              id="confirm_password"
              type={show ? "text" : "password"}
              autoComplete="new-password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
            />
            {errors.confirm && (
              <p className="text-xs text-destructive">{errors.confirm}</p>
            )}
          </div>

          <div className="flex items-center gap-4">
            <Button
              type="submit"
              disabled={submitting || !current || !next || !confirm}
            >
              {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Update password
            </Button>
            <Link
              to="/forgot-password"
              className="text-xs text-muted-foreground hover:text-primary hover:underline"
            >
              Forgot current password?
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
