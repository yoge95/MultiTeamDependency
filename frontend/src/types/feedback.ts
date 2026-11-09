// Feedback types for frontend

export interface CitationFeedbackItem {
  citation_id: string;
  issue_type: string;
  comment?: string;
}

export interface FeedbackSubmissionRequest {
  answer_id: string;
  feedback_type: 'helpful' | 'incomplete' | 'stale' | 'unclear' | 'incorrect' | 'other';
  feedback_text?: string;
  citation_feedback?: CitationFeedbackItem[];
}

export interface FeedbackSubmissionResponse {
  feedback_id: string;
  answer_id: string;
  feedback_type: string;
  triage_status: string;
  created_at: string;
  message: string;
}

export type FeedbackRating = 'poor' | 'fair' | 'good' | 'great' | 'excellent';

export interface FeedbackIssue {
  id: string;
  label: string;
  feedbackType: 'incomplete' | 'stale' | 'unclear' | 'incorrect' | 'other';
}
