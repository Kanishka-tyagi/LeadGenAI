export type LeadStatus =
  | "new"
  | "scored"
  | "reviewed"
  | "contacted"
  | "converted"
  | "rejected";

export interface SubScores {
  has_website: boolean;
  mobile_responsive?: boolean | null;
  broken_links_count?: number | null;
  outdated_tech_flags: string[];
  load_time_ms?: number | null;
  reviews_count?: number | null;
  rating?: number | null;
}

export interface LLMOutput {
  website_score: number;
  digital_presence: number;
  overall_lead_score: number;
  reasoning: string;
  recommended_pitch: string;
  drafted_email_subject: string;
  drafted_email_body: string;
}

export interface Lead {
  id: string;
  business_name: string;
  category?: string | null;
  address?: string | null;
  phone?: string | null;
  website_url?: string | null;
  status: LeadStatus;
  sub_scores?: SubScores | null;
  llm_output?: LLMOutput | null;
  overridden_score?: number | null;
  edited_email_subject?: string | null;
  edited_email_body?: string | null;
  reviewer_notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface LeadListResponse {
  items: Lead[];
  total: number;
  page: number;
  page_size: number;
}

export function effectiveScore(lead: Lead): number {
  return lead.overridden_score ?? lead.llm_output?.overall_lead_score ?? 0;
}

export function fetchWithAuth(
  url: string,
  options: RequestInit & { token?: string } = {}
) {
  const { token, ...opts } = options;
  const headers = new Headers(opts.headers || {});
  
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  
  return fetch(url, { ...opts, headers });
}