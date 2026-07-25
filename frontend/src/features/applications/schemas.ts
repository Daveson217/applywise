import { z } from "zod";

export const applicationSchema = z
  .object({
    company: z.string().min(1, "Company is required"),
    role: z.string().min(1, "Role is required"),
    job_type: z.string().min(1, "Job type is required"),
    status: z.string().default("saved"),
    priority: z.string().default("medium"),
    applied_date: z.string().optional().or(z.literal("")),
    deadline: z.string().optional().or(z.literal("")),
    salary_min: z.coerce.number().optional().or(z.literal("")),
    salary_max: z.coerce.number().optional().or(z.literal("")),
    salary_currency: z.string().default("USD"),
    location: z.string().optional(),
    is_remote: z.boolean().default(false),
    url: z.string().url("Must be a valid URL").or(z.literal("")).optional(),
    source: z.string().optional(),
    notes: z.string().optional(),
    follow_up_date: z.string().optional().or(z.literal("")),
    recruiter_name: z.string().optional(),
    recruiter_email: z
      .string()
      .email("Must be a valid email")
      .or(z.literal(""))
      .optional(),
    tag_ids: z.array(z.number()).optional(),
  })
  .refine(
    (data) => {
      if (
        data.salary_min &&
        data.salary_max &&
        typeof data.salary_min === "number" &&
        typeof data.salary_max === "number"
      ) {
        return data.salary_min <= data.salary_max;
      }
      return true;
    },
    {
      message: "Min salary cannot exceed max salary",
      path: ["salary_min"],
    }
  );

export type ApplicationFormData = z.infer<typeof applicationSchema>;
