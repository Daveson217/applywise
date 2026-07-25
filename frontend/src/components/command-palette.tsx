import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog";
import { useTheme } from "@/hooks/use-theme";
import { cn } from "@/lib/utils";
import {
  Eye,
  FileText,
  LayoutDashboard,
  ListTodo,
  Moon,
  Settings,
  Sparkles,
  Sun,
  Users,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

interface CommandItem {
  id: string;
  label: string;
  icon: typeof LayoutDashboard;
  action: () => void;
  shortcut?: string;
}

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate();
  const { theme, setTheme } = useTheme();
  const [query, setQuery] = useState("");
  const [selectedIdx, setSelectedIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const items: CommandItem[] = [
    {
      id: "dashboard",
      label: "Go to Dashboard",
      icon: LayoutDashboard,
      action: () => navigate("/dashboard"),
      shortcut: "D",
    },
    {
      id: "applications",
      label: "Go to Applications",
      icon: ListTodo,
      action: () => navigate("/applications"),
      shortcut: "A",
    },
    {
      id: "watchlist",
      label: "Go to Watchlist",
      icon: Eye,
      action: () => navigate("/watchlist"),
      shortcut: "W",
    },
    {
      id: "networking",
      label: "Go to Networking",
      icon: Users,
      action: () => navigate("/networking"),
    },
    {
      id: "cv",
      label: "Go to CV Manager",
      icon: FileText,
      action: () => navigate("/cv"),
    },
    {
      id: "ai",
      label: "Go to AI Assistant",
      icon: Sparkles,
      action: () => navigate("/ai"),
    },
    {
      id: "settings",
      label: "Go to Settings",
      icon: Settings,
      action: () => navigate("/settings"),
    },
    {
      id: "toggle-theme",
      label: `Switch to ${theme === "dark" ? "Light" : "Dark"} Mode`,
      icon: theme === "dark" ? Sun : Moon,
      action: () => setTheme(theme === "dark" ? "light" : "dark"),
    },
  ];

  const filtered = items.filter((item) =>
    item.label.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    if (open) {
      setQuery("");
      setSelectedIdx(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  useEffect(() => {
    setSelectedIdx(0);
  }, [query]);

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIdx((i) => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const item = filtered[selectedIdx];
      if (item) {
        item.action();
        onOpenChange(false);
      }
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="p-0 sm:max-w-lg">
        <DialogTitle className="sr-only">Command Palette</DialogTitle>
        <div className="border-b px-4 py-3">
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a command or search..."
            className="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
        </div>
        <div className="max-h-80 overflow-y-auto p-2">
          {filtered.length === 0 ? (
            <p className="px-3 py-6 text-center text-sm text-muted-foreground">
              No results found.
            </p>
          ) : (
            filtered.map((item, i) => (
              <button
                key={item.id}
                onClick={() => {
                  item.action();
                  onOpenChange(false);
                }}
                onMouseEnter={() => setSelectedIdx(i)}
                className={cn(
                  "flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm transition-colors",
                  i === selectedIdx
                    ? "bg-accent text-accent-foreground"
                    : "hover:bg-accent/50"
                )}
              >
                <item.icon className="h-4 w-4 text-muted-foreground" />
                <span className="flex-1">{item.label}</span>
                {item.shortcut && (
                  <kbd className="rounded border bg-muted px-1.5 py-0.5 text-xs">
                    {item.shortcut}
                  </kbd>
                )}
              </button>
            ))
          )}
        </div>
        <div className="border-t px-4 py-2 text-xs text-muted-foreground">
          <kbd className="rounded border bg-muted px-1">↑</kbd>
          <kbd className="ml-0.5 rounded border bg-muted px-1">↓</kbd> navigate
          <kbd className="ml-3 rounded border bg-muted px-1">↵</kbd> select
          <kbd className="ml-3 rounded border bg-muted px-1">esc</kbd> close
        </div>
      </DialogContent>
    </Dialog>
  );
}
