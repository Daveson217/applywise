import { Briefcase } from "lucide-react";
import { Outlet } from "react-router-dom";

export function AuthLayout() {
  return (
    <div className="flex min-h-svh items-center justify-center bg-gradient-to-br from-background via-background to-primary/5 p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary">
            <Briefcase className="h-6 w-6 text-primary-foreground" />
          </div>
          <h1 className="font-[family-name:var(--font-display)] text-3xl font-bold">
            Applywise
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Your career command center
          </p>
        </div>
        <Outlet />
      </div>
    </div>
  );
}
