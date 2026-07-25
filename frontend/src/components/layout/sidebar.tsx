import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/ui-store";
import {
  Briefcase,
  ChevronLeft,
  ChevronRight,
  Eye,
  FileText,
  LayoutDashboard,
  ListTodo,
  Settings,
  Sparkles,
  Users,
} from "lucide-react";
import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/applications", icon: ListTodo, label: "Applications" },
  { to: "/watchlist", icon: Eye, label: "Watchlist" },
  { to: "/networking", icon: Users, label: "Networking" },
  { to: "/cv", icon: FileText, label: "CV Manager" },
  { to: "/ai", icon: Sparkles, label: "AI Assistant" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useUIStore();

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-30 flex h-svh flex-col border-r bg-sidebar transition-all duration-200",
        sidebarCollapsed ? "w-14" : "w-[220px]"
      )}
    >
      <div className="flex h-14 items-center gap-2 border-b px-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary">
          <Briefcase className="h-4 w-4 text-primary-foreground" />
        </div>
        {!sidebarCollapsed && (
          <span className="font-[family-name:var(--font-display)] text-lg font-semibold">
            Applywise
          </span>
        )}
      </div>

      <nav className="flex-1 space-y-1 p-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-sidebar-foreground hover:bg-sidebar-hover"
              )
            }
          >
            <item.icon className="h-4 w-4 shrink-0" />
            {!sidebarCollapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="border-t p-2">
        <button
          onClick={toggleSidebar}
          className="flex w-full items-center justify-center rounded-md p-2 text-muted-foreground transition-colors hover:bg-sidebar-hover hover:text-foreground"
        >
          {sidebarCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
      </div>
    </aside>
  );
}
