import { useTheme } from "@/hooks/use-theme";
import { cn } from "@/lib/utils";
import { Monitor, Moon, Sun } from "lucide-react";

const themes = [
  { value: "light" as const, label: "Light", icon: Sun },
  { value: "dark" as const, label: "Dark", icon: Moon },
  { value: "system" as const, label: "System", icon: Monitor },
];

export function AppearanceSettings() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h3 className="text-sm font-medium">Theme</h3>
        <p className="text-sm text-muted-foreground">
          Select your preferred color scheme.
        </p>
        <div className="mt-3 flex gap-3">
          {themes.map((t) => (
            <button
              key={t.value}
              onClick={() => setTheme(t.value)}
              className={cn(
                "flex flex-col items-center gap-2 rounded-lg border p-4 transition-colors",
                theme === t.value
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50"
              )}
            >
              <t.icon className="h-5 w-5" />
              <span className="text-sm font-medium">{t.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
