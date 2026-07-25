import { CommandPalette } from "@/components/command-palette";
import { GuestRoute } from "@/components/guards/guest-route";
import { ProtectedRoute } from "@/components/guards/protected-route";
import { AuthLayout } from "@/components/layout/auth-layout";
import { RootLayout } from "@/components/layout/root-layout";
import { ShortcutReference } from "@/components/shortcut-reference";
import { useKeyboardShortcuts } from "@/hooks/use-keyboard-shortcuts";
import { useTheme } from "@/hooks/use-theme";
import { AIAssistantPage } from "@/pages/ai-assistant";
import { ApplicationsPage } from "@/pages/applications";
import { CVPage } from "@/pages/cv";
import { DashboardPage } from "@/pages/dashboard";
import { ForgotPasswordPage } from "@/pages/forgot-password";
import { LoginPage } from "@/pages/login";
import { NetworkingPage } from "@/pages/networking";
import { OAuthCallbackPage } from "@/pages/oauth-callback";
import { OnboardingPage } from "@/pages/onboarding";
import { PricingPage } from "@/pages/pricing";
import { RegisterPage } from "@/pages/register";
import { ResetPasswordPage } from "@/pages/reset-password";
import { SettingsPage } from "@/pages/settings";
import { WatchlistPage } from "@/pages/watchlist";
import { useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

export default function App() {
  useTheme();
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);

  useKeyboardShortcuts({
    onOpenCommandPalette: () => setPaletteOpen(true),
    onShowHelp: () => setHelpOpen(true),
  });

  return (
    <>
      <Routes>
        <Route element={<GuestRoute />}>
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
          </Route>
        </Route>

        <Route element={<ProtectedRoute />}>
          <Route path="/onboarding" element={<OnboardingPage />} />
          <Route element={<RootLayout />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/applications" element={<ApplicationsPage />} />
            <Route path="/watchlist" element={<WatchlistPage />} />
            <Route path="/networking" element={<NetworkingPage />} />
            <Route path="/cv" element={<CVPage />} />
            <Route path="/ai" element={<AIAssistantPage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Route>

        <Route path="/auth/callback" element={<OAuthCallbackPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />
      <ShortcutReference open={helpOpen} onOpenChange={setHelpOpen} />
    </>
  );
}
