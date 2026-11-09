import sharedConfig from '../../../shared_config.json' with { type: 'json' };
import type { LoginRequest, LoginResponse } from '../types/auth';
import type { QuestionSubmissionRequest, QuestionSubmissionResponse, QuestionStatusResponse } from '../types/questions';
import type { AnswerResponse, CitationDetail } from '../types/answers';
import type { FeedbackSubmissionRequest, FeedbackSubmissionResponse } from '../types/feedback';

const baseUrl = import.meta.env.VITE_API_URL || `http://localhost:${sharedConfig.ports.backend}`;

/**
 * Generic request helper that handles authentication, errors, and redirects
 */
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem(sharedConfig.auth.storage_key);
  const headers = new Headers(options.headers);
  
  // Attach Bearer token if available
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  // Set Content-Type for JSON payloads
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const url = `${baseUrl}${sharedConfig.api_base_path}${path}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle 401 Unauthorized - clear token and redirect to login
    if (response.status === 401) {
      localStorage.removeItem(sharedConfig.auth.storage_key);
      localStorage.removeItem('user');
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }

    // Handle other error responses
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || `Request failed with status ${response.status}`);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return null as T;
    }

    return response.json() as Promise<T>;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('An unexpected error occurred');
  }
}

/**
 * API client with typed methods
 */
export const api = {
  /**
   * Login with email and password
   */
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    return request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  },

  /**
   * Health check endpoint (unauthenticated)
   */
  health: async (): Promise<{ status: string }> => {
    const response = await fetch(`${baseUrl}${sharedConfig.api_base_path}/health`);
    if (!response.ok) {
      throw new Error('Health check failed');
    }
    return response.json();
  },

  /**
   * Submit a question
   */
  submitQuestion: async (questionRequest: QuestionSubmissionRequest): Promise<QuestionSubmissionResponse> => {
    return request<QuestionSubmissionResponse>('/questions', {
      method: 'POST',
      body: JSON.stringify(questionRequest),
    });
  },

  /**
   * Get question status
   */
  getQuestionStatus: async (questionId: string): Promise<QuestionStatusResponse> => {
    return request<QuestionStatusResponse>(`/questions/${questionId}`);
  },

  /**
   * Get answer by ID
   */
  getAnswer: async (answerId: string): Promise<AnswerResponse> => {
    return request<AnswerResponse>(`/answers/${answerId}`);
  },

  /**
   * Get citation details
   */
  getCitation: async (citationId: string): Promise<CitationDetail> => {
    return request<CitationDetail>(`/citations/${citationId}`);
  },

  /**
   * Submit feedback for an answer
   */
  submitFeedback: async (feedbackRequest: FeedbackSubmissionRequest): Promise<FeedbackSubmissionResponse> => {
    return request<FeedbackSubmissionResponse>('/feedback', {
      method: 'POST',
      body: JSON.stringify(feedbackRequest),
    });
  },
};

export { request };

// Export individual functions for convenience
export const { login, health, submitQuestion, getQuestionStatus, getAnswer, getCitation, submitFeedback } = api;
