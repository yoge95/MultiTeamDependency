/**
 * Question submission and status types
 */

export interface QuestionSubmissionRequest {
  question_text: string;
  session_id?: string;
  context_hints?: Record<string, unknown>;
}

export interface IntentClassification {
  primary_intent: 'ownership' | 'dependency' | 'routing' | 'runbook' | 'onboarding' | 'governance';
  confidence: number;
  secondary_intents?: string[];
  ambiguity_flags?: string[];
}

export interface ClarificationOption {
  option_id: string;
  option_text: string;
  description: string;
  metadata?: Record<string, unknown>;
}

export interface ClarificationPrompt {
  prompt_text: string;
  prompt_type: 'multiple_intents' | 'too_vague' | 'unclear_reference';
  options: ClarificationOption[];
}

export interface QuestionSubmissionResponse {
  question_id: string;
  session_id: string;
  turn_id: string;
  status: 'processing' | 'clarification_needed' | 'completed' | 'error';
  intent_classification?: IntentClassification;
  clarification_prompt?: ClarificationPrompt;
  answer_id?: string;
  error_message?: string;
}

export interface QuestionStatusResponse {
  question_id: string;
  session_id: string;
  turn_id: string;
  status: 'processing' | 'clarification_needed' | 'completed' | 'error';
  intent_classification?: IntentClassification;
  answer_id?: string;
  created_at: string;
  updated_at: string;
}
