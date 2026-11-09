import React, { useState } from 'react';
import type { CitationSummary } from '../types/answers';
import { formatDateTime } from '../lib/utils';

interface CitationPanelProps {
  citations: CitationSummary[];
  highlightedCitationId?: string;
  onCitationClick?: (citationId: string) => void;
}

/**
 * Citations panel showing source attributions with freshness indicators
 */
export function CitationPanel({ citations, highlightedCitationId, onCitationClick }: CitationPanelProps): React.ReactElement {
  const [expandedCitations, setExpandedCitations] = useState<Set<string>>(new Set());

  const toggleCitation = (citationId: string): void => {
    const newExpanded = new Set(expandedCitations);
    if (newExpanded.has(citationId)) {
      newExpanded.delete(citationId);
    } else {
      newExpanded.add(citationId);
    }
    setExpandedCitations(newExpanded);
  };

  const getFreshnessIndicator = (status: string): React.ReactElement => {
    switch (status) {
      case 'current':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Current
          </span>
        );
      case 'stale':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs font-medium">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Stale
          </span>
        );
      case 'exception_granted':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0121 12c0 5.523-4.477 10-10 10S1 17.523 1 12 5.477 2 11 2c1.821 0 3.532.482 5.009 1.325" />
            </svg>
            Exception
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs font-medium">
            Unknown
          </span>
        );
    }
  };

  if (citations.length === 0) {
    return (
      <div className="bg-gray-50 rounded-xl p-5 text-center text-gray-500 text-sm">
        No citations available
      </div>
    );
  }

  return (
    <div className="bg-gray-50 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <h3 className="text-base font-semibold text-gray-900">Sources</h3>
        <span className="text-sm text-gray-500">({citations.length} {citations.length === 1 ? 'citation' : 'citations'})</span>
      </div>

      <div className="space-y-3">
        {citations.map((citation, index) => {
          const isExpanded = expandedCitations.has(citation.citation_id);
          const isHighlighted = highlightedCitationId === citation.citation_id;

          return (
            <div
              key={citation.citation_id}
              className={`bg-white border rounded-lg p-4 transition-all cursor-pointer ${
                isHighlighted ? 'border-purple-600 shadow-md' : 'border-gray-200 hover:border-purple-400 hover:shadow-sm'
              }`}
              onClick={() => {
                toggleCitation(citation.citation_id);
                if (onCitationClick) {
                  onCitationClick(citation.citation_id);
                }
              }}
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-6 h-6 bg-purple-600 text-white rounded-full flex items-center justify-center text-sm font-semibold">
                  {index + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h4 className="text-sm font-semibold text-gray-900 leading-tight">
                      {citation.source_title}
                    </h4>
                    {getFreshnessIndicator(citation.freshness_status)}
                  </div>
                  
                  {citation.section_path && (
                    <p className="text-xs text-gray-500 mb-2">
                      {citation.section_path}
                    </p>
                  )}

                  {isExpanded && citation.claim_text && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <p className="text-sm text-gray-700 leading-relaxed">
                        {citation.claim_text}
                      </p>
                    </div>
                  )}

                  {citation.last_reviewed_at && (
                    <div className="flex items-center gap-1 mt-2 text-xs text-gray-500">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>Last reviewed: {formatDateTime(citation.last_reviewed_at)}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
