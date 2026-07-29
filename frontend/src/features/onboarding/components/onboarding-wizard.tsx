import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authApi } from "@/features/auth/api";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";
import {
  Briefcase,
  ChevronLeft,
  ChevronRight,
  FileText,
  GraduationCap,
  Target,
  User,
} from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

const steps = [
  { id: 1, label: "Profile", icon: User },
  { id: 2, label: "Education", icon: GraduationCap },
  { id: 3, label: "Resume", icon: FileText },
  { id: 4, label: "Interests", icon: Briefcase },
  { id: 5, label: "Goals", icon: Target },
];

export function OnboardingWizard() {
  const [currentStep, setCurrentStep] = useState(1);
  const navigate = useNavigate();
  const setUser = useAuthStore((s) => s.setUser);

  const [profile, setProfile] = useState({
    university: "",
    graduation_date: "",
    linkedin_url: "",
    target_roles: "",
    preferred_locations: "",
    weekly_goal: 10,
  });

  async function handleFinish() {
    try {
      const targetRoles = profile.target_roles
        .split(",")
        .map((r) => r.trim())
        .filter(Boolean);
      const locations = profile.preferred_locations
        .split(",")
        .map((l) => l.trim())
        .filter(Boolean);

      const res = await authApi.updateMe({
        profile: {
          university: profile.university,
          graduation_date: profile.graduation_date || null,
          linkedin_url: profile.linkedin_url,
          target_roles: targetRoles,
          preferred_locations: locations,
          weekly_goal: profile.weekly_goal,
          onboarding_completed: true,
        },
      });
      setUser(res.data);
    } catch {
      // continue anyway
    }
    navigate("/dashboard");
  }

  function handleNext() {
    if (currentStep < 5) setCurrentStep(currentStep + 1);
    else handleFinish();
  }

  function handleBack() {
    if (currentStep > 1) setCurrentStep(currentStep - 1);
  }

  function handleSkip() {
    handleFinish();
  }

  return (
    <div className="flex min-h-svh items-center justify-center bg-gradient-to-br from-background via-background to-primary/5 p-4">
      <div className="w-full max-w-2xl">
        {/* Progress */}
        <div className="mb-8 flex items-center justify-center gap-2">
          {steps.map((step) => (
            <div key={step.id} className="flex items-center gap-2">
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full text-xs font-medium transition-colors",
                  currentStep >= step.id
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground"
                )}
              >
                {step.id}
              </div>
              {step.id < 5 && (
                <div
                  className={cn(
                    "h-0.5 w-8 transition-colors",
                    currentStep > step.id ? "bg-primary" : "bg-muted"
                  )}
                />
              )}
            </div>
          ))}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>
              {currentStep === 1 && "Tell us about yourself"}
              {currentStep === 2 && "Education"}
              {currentStep === 3 && "Upload your resume"}
              {currentStep === 4 && "What are you looking for?"}
              {currentStep === 5 && "Set your goals"}
            </CardTitle>
            <CardDescription>
              {currentStep === 1 && "Basic info to personalize your experience."}
              {currentStep === 2 && "Your academic background."}
              {currentStep === 3 && "Upload a resume to enable AI features. You can skip this."}
              {currentStep === 4 && "Tell us your target roles and locations."}
              {currentStep === 5 && "How many applications per week do you want to target?"}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {currentStep === 1 && (
              <>
                <div className="space-y-2">
                  <Label>LinkedIn URL</Label>
                  <Input
                    type="url"
                    value={profile.linkedin_url}
                    onChange={(e) =>
                      setProfile({ ...profile, linkedin_url: e.target.value })
                    }
                    placeholder="https://linkedin.com/in/..."
                  />
                </div>
              </>
            )}

            {currentStep === 2 && (
              <>
                <div className="space-y-2">
                  <Label>University</Label>
                  <Input
                    value={profile.university}
                    onChange={(e) =>
                      setProfile({ ...profile, university: e.target.value })
                    }
                    placeholder="e.g. MIT"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Expected Graduation</Label>
                  <Input
                    type="date"
                    value={profile.graduation_date}
                    onChange={(e) =>
                      setProfile({
                        ...profile,
                        graduation_date: e.target.value,
                      })
                    }
                  />
                </div>
              </>
            )}

            {currentStep === 3 && (
              <div className="rounded-lg border-2 border-dashed p-8 text-center">
                <FileText className="mx-auto mb-3 h-10 w-10 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">
                  You can upload your resume from the CV Manager page after
                  onboarding.
                </p>
              </div>
            )}

            {currentStep === 4 && (
              <>
                <div className="space-y-2">
                  <Label>Target Roles</Label>
                  <Input
                    value={profile.target_roles}
                    onChange={(e) =>
                      setProfile({ ...profile, target_roles: e.target.value })
                    }
                    placeholder="e.g. Software Engineer, Data Scientist (comma-separated)"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Preferred Locations</Label>
                  <Input
                    value={profile.preferred_locations}
                    onChange={(e) =>
                      setProfile({
                        ...profile,
                        preferred_locations: e.target.value,
                      })
                    }
                    placeholder="e.g. San Francisco, New York, Remote (comma-separated)"
                  />
                </div>
              </>
            )}

            {currentStep === 5 && (
              <div className="space-y-2">
                <Label>Weekly Application Goal</Label>
                <Input
                  type="number"
                  min={1}
                  max={50}
                  value={profile.weekly_goal}
                  onChange={(e) =>
                    setProfile({
                      ...profile,
                      weekly_goal: Number(e.target.value) || 10,
                    })
                  }
                />
                <p className="text-xs text-muted-foreground">
                  We'll track your progress on the dashboard.
                </p>
              </div>
            )}
          </CardContent>

          <CardFooter className="flex justify-between">
            <div>
              {currentStep > 1 && (
                <Button variant="ghost" onClick={handleBack}>
                  <ChevronLeft className="mr-1 h-4 w-4" />
                  Back
                </Button>
              )}
            </div>
            <div className="flex gap-2">
              <Button variant="ghost" onClick={handleSkip}>
                Skip
              </Button>
              <Button onClick={handleNext}>
                {currentStep === 5 ? "Finish" : "Next"}
                {currentStep < 5 && <ChevronRight className="ml-1 h-4 w-4" />}
              </Button>
            </div>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
