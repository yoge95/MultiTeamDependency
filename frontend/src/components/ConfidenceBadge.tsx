import React, { useState } from 'react';
import type { ConfidenceScore } from '../types/answers';

interface ConfidenceBadgeProps {
  confidenceScore: ConfidenceScore;
}

/**
 * Confidence badge with color coding and tooltip explanation
 */
export function ConfidenceBadge({ confidenceScore }: ConfidenceBadgeProps): React.ReactElement {
  const [showTooltip, setShowTooltip] = useState(false);

  const getBadgeStyles = (band: string): string => {
    switch (band) {
      case 'high':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'insufficient':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getBadgeText = (band: string): string => {
    switch (band) {
      case 'high':
        return 'High Confidence';
      case 'medium':
        return 'Medium Confidence';
      case 'low':
        return 'Low Confidence';
      case 'insufficient':
        return 'Insufficient Evidence';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="relative inline-block">
      <div
        className={`px-3 py-1.5 rounded-md border font-semibold text-sm cursor-help ${getBadgeStyles(confidenceScore.confidence_band)}`}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        {getBadgeText(confidenceScore.confidence_band)}
      </div>

      {showTooltip && (
        <div className="absolute z-50 top-full mt-2 right-0 w-80 bg-white border border-gray-200 rounded-lg shadow-xl p-4">
          <div className="mb-3">
            <div className="text-sm font-semibold text-gray-900 mb-1">
              Overall Score: {(confidenceScore.overall_score * 100).toFixed(0)}%
            </div>
            {confidenceScore.explanation && (
              <p className="text-xs text-gray-600">{confidenceScore.explanation}</p>
            )}
          </div>

          <div className="space-y-2">
            <div className="text-xs font-semibold text-gray-700 mb-2">Score Breakdown:</div>
            
            <div>
              <div className="flex justify-between text-xs text-gray-600 mb-1">
                <span>Evidence Quality</span>
                <span className="font-medium">{(confidenceScore.dimensions.evidence_quality * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div
                  className="bg-purple-600 h-1.5 rounded-full"
                  style={{ width: `${confidenceScore.dimensions.evidence_quality * 100}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs text-gray-600 mb-1">
                <span>Freshness</span>
                <span className="font-medium">{(confidenceScore.dimensions.freshness * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div
                  className="bg-purple-600 h-1.5 rounded-full"
                  style={{ width: `${confidenceScore.dimensions.freshness * 100}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs text-gray-600 mb-1">
                <span>Consistency</span>
                <span className="font-medium">{(confidenceScore.dimensions.consistency * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div
                  className="bg-purple-600 h-1.5 rounded-full"
                  style={{ width: `${confidenceScore.dimensions.consistency * 100}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs text-gray-600 mb-1">
                <span>Citation Coverage</span>
                <span className="font-medium">{(confidenceScore.dimensions.citation_coverage * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div
                  className="bg-purple-600 h-1.5 rounded-full"
                  style={{ width: `${confidenceScore.dimensions.citation_coverage * 100}%` }}
                />
              </div>
            </div>
          </div>

          {confidenceScore.flags.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <div className="text-xs font-semibold text-gray-700 mb-1">Flags:</div>
              <div className="flex flex-wrap gap-1">
                {confidenceScore.flags.map((flag, idx) => (
                  <span key={idx} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-700 rounded">
                    {flag.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
