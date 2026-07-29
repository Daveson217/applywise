import { Separator } from "@/components/ui/separator";
import { AccountSettings } from "@/features/settings/components/account-settings";
import { AppearanceSettings } from "@/features/settings/components/appearance-settings";
import { JobPreferences } from "@/features/settings/components/job-preferences";
import { ProfileForm } from "@/features/settings/components/profile-form";
import { UsagePanel } from "@/features/settings/components/usage-panel";
import { cn } from "@/lib/utils";
import { useState } from "react";

const tabs = [
  { id: "profile", label: "Profile" },
  { id: "job-preferences", label: "Job Preferences" },
  { id: "appearance", label: "Appearance" },
  { id: "usage", label: "Usage & Plan" },
  { id: "account", label: "Account" },
];

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState("profile");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-[family-name:var(--font-display)] text-2xl font-bold">
          Settings
        </h1>
        <p className="text-muted-foreground">
          Manage your account and preferences.
        </p>
      </div>

      <div className="flex gap-2 border-b">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "border-b-2 px-4 py-2 text-sm font-medium transition-colors",
              activeTab === tab.id
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <Separator className="hidden" />

      {activeTab === "profile" && <ProfileForm />}
      {activeTab === "job-preferences" && <JobPreferences />}
      {activeTab === "appearance" && <AppearanceSettings />}
      {activeTab === "usage" && <UsagePanel />}
      {activeTab === "account" && <AccountSettings />}
    </div>
  );
}
