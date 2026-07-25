import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authApi } from "@/features/auth/api";
import { useAuthStore } from "@/store/auth-store";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";

interface ProfileFormData {
  first_name: string;
  last_name: string;
  university: string;
  graduation_date: string;
  linkedin_url: string;
  github_url: string;
  website_url: string;
  bio: string;
  weekly_goal: number;
}

export function ProfileForm() {
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const [saved, setSaved] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<ProfileFormData>({
    defaultValues: {
      first_name: user?.first_name || "",
      last_name: user?.last_name || "",
      university: user?.profile?.university || "",
      graduation_date: user?.profile?.graduation_date || "",
      linkedin_url: user?.profile?.linkedin_url || "",
      github_url: user?.profile?.github_url || "",
      website_url: user?.profile?.website_url || "",
      bio: user?.profile?.bio || "",
      weekly_goal: user?.profile?.weekly_goal || 10,
    },
  });

  async function onSubmit(data: ProfileFormData) {
    const { first_name, last_name, ...profileData } = data;
    const res = await authApi.updateMe({
      first_name,
      last_name,
      profile: {
        ...profileData,
        graduation_date: profileData.graduation_date || null,
      },
    });
    setUser(res.data);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="max-w-2xl space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>First Name</Label>
          <Input {...register("first_name")} />
        </div>
        <div className="space-y-2">
          <Label>Last Name</Label>
          <Input {...register("last_name")} />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>University</Label>
          <Input {...register("university")} />
        </div>
        <div className="space-y-2">
          <Label>Graduation Date</Label>
          <Input type="date" {...register("graduation_date")} />
        </div>
      </div>
      <div className="space-y-2">
        <Label>LinkedIn URL</Label>
        <Input type="url" {...register("linkedin_url")} />
      </div>
      <div className="space-y-2">
        <Label>GitHub URL</Label>
        <Input type="url" {...register("github_url")} />
      </div>
      <div className="space-y-2">
        <Label>Website URL</Label>
        <Input type="url" {...register("website_url")} />
      </div>
      <div className="space-y-2">
        <Label>Bio</Label>
        <textarea
          rows={3}
          className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          {...register("bio")}
        />
      </div>
      <div className="space-y-2">
        <Label>Weekly Application Goal</Label>
        <Input type="number" min={1} max={50} {...register("weekly_goal")} />
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {saved ? "Saved!" : "Save Changes"}
      </Button>
    </form>
  );
}
