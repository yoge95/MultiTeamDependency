/**
 * Answer and citation types
 */

export interface CitationSummary {
  citation_id: string;
  claim_text: string;
  source_title: string;
  section_path: string;
  freshness_status: 'current' | 'stale' | 'exception_granted';
  last_reviewed_at?: string;
}

export interface ConfidenceScore {
  overall_score: number;
  confidence_band: 'high' | 'medium' | 'low' | 'insufficient';
  dimensions: {
    evidence_quality: number;
    freshness: number;
    consistency: number;
    citation_coverage: number;
  };
  flags: string[];
  explanation?: string;
}

export interface LimitationMessage {
  type: 'low_confidence' | 'stale_warning' | 'conflicting_evidence' | 'restricted_scope' | 'missing_knowledge';
  severity: 'info' | 'warning' | 'error';
  message: string;
  details?: string;
}

export interface EscalationContact {
  contact_type: 'team_lead' | 'domain_steward' | 'platform_admin' | 'general';
  name: string;
  contact_method: 'email' | 'slack' | 'team_channel';
  contact_address: string;
}

export interface AnswerResponse {
  answer_id: string;
  question_id: string;
  session_id: string;
  answer_text: string;
  answer_type: 'grounded' | 'low_confidence' | 'clarification_needed' | 'escalation_required' | 'restricted_scope' | 'stale_warning' | 'conflicting_evidence' | 'missing_knowledge';
  citations: CitationSummary[];
  confidence_score: ConfidenceScore;
  limitations: LimitationMessage[];
  freshness_warnings: Array<{
    source_title: string;
    last_reviewed_at: string;
    days_since_review: number;
  }>;
  escalation_contacts: EscalationContact[];
  created_at: string;
}

export interface CitationDetail {
  citation_id: string;
  claim_text: string;
  source_record_id: string;
  source_title: string;
  section_path: string;
  evidence_text: string;
  chunk_id: string;
  freshness_status: 'current' | 'stale' | 'exception_granted';
  last_reviewed_at?: string;
  approval_state: string;
  source_context?: {
    domain_name: string;
    source_type: string;
    owning_team?: string;
  };
}
