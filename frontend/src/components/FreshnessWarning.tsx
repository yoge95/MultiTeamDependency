import React from 'react';

interface FreshnessWarningProps {
  sourceTitle: string;
  lastReviewedAt: string;
  daysSinceReview: number;
}

/**
 * Freshness warning component for stale sources
 */
export function FreshnessWarning({ sourceTitle, lastReviewedAt, daysSinceReview }: FreshnessWarningProps): React.ReactElement {
  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="bg-yellow-50 border-l-4 border-yellow-400 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div className="flex-1">
          <h4 className="text-sm font-semibold text-yellow-800 mb-1">Stale Source Warning</h4>
          <p className="text-sm text-yellow-700">
            <strong>{sourceTitle}</strong> was last reviewed <strong>{formatDate(lastReviewedAt)}</strong> ({daysSinceReview} days ago). 
            This information may be outdated. Please verify with the owning team for the most current details.
          </p>
        </div>
      </div>
    </div>
  );
}
