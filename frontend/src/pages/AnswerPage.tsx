import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import type { AnswerResponse } from '../types/answers';
import { CitationPanel } from '../components/CitationPanel';
import { ConfidenceBadge } from '../components/ConfidenceBadge';
import { FreshnessWarning } from '../components/FreshnessWarning';
import { LimitationMessage } from '../components/LimitationMessage';
import { formatDateTime } from '../lib/utils';

/**
 * Answer display page matching wireframe designs
 */
export function AnswerPage(): React.ReactElement {
  const { answerId } = useParams<{ answerId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  
  const [answer, setAnswer] = useState<AnswerResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [highlightedCitation, setHighlightedCitation] = useState<string | null>(null);
  const [followUpQuestion, setFollowUpQuestion] = useState('');
  const [submittingFollowUp, setSubmittingFollowUp] = useState(false);

  const questionText = location.state?.questionText || 'Your question';

  useEffect(() => {
    if (!answerId) {
      setError('No answer ID provided');
      setLoading(false);
      return;
    }

    const fetchAnswer = async (): Promise<void> => {
      try {
        setLoading(true);
        const data = await api.getAnswer(answerId);
        setAnswer(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load answer');
      } finally {
        setLoading(false);
      }
    };

    fetchAnswer();
  }, [answerId]);

  const handleFollowUpSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    
    if (!followUpQuestion.trim() || !answer) {
      return;
    }

    setSubmittingFollowUp(true);
    try {
      const response = await api.submitQuestion({
        question_text: followUpQuestion.trim(),
        session_id: answer.session_id,
      });

      if (response.status === 'completed' && response.answer_id) {
        navigate(`/answer/${response.answer_id}`, { state: { questionText: followUpQuestion } });
      } else if (response.status === 'clarification_needed') {
        navigate('/question', { state: { clarificationResponse: response } });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit follow-up question');
    } finally {
      setSubmittingFollowUp(false);
    }
  };

  const renderAnswerContent = (text: string): React.ReactElement => {
    // Split answer text and insert citation markers
    // For now, render as-is; citation markers would be inserted by backend
    const paragraphs = text.split('\n\n');
    
    return (
      <div className="space-y-4">
        {paragraphs.map((paragraph, idx) => {
          if (paragraph.trim().startsWith('**') && paragraph.includes(':')) {
            // Bold heading
            return (
              <p key={idx} className="text-base text-gray-900 leading-relaxed">
                <strong>{paragraph.replace(/\*\*/g, '')}</strong>
              </p>
            );
          }
          
          return (
            <p key={idx} className="text-base text-gray-800 leading-relaxed">
              {paragraph}
            </p>
          );
        })}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-purple-600 to-purple-700 rounded-2xl flex items-center justify-center mx-auto mb-4 animate-pulse">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <p className="text-lg font-medium text-gray-900">Loading answer...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 text-center">
          <div className="w-16 h-16 bg-red-100 rounded-xl flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Unable to Load Answer</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => navigate('/question')}
            className="px-6 py-3 text-white bg-gradient-to-r from-purple-600 to-purple-700 rounded-lg font-semibold hover:from-purple-700 hover:to-purple-800 transition"
          >
            Ask Another Question
          </button>
        </div>
      </div>
    );
  }

  if (!answer) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">No answer data available</p>
      </div>
    );
  }

  const isLowConfidence = answer.confidence_score.confidence_band === 'low' || answer.confidence_score.confidence_band === 'insufficient';

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
        {/* Question Display */}
        <div className="bg-white rounded-xl p-6 mb-6 border border-gray-200">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Your Question</div>
          <div className="text-lg font-semibold text-gray-900">{questionText}</div>
        </div>

        {/* Answer Card */}
        <div className={`bg-white rounded-2xl shadow-xl p-8 mb-6 ${isLowConfidence ? 'border-2 border-yellow-400' : ''}`}>
          {/* Answer Header */}
          <div className="flex items-center gap-4 mb-5 pb-5 border-b border-gray-200">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              isLowConfidence ? 'bg-yellow-100' : 'bg-gradient-to-br from-purple-600 to-purple-700'
            }`}>
              <svg className={`w-6 h-6 ${isLowConfidence ? 'text-yellow-600' : 'text-white'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {isLowConfidence ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                )}
              </svg>
            </div>
            <div className="flex-1">
              <h2 className="text-base font-semibold text-gray-900 mb-1">
                {isLowConfidence ? 'Partial Answer Available' : 'Answer'}
              </h2>
              <p className="text-sm text-gray-500">Generated {formatDateTime(answer.created_at)}</p>
            </div>
            <ConfidenceBadge confidenceScore={answer.confidence_score} />
          </div>

          {/* Low Confidence Warning */}
          {isLowConfidence && (
            <div className="bg-yellow-50 border-l-4 border-yellow-400 rounded-lg p-5 mb-6">
              <p className="text-sm text-yellow-800 font-semibold mb-2">
                <strong>I found some information, but it may not be complete.</strong>
              </p>
              <p className="text-sm text-yellow-800">
                The available documentation has limitations that affect the completeness of this answer. 
                Please review the limitations below and consider contacting the team directly for the most current information.
              </p>
            </div>
          )}

          {/* Limitations */}
          {answer.limitations.length > 0 && (
            <div className="mb-6">
              <LimitationMessage limitations={answer.limitations} />
            </div>
          )}

          {/* Answer Content */}
          <div className="mb-6">
            {renderAnswerContent(answer.answer_text)}
          </div>

          {/* Freshness Warnings */}
          {answer.freshness_warnings.length > 0 && (
            <div className="mb-6 space-y-3">
              {answer.freshness_warnings.map((warning, idx) => (
                <FreshnessWarning
                  key={idx}
                  sourceTitle={warning.source_title}
                  lastReviewedAt={warning.last_reviewed_at}
                  daysSinceReview={warning.days_since_review}
                />
              ))}
            </div>
          )}

          {/* Citations */}
          {answer.citations.length > 0 && (
            <div className="mb-6">
              <CitationPanel
                citations={answer.citations}
                highlightedCitationId={highlightedCitation || undefined}
                onCitationClick={setHighlightedCitation}
              />
            </div>
          )}

          {/* Escalation Contacts */}
          {answer.escalation_contacts.length > 0 && (
            <div className="bg-blue-50 border-l-4 border-blue-400 rounded-lg p-5 mb-6">
              <h3 className="text-sm font-semibold text-blue-900 mb-3 flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Need More Help?
              </h3>
              <p className="text-sm text-blue-800 mb-3">For the most current information, contact:</p>
              <div className="space-y-2">
                {answer.escalation_contacts.map((contact, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm text-blue-900">
                    <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    <strong>{contact.name}</strong>
                    {contact.contact_method === 'email' ? (
                      <a href={`mailto:${contact.contact_address}`} className="text-blue-700 hover:underline">
                        {contact.contact_address}
                      </a>
                    ) : (
                      <span>{contact.contact_address}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Bar */}
          <div className="flex gap-3 pt-6 border-t border-gray-200">
            <button className="px-5 py-3 text-sm font-semibold text-gray-700 bg-white border-2 border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
              </svg>
              Helpful
            </button>
            <button className="px-5 py-3 text-sm font-semibold text-gray-700 bg-white border-2 border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
              </svg>
              Not Helpful
            </button>
            <button className="px-5 py-3 text-sm font-semibold text-gray-700 bg-white border-2 border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
              </svg>
              Share
            </button>
          </div>
        </div>

        {/* Follow-up Question Section */}
        <div className="bg-white rounded-xl p-6 border border-gray-200">
          <h3 className="text-base font-semibold text-gray-900 mb-3">Ask a Follow-up Question</h3>
          <form onSubmit={handleFollowUpSubmit}>
            <textarea
              className="w-full min-h-[80px] px-4 py-3 text-sm border-2 border-gray-200 rounded-lg resize-y focus:outline-none focus:border-purple-600 focus:ring-3 focus:ring-purple-100 transition placeholder-gray-400"
              placeholder="Example: What is the escalation process for payment issues?"
              value={followUpQuestion}
              onChange={(e) => setFollowUpQuestion(e.target.value)}
            />
            <div className="flex justify-end mt-3">
              <button
                type="submit"
                disabled={submittingFollowUp || !followUpQuestion.trim()}
                className="px-6 py-3 text-sm font-semibold text-white bg-gradient-to-r from-purple-600 to-purple-700 rounded-lg hover:from-purple-700 hover:to-purple-800 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center gap-2"
              >
                {submittingFollowUp ? (
                  <>
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span>Sending...</span>
                  </>
                ) : (
                  <>
                    <span>Send</span>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
