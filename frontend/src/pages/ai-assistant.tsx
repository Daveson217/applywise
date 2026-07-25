import { CoverLetterForm } from "@/features/ai/components/cover-letter-form";
import { QAForm } from "@/features/ai/components/qa-form";
import {
  ATSScoreForm,
  FitScoreForm,
} from "@/features/ai/components/scoring-forms";
import { cn } from "@/lib/utils";
import { useState } from "react";

const tabs = [
  { id: "cover-letter", label: "Cover Letter" },
  { id: "qa", label: "Q&A" },
  { id: "fit-score", label: "Fit Score" },
  { id: "ats-score", label: "ATS Score" },
];

export function AIAssistantPage() {
  const [activeTab, setActiveTab] = useState("cover-letter");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-[family-name:var(--font-display)] text-2xl font-bold">
          AI Assistant
        </h1>
        <p className="text-muted-foreground">
          Generate cover letters, answer questions, and score your applications.
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

      {activeTab === "cover-letter" && <CoverLetterForm />}
      {activeTab === "qa" && <QAForm />}
      {activeTab === "fit-score" && <FitScoreForm />}
      {activeTab === "ats-score" && <ATSScoreForm />}
    </div>
  );
}
