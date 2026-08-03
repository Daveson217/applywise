export interface WatchlistRule {
  id: number;
  keywords: string[];
  exclude_keywords: string[];
  locations: string[];
  job_types: string[];
  search_description: boolean;
  is_active: boolean;
}

export interface WatchlistCompany {
  id: number;
  name: string;
  careers_url: string;
  ats_provider: string;
  ats_company_slug: string;
  scrape_status: string;
  last_checked_at: string | null;
  last_error: string;
  rules: WatchlistRule[];
  active_postings_count: number;
  total_postings_count: number;
  created_at: string;
}

export interface JobPosting {
  id: number;
  external_id: string;
  title: string;
  url: string;
  location: string;
  first_seen_at: string;
  last_seen_at: string;
  is_active: boolean;
  is_reposted: boolean;
  matched_rules: boolean;
  ai_relevance_score: number | null;
}

export interface ATSDetectResult {
  detected: boolean;
  provider: string | null;
  slug: string | null;
}

export interface MatchedJob {
  id: number;
  company_id: number;
  company_name: string;
  title: string;
  url: string;
  location: string;
  ai_relevance_score: number | null;
  matched_at: string | null;
  first_seen_at: string;
  match_dismissed: boolean;
}
