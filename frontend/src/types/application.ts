export interface Tag {
  id: number;
  name: string;
  color: string;
}

export interface Application {
  id: number;
  company: string;
  role: string;
  status: string;
  job_type: string;
  priority: string;
  applied_date: string | null;
  deadline: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  location: string;
  is_remote: boolean;
  url: string;
  source: string;
  notes: string;
  tags: Tag[];
  ai_fit_score: number | null;
  follow_up_date: string | null;
  recruiter_name: string;
  recruiter_email: string;
  activity_count?: number;
  created_at: string;
  updated_at: string;
}

export interface ApplicationActivity {
  id: number;
  event_type: string;
  old_value: string;
  new_value: string;
  timestamp: string;
}

export interface ApplicationFilters {
  status?: string;
  job_type?: string;
  priority?: string;
  source?: string;
  is_remote?: boolean;
  search?: string;
  ordering?: string;
  page?: number;
}

export interface CreateApplicationData {
  company: string;
  role: string;
  job_type: string;
  status?: string;
  priority?: string;
  applied_date?: string | null;
  deadline?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  salary_currency?: string;
  location?: string;
  is_remote?: boolean;
  url?: string;
  source?: string;
  notes?: string;
  follow_up_date?: string | null;
  recruiter_name?: string;
  recruiter_email?: string;
  tag_ids?: number[];
}
