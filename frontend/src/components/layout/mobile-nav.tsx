import { cn } from "@/lib/utils";
import {
  Eye,
  LayoutDashboard,
  ListTodo,
  Settings,
  Sparkles,
} from "lucide-react";
import { NavLink } from "react-router-dom";

const mobileNavItems = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Home" },
  { to: "/applications", icon: ListTodo, label: "Apps" },
  { to: "/watchlist", icon: Eye, label: "Watch" },
  { to: "/ai", icon: Sparkles, label: "AI" },
  { to: "/settings", icon: Settings, label: "More" },
];

export function MobileNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 border-t bg-background md:hidden">
      <div className="flex items-center justify-around py-2">
        {mobileNavItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                "flex flex-col items-center gap-0.5 px-3 py-1 text-xs transition-colors",
                isActive
                  ? "text-primary"
                  : "text-muted-foreground hover:text-foreground"
              )
            }
          >
            <item.icon className="h-5 w-5" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
