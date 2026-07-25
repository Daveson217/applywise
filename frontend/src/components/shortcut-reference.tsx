import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const shortcuts = [
  { keys: ["⌘", "K"], label: "Open command palette" },
  { keys: ["D"], label: "Go to Dashboard" },
  { keys: ["A"], label: "Go to Applications" },
  { keys: ["W"], label: "Go to Watchlist" },
  { keys: ["?"], label: "Show this reference" },
  { keys: ["Esc"], label: "Close modal" },
];

interface ShortcutReferenceProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ShortcutReference({
  open,
  onOpenChange,
}: ShortcutReferenceProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Keyboard Shortcuts</DialogTitle>
          <DialogDescription>
            Boost your speed with these shortcuts.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          {shortcuts.map((s) => (
            <div
              key={s.label}
              className="flex items-center justify-between rounded-md px-3 py-2 hover:bg-muted/50"
            >
              <span className="text-sm">{s.label}</span>
              <div className="flex gap-1">
                {s.keys.map((k) => (
                  <kbd
                    key={k}
                    className="rounded border bg-muted px-2 py-0.5 text-xs font-mono"
                  >
                    {k}
                  </kbd>
                ))}
              </div>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
