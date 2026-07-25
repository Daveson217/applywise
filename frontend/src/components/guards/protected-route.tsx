import { useAuthStore } from "@/store/auth-store";
import { Navigate, Outlet } from "react-router-dom";

export function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
