import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/ui-store";
import { Outlet } from "react-router-dom";

import { MobileNav } from "./mobile-nav";
import { Sidebar } from "./sidebar";
import { TopNav } from "./top-nav";

export function RootLayout() {
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed);

  return (
    <div className="min-h-svh">
      {/* Desktop sidebar */}
      <div className="hidden md:block">
        <Sidebar />
      </div>

      <div
        className={cn(
          "transition-all duration-200",
          "md:ml-14",
          !sidebarCollapsed && "md:ml-[220px]"
        )}
      >
        <TopNav />
        <main className="p-4 pb-20 md:p-6 md:pb-6">
          <Outlet />
        </main>
      </div>

      {/* Mobile bottom nav */}
      <MobileNav />
    </div>
  );
}
