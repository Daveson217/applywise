import { create } from "zustand";
import { persist } from "zustand/middleware";

type Theme = "light" | "dark" | "system";
type ApplicationsView = "list" | "kanban";

interface UIState {
  theme: Theme;
  sidebarCollapsed: boolean;
  applicationsView: ApplicationsView;
  setTheme: (theme: Theme) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setApplicationsView: (view: ApplicationsView) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      theme: "dark",
      sidebarCollapsed: false,
      applicationsView: "list",
      setTheme: (theme) => set({ theme }),
      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      setApplicationsView: (view) => set({ applicationsView: view }),
    }),
    {
      name: "applywise-ui",
    }
  )
);
