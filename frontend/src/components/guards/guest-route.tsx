import { useAuthStore } from "@/store/auth-store";
import { Navigate, Outlet } from "react-router-dom";

export function GuestRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}
