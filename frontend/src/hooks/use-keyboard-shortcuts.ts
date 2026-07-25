import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

interface UseShortcutsOptions {
  onOpenCommandPalette: () => void;
  onShowHelp: () => void;
}

export function useKeyboardShortcuts({
  onOpenCommandPalette,
  onShowHelp,
}: UseShortcutsOptions) {
  const navigate = useNavigate();

  useEffect(() => {
    function handler(e: KeyboardEvent) {
      // Cmd+K / Ctrl+K — command palette
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        onOpenCommandPalette();
        return;
      }

      // Skip single-key shortcuts when typing in inputs
      const target = e.target as HTMLElement;
      const tag = target.tagName;
      if (
        tag === "INPUT" ||
        tag === "TEXTAREA" ||
        tag === "SELECT" ||
        target.isContentEditable
      ) {
        return;
      }

      // Skip when modifier keys are pressed (handled above for cmd+k)
      if (e.metaKey || e.ctrlKey || e.altKey) return;

      switch (e.key) {
        case "d":
          e.preventDefault();
          navigate("/dashboard");
          break;
        case "a":
          e.preventDefault();
          navigate("/applications");
          break;
        case "w":
          e.preventDefault();
          navigate("/watchlist");
          break;
        case "?":
          e.preventDefault();
          onShowHelp();
          break;
      }
    }

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [navigate, onOpenCommandPalette, onShowHelp]);
}
