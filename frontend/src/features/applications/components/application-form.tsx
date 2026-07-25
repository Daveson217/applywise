import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  JOB_TYPE_OPTIONS,
  PRIORITY_OPTIONS,
  SOURCE_OPTIONS,
  STATUS_OPTIONS,
} from "@/lib/constants";
import type { Application } from "@/types/application";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";

import { useCreateApplication, useUpdateApplication } from "../hooks";
import { type ApplicationFormData, applicationSchema } from "../schemas";

interface ApplicationFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  application?: Application | null;
}

export function ApplicationForm({
  open,
  onOpenChange,
  application,
}: ApplicationFormProps) {
  const createMutation = useCreateApplication();
  const updateMutation = useUpdateApplication();
  const isEditing = !!application;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ApplicationFormData>({
    resolver: zodResolver(applicationSchema),
    defaultValues: {
      job_type: "internship",
      status: "saved",
      priority: "medium",
      salary_currency: "USD",
      is_remote: false,
    },
  });

  useEffect(() => {
    if (application) {
      reset({
        company: application.company,
        role: application.role,
        job_type: application.job_type,
        status: application.status,
        priority: application.priority,
        applied_date: application.applied_date || "",
        deadline: application.deadline || "",
        salary_min: application.salary_min || "",
        salary_max: application.salary_max || "",
        salary_currency: application.salary_currency,
        location: application.location,
        is_remote: application.is_remote,
        url: application.url,
        source: application.source,
        notes: application.notes,
        follow_up_date: application.follow_up_date || "",
        recruiter_name: application.recruiter_name,
        recruiter_email: application.recruiter_email,
      });
    } else {
      reset({
        job_type: "internship",
        status: "saved",
        priority: "medium",
        salary_currency: "USD",
        is_remote: false,
      });
    }
  }, [application, reset]);

  async function onSubmit(data: ApplicationFormData) {
    const cleaned = {
      ...data,
      applied_date: data.applied_date || null,
      deadline: data.deadline || null,
      follow_up_date: data.follow_up_date || null,
      salary_min:
        typeof data.salary_min === "number" ? data.salary_min : null,
      salary_max:
        typeof data.salary_max === "number" ? data.salary_max : null,
    };

    if (isEditing && application) {
      await updateMutation.mutateAsync({ id: application.id, data: cleaned });
    } else {
      await createMutation.mutateAsync(cleaned);
    }
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? "Edit Application" : "Add Application"}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? "Update the details of your application."
              : "Track a new job application."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="company">Company *</Label>
              <Input id="company" {...register("company")} />
              {errors.company && (
                <p className="text-xs text-destructive">
                  {errors.company.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="role">Role *</Label>
              <Input id="role" {...register("role")} />
              {errors.role && (
                <p className="text-xs text-destructive">
                  {errors.role.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="job_type">Job Type *</Label>
              <select
                id="job_type"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                {...register("job_type")}
              >
                {JOB_TYPE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <select
                id="status"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                {...register("status")}
              >
                {STATUS_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="priority">Priority</Label>
              <select
                id="priority"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                {...register("priority")}
              >
                {PRIORITY_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="source">Source</Label>
              <select
                id="source"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                {...register("source")}
              >
                <option value="">Select source</option>
                {SOURCE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="location">Location</Label>
              <Input
                id="location"
                placeholder="City, State"
                {...register("location")}
              />
            </div>
            <div className="flex items-end gap-2 pb-1">
              <input
                type="checkbox"
                id="is_remote"
                className="h-4 w-4 rounded"
                {...register("is_remote")}
              />
              <Label htmlFor="is_remote">Remote</Label>
            </div>
            <div className="space-y-2">
              <Label htmlFor="url">Job URL</Label>
              <Input
                id="url"
                type="url"
                placeholder="https://..."
                {...register("url")}
              />
              {errors.url && (
                <p className="text-xs text-destructive">
                  {errors.url.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="applied_date">Applied Date</Label>
              <Input
                id="applied_date"
                type="date"
                {...register("applied_date")}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="deadline">Deadline</Label>
              <Input id="deadline" type="date" {...register("deadline")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="follow_up_date">Follow-up Date</Label>
              <Input
                id="follow_up_date"
                type="date"
                {...register("follow_up_date")}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="salary_min">Salary Min</Label>
              <Input
                id="salary_min"
                type="number"
                placeholder="e.g. 80000"
                {...register("salary_min")}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="salary_max">Salary Max</Label>
              <Input
                id="salary_max"
                type="number"
                placeholder="e.g. 120000"
                {...register("salary_max")}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="recruiter_name">Recruiter Name</Label>
              <Input id="recruiter_name" {...register("recruiter_name")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="recruiter_email">Recruiter Email</Label>
              <Input
                id="recruiter_email"
                type="email"
                {...register("recruiter_email")}
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="notes">Notes</Label>
            <textarea
              id="notes"
              rows={3}
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              {...register("notes")}
            />
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              {isEditing ? "Save Changes" : "Add Application"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
