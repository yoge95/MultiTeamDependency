import React from 'react';
import type { LimitationMessage as LimitationMessageType } from '../types/answers';

interface LimitationMessageProps {
  limitations: LimitationMessageType[];
}

/**
 * Limitation message component for displaying answer limitations
 */
export function LimitationMessage({ limitations }: LimitationMessageProps): React.ReactElement | null {
  if (limitations.length === 0) {
    return null;
  }

  const getIconForType = (type: string): React.ReactElement => {
    switch (type) {
      case 'low_confidence':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        );
      case 'stale_warning':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'conflicting_evidence':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16l2.879-2.879m0 0a3 3 0 104.243-4.242 3 3 0 00-4.243 4.242zM21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'restricted_scope':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        );
      case 'missing_knowledge':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  const getStylesForSeverity = (severity: string): { bg: string; border: string; text: string; icon: string } => {
    switch (severity) {
      case 'error':
        return { bg: 'bg-red-50', border: 'border-red-400', text: 'text-red-800', icon: 'text-red-600' };
      case 'warning':
        return { bg: 'bg-yellow-50', border: 'border-yellow-400', text: 'text-yellow-800', icon: 'text-yellow-600' };
      case 'info':
      default:
        return { bg: 'bg-blue-50', border: 'border-blue-400', text: 'text-blue-800', icon: 'text-blue-600' };
    }
  };

  const getLabelForType = (type: string): string => {
    switch (type) {
      case 'low_confidence':
        return 'Low Confidence';
      case 'stale_warning':
        return 'Stale Information';
      case 'conflicting_evidence':
        return 'Conflicting Evidence';
      case 'restricted_scope':
        return 'Restricted Access';
      case 'missing_knowledge':
        return 'Missing Knowledge';
      default:
        return 'Limitation';
    }
  };

  return (
    <div className="bg-gray-50 rounded-xl p-5 space-y-3">
      <div className="flex items-center gap-2 mb-3">
        <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 className="text-base font-semibold text-gray-900">Known Limitations</h3>
      </div>

      {limitations.map((limitation, index) => {
        const styles = getStylesForSeverity(limitation.severity);
        return (
          <div key={index} className={`${styles.bg} border-l-4 ${styles.border} rounded-lg p-4`}>
            <div className="flex items-start gap-3">
              <div className={`flex-shrink-0 mt-0.5 ${styles.icon}`}>
                {getIconForType(limitation.type)}
              </div>
              <div className="flex-1">
                <div className={`text-sm font-semibold ${styles.text} mb-1`}>
                  {getLabelForType(limitation.type)}
                </div>
                <p className={`text-sm ${styles.text}`}>
                  {limitation.message}
                </p>
                {limitation.details && (
                  <p className={`text-xs ${styles.text} mt-2 opacity-90`}>
                    {limitation.details}
                  </p>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
