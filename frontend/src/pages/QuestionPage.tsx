import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import type { QuestionSubmissionResponse, ClarificationOption } from '../types/questions';

/**
 * Question input page matching wireframe_question_entry_main.html
 */
export function QuestionPage(): React.ReactElement {
  const navigate = useNavigate();
  const [questionText, setQuestionText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [clarificationResponse, setClarificationResponse] = useState<QuestionSubmissionResponse | null>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [refinedQuestion, setRefinedQuestion] = useState('');

  const maxLength = 2000;
  const charCount = questionText.length;

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    
    if (!questionText.trim()) {
      setError('Please enter a question');
      return;
    }

    if (questionText.length > maxLength) {
      setError(`Question must be ${maxLength} characters or less`);
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await api.submitQuestion({ question_text: questionText.trim() });

      if (response.status === 'clarification_needed' && response.clarification_prompt) {
        setClarificationResponse(response);
      } else if (response.status === 'completed' && response.answer_id) {
        navigate(`/answer/${response.answer_id}`, { state: { questionText } });
      } else if (response.status === 'processing') {
        // Poll for completion or navigate to status page
        navigate(`/answer/${response.question_id}`, { state: { questionText, processing: true } });
      } else if (response.status === 'error') {
        setError(response.error_message || 'An error occurred while processing your question');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit question');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClarificationSubmit = async (): Promise<void> => {
    if (!selectedOption && !refinedQuestion.trim()) {
      setError('Please select an option or provide a refined question');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const finalQuestion = refinedQuestion.trim() || questionText.trim();
      const response = await api.submitQuestion({
        question_text: finalQuestion,
        session_id: clarificationResponse?.session_id,
        context_hints: selectedOption ? { selected_interpretation: selectedOption } : undefined,
      });

      if (response.status === 'completed' && response.answer_id) {
        navigate(`/answer/${response.answer_id}`, { state: { questionText: finalQuestion } });
      } else if (response.status === 'processing') {
        navigate(`/answer/${response.question_id}`, { state: { questionText: finalQuestion, processing: true } });
      } else if (response.status === 'error') {
        setError(response.error_message || 'An error occurred');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit clarification');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (clarificationResponse?.clarification_prompt) {
    const prompt = clarificationResponse.clarification_prompt;
    
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-purple-700 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <span className="text-lg font-bold text-gray-900">Knowledge Assistant</span>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-4xl mx-auto px-6 py-8">
          <div className="bg-white rounded-xl p-6 mb-6 border border-gray-200">
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Your Question</div>
            <div className="text-lg font-semibold text-gray-900">{questionText}</div>
          </div>

          <div className="bg-white rounded-2xl shadow-lg p-8">
            <div className="flex items-center gap-4 mb-6 pb-6 border-b border-gray-200">
              <div className="w-14 h-14 bg-yellow-100 rounded-xl flex items-center justify-center">
                <svg className="w-7 h-7 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-bold text-gray-900 mb-1">Multiple Interpretations Found</h2>
                <p className="text-sm text-gray-600">Your question could mean different things</p>
              </div>
            </div>

            <div className="bg-yellow-50 border-l-4 border-yellow-400 rounded-lg p-5 mb-6">
              <p className="text-sm text-yellow-800 leading-relaxed">{prompt.prompt_text}</p>
            </div>

            {error && (
              <div className="bg-red-50 border-l-4 border-red-400 rounded-lg p-4 mb-6">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            <div className="mb-6">
              <h3 className="text-base font-semibold text-gray-900 mb-4">Select the best match:</h3>
              <div className="space-y-3">
                {prompt.options.map((option: ClarificationOption) => (
                  <div
                    key={option.option_id}
                    className={`bg-gray-50 border-2 rounded-xl p-5 cursor-pointer transition-all ${
                      selectedOption === option.option_id
                        ? 'border-purple-600 bg-purple-50'
                        : 'border-gray-200 hover:border-purple-400 hover:bg-white hover:shadow-md'
                    }`}
                    onClick={() => setSelectedOption(option.option_id)}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 mt-1">
                        <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                          selectedOption === option.option_id ? 'border-purple-600' : 'border-gray-400'
                        }`}>
                          {selectedOption === option.option_id && (
                            <div className="w-2.5 h-2.5 bg-purple-600 rounded-full" />
                          )}
                        </div>
                      </div>
                      <div className="flex-1">
                        <div className="text-sm font-semibold text-gray-900 mb-1">{option.option_text}</div>
                        <p className="text-sm text-gray-600">{option.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-900 mb-2">
                Or refine your question (Optional)
              </label>
              <input
                type="text"
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-purple-600 focus:ring-3 focus:ring-purple-100 transition"
                placeholder="Example: I'm asking about the payment API deployment to staging environment"
                value={refinedQuestion}
                onChange={(e) => setRefinedQuestion(e.target.value)}
              />
            </div>

            <div className="flex justify-end gap-3 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={() => {
                  setClarificationResponse(null);
                  setSelectedOption(null);
                  setRefinedQuestion('');
                  setError(null);
                }}
                className="px-5 py-3 text-sm font-semibold text-gray-700 bg-white border-2 border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleClarificationSubmit}
                disabled={isSubmitting}
                className="px-6 py-3 text-sm font-semibold text-white bg-gradient-to-r from-purple-600 to-purple-700 rounded-lg hover:from-purple-700 hover:to-purple-800 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <span>Continue with Selection</span>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                  </>
                )}
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-purple-700 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <span className="text-lg font-bold text-gray-900">Knowledge Assistant</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-3">What can I help you find?</h1>
          <p className="text-lg text-gray-600">Ask about team ownership, dependencies, contacts, or processes</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-lg p-8 mb-8">
          <label className="block text-sm font-semibold text-gray-900 mb-3">Your Question</label>
          <textarea
            className="w-full min-h-[120px] px-4 py-3 text-base border-2 border-gray-200 rounded-xl resize-y focus:outline-none focus:border-purple-600 focus:ring-3 focus:ring-purple-100 transition placeholder-gray-400"
            placeholder="Example: Who owns the payment service? Which teams should I contact before deploying to production?"
            value={questionText}
            onChange={(e) => setQuestionText(e.target.value)}
            maxLength={maxLength}
          />
          <div className="flex items-center justify-between mt-4">
            <span className={`text-sm ${charCount > maxLength * 0.9 ? 'text-red-600' : 'text-gray-500'}`}>
              {charCount} / {maxLength}
            </span>
            <button
              type="submit"
              disabled={isSubmitting || !questionText.trim()}
              className="px-8 py-3.5 text-base font-semibold text-white bg-gradient-to-r from-purple-600 to-purple-700 rounded-lg hover:from-purple-700 hover:to-purple-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:shadow-lg flex items-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <span>Ask Question</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </>
              )}
            </button>
          </div>

          {error && (
            <div className="mt-4 bg-red-50 border-l-4 border-red-400 rounded-lg p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}
        </form>

        {/* Popular Questions */}
        <div className="mb-12">
          <h2 className="text-lg font-semibold text-gray-900 mb-5">Popular Questions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div
              className="bg-white border-2 border-gray-200 rounded-xl p-5 cursor-pointer transition-all hover:border-purple-600 hover:shadow-lg hover:-translate-y-0.5"
              onClick={() => setQuestionText('Who owns the payment service?')}
            >
              <div className="w-10 h-10 bg-gray-50 rounded-lg flex items-center justify-center mb-3 text-purple-600">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <div className="text-sm font-semibold text-gray-900 mb-1">Team Ownership</div>
              <p className="text-sm text-gray-600">Find out which team owns a service or platform</p>
            </div>
            <div
              className="bg-white border-2 border-gray-200 rounded-xl p-5 cursor-pointer transition-all hover:border-purple-600 hover:shadow-lg hover:-translate-y-0.5"
              onClick={() => setQuestionText('What are the dependencies for the payment API?')}
            >
              <div className="w-10 h-10 bg-gray-50 rounded-lg flex items-center justify-center mb-3 text-purple-600">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16l2.879-2.879m0 0a3 3 0 104.243-4.242 3 3 0 00-4.243 4.242zM21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="text-sm font-semibold text-gray-900 mb-1">Dependencies</div>
              <p className="text-sm text-gray-600">Discover upstream and downstream service dependencies</p>
            </div>
            <div
              className="bg-white border-2 border-gray-200 rounded-xl p-5 cursor-pointer transition-all hover:border-purple-600 hover:shadow-lg hover:-translate-y-0.5"
              onClick={() => setQuestionText('Where can I find the deployment runbook?')}
            >
              <div className="w-10 h-10 bg-gray-50 rounded-lg flex items-center justify-center mb-3 text-purple-600">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <div className="text-sm font-semibold text-gray-900 mb-1">Runbooks</div>
              <p className="text-sm text-gray-600">Access operational guides and escalation procedures</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
