export type VerificationStatus =
  "VERIFIED" | "REVIEW_REQUIRED" | "SOURCE_UNAVAILABLE" | "ERROR";
export type ReviewStatus = "PENDING" | "APPROVED" | "REJECTED" | "NOT_REQUIRED";
export interface Lender {
  id: number;
  name: string;
  country: string;
  lender_type: string;
  description: string;
  website_url: string | null;
  alehar_url: string | null;
  retrieved_at: string | null;
  source_notes: string | null;
  verification_source_url: string | null;
  source_type: string;
  is_demo: boolean;
  active: boolean;
  last_verified_at: string | null;
}
export interface AIAnalysis {
  identity_match: boolean | null;
  possible_mismatch: boolean;
  review_recommended: boolean;
  reason: string | null;
  supported_findings: string[];
  uncertain_findings: string[];
}
export interface SourceIntelligence {
  company_name: string | null;
  company_description: string | null;
  entity_type: string | null;
  products_or_services: string[];
  geographies: string[];
  identity_evidence: string[];
  uncertain_fields: string[];
  source_summary: string | null;
}
export interface Verification {
  id: number;
  lender_id: number;
  lender_name?: string;
  status: VerificationStatus;
  confidence_score: number;
  source_url: string | null;
  source_http_status: number | null;
  source_reachable: boolean;
  checked_at: string;
  error_message: string | null;
  detected_changes: { type: string; message: string }[];
  evidence: Record<string, unknown>;
  ai_enabled: boolean;
  ai_status: string;
  ai_provider: string | null;
  ai_model: string | null;
  ai_analysis: AIAnalysis | null;
  ai_extracted_data: SourceIntelligence | null;
  ai_error: string | null;
  review_status: ReviewStatus;
  review_note: string | null;
  reviewed_at: string | null;
}
export interface Summary {
  total_lenders: number;
  verified: number;
  review_required: number;
  source_unavailable: number;
  errors: number;
  unverified: number;
  pending_reviews: number;
  approved_reviews: number;
  rejected_reviews: number;
  last_verification_time: string | null;
}
export interface BatchSummary {
  total: number;
  verified: number;
  review_required: number;
  source_unavailable: number;
  errors: number;
}
export interface SystemStatus {
  public_demo_mode: boolean;
  public_demo_snapshot: boolean;
  backend_status: string;
  database_status: string;
  ai_enabled: boolean;
  ai_provider: string;
  ai_model: string | null;
  ai_status: string;
  ai_message: string;
  scheduler_enabled: boolean;
  verification_interval_hours: number;
  next_scheduled_run: string | null;
  verification_running: boolean;
}
