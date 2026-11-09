import { useState } from 'react';
import { FeedbackRating, FeedbackSubmissionRequest } from '../types/feedback';
import { submitFeedback } from '../services/api';

interface FeedbackFormProps {
  answerId: string;
  questionText: string;
  onSuccess?: () => void;
  onCancel?: () => void;
}

const RATING_OPTIONS: Array<{ value: FeedbackRating; emoji: string; label: string }> = [
  { value: 'poor', emoji: '😞', label: 'Poor' },
  { value: 'fair', emoji: '😐', label: 'Fair' },
  { value: 'good', emoji: '🙂', label: 'Good' },
  { value: 'great', emoji: '😊', label: 'Great' },
  { value: 'excellent', emoji: '🤩', label: 'Excellent' },
];

const IMPROVEMENT_OPTIONS = [
  { id: 'incomplete', label: 'Answer was incomplete or missing information' },
  { id: 'inaccurate', label: 'Answer was inaccurate or outdated' },
  { id: 'citations', label: 'Citations were missing or unclear' },
  { id: 'technical', label: 'Answer was too technical or hard to understand' },
  { id: 'slow', label: 'Took too long to get an answer' },
];

export function FeedbackForm({ answerId, questionText, onSuccess, onCancel }: FeedbackFormProps) {
  const [selectedRating, setSelectedRating] = useState<FeedbackRating | null>(null);
  const [selectedIssues, setSelectedIssues] = useState<Set<string>>(new Set());
  const [comments, setComments] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleIssueToggle = (issueId: string) => {
    const newIssues = new Set(selectedIssues);
    if (newIssues.has(issueId)) {
      newIssues.delete(issueId);
    } else {
      newIssues.add(issueId);
    }
    setSelectedIssues(newIssues);
  };

  const mapRatingToFeedbackType = (rating: FeedbackRating | null) => {
    if (!rating) return 'other';
    if (rating === 'excellent' || rating === 'great') return 'helpful';
    if (rating === 'poor' || rating === 'fair') {
      // Map selected issues to feedback type
      if (selectedIssues.has('incomplete')) return 'incomplete';
      if (selectedIssues.has('inaccurate')) return 'incorrect';
      if (selectedIssues.has('citations')) return 'unclear';
      if (selectedIssues.has('technical')) return 'unclear';
      return 'other';
    }
    return 'other';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedRating) {
      setError('Please select a rating');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const request: FeedbackSubmissionRequest = {
        answer_id: answerId,
        feedback_type: mapRatingToFeedbackType(selectedRating),
        feedback_text: comments || undefined,
      };

      await submitFeedback(request);
      
      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      setError(err.message || 'Failed to submit feedback');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8 max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-purple-500 to-purple-700 rounded-2xl mb-4">
          <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Share Your Feedback</h1>
        <p className="text-gray-600">Help us improve the quality of our answers</p>
      </div>

      <div className="bg-gray-50 rounded-lg p-4 mb-6">
        <div className="text-sm font-semibold text-gray-600 mb-1">Your Question</div>
        <div className="text-gray-900">{questionText}</div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="mb-6">
          <label className="block text-sm font-semibold text-gray-900 mb-3">
            How helpful was this answer?
          </label>
          <div className="flex gap-3 justify-center">
            {RATING_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setSelectedRating(option.value)}
                className={`w-14 h-14 flex flex-col items-center justify-center gap-1 border-2 rounded-xl transition-all ${
                  selectedRating === option.value
                    ? 'border-purple-500 bg-purple-50'
                    : 'border-gray-200 bg-white hover:border-purple-300 hover:bg-gray-50'
                }`}
              >
                <span className="text-2xl">{option.emoji}</span>
                <span className="text-xs text-gray-600 font-medium">{option.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-semibold text-gray-900 mb-3">
            What could be improved? (Select all that apply)
          </label>
          <div className="space-y-3">
            {IMPROVEMENT_OPTIONS.map((option) => (
              <label
                key={option.id}
                className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors"
              >
                <input
                  type="checkbox"
                  checked={selectedIssues.has(option.id)}
                  onChange={() => handleIssueToggle(option.id)}
                  className="w-5 h-5 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                />
                <span className="text-gray-900">{option.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-semibold text-gray-900 mb-3">
            Additional Comments (Optional)
          </label>
          <textarea
            value={comments}
            onChange={(e) => setComments(e.target.value.slice(0, 500))}
            placeholder="Tell us more about your experience or suggest improvements..."
            maxLength={500}
            className="w-full min-h-[120px] p-3 text-gray-900 border-2 border-gray-200 rounded-lg resize-y focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-100 transition-all"
          />
          <div className="text-right text-sm text-gray-500 mt-1">
            {comments.length} / 500
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        <div className="flex gap-3 justify-end pt-6 border-t border-gray-200">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-5 py-2.5 text-gray-700 font-semibold border-2 border-gray-200 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={isSubmitting || !selectedRating}
            className="px-6 py-2.5 text-white font-semibold bg-gradient-to-r from-purple-500 to-purple-700 rounded-lg hover:shadow-lg hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center gap-2"
          >
            <span>Submit Feedback</span>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
}
