import { useUIStore } from "@/store/ui-store";
import { useEffect } from "react";

export function useTheme() {
  const { theme, setTheme } = useUIStore();

  useEffect(() => {
    const root = document.documentElement;

    function applyTheme(t: "light" | "dark" | "system") {
      if (t === "system") {
        const prefersDark = window.matchMedia(
          "(prefers-color-scheme: dark)"
        ).matches;
        root.classList.toggle("dark", prefersDark);
      } else {
        root.classList.toggle("dark", t === "dark");
      }
    }

    applyTheme(theme);

    if (theme === "system") {
      const mq = window.matchMedia("(prefers-color-scheme: dark)");
      const handler = () => applyTheme("system");
      mq.addEventListener("change", handler);
      return () => mq.removeEventListener("change", handler);
    }
  }, [theme]);

  return { theme, setTheme };
}
