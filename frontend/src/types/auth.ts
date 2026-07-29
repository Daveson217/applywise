export interface UserProfile {
  phone: string;
  graduation_date: string | null;
  university: string;
  target_roles: string[];
  excluded_keywords: string[];
  target_job_types: string[];
  preferred_locations: string[];
  linkedin_url: string;
  github_url: string;
  website_url: string;
  bio: string;
  weekly_goal: number;
  theme: "light" | "dark" | "system";
  accent_color: string;
  default_llm_provider: string;
  default_llm_model: string;
  onboarding_completed: boolean;
  ai_relevance_enabled: boolean;
}

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_email_verified: boolean;
  date_joined: string;
  profile: UserProfile;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
}

export interface RegisterResponse {
  user: User;
  tokens: TokenPair;
}
