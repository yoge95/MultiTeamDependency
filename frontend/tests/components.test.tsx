import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ConfidenceBadge } from '../src/components/ConfidenceBadge';
import { FreshnessWarning } from '../src/components/FreshnessWarning';
import { LimitationMessage } from '../src/components/LimitationMessage';
import { CitationPanel } from '../src/components/CitationPanel';
import type { ConfidenceScore, LimitationMessage as LimitationMessageType, CitationSummary } from '../src/types/answers';

describe('ConfidenceBadge', () => {
  it('renders high confidence badge correctly', () => {
    const score: ConfidenceScore = {
      overall_score: 0.85,
      confidence_band: 'high',
      dimensions: {
        evidence_quality: 0.9,
        freshness: 0.8,
        consistency: 0.85,
        citation_coverage: 0.85,
      },
      flags: [],
    };

    render(<ConfidenceBadge confidenceScore={score} />);
    expect(screen.getByText('High Confidence')).toBeInTheDocument();
  });

  it('renders low confidence badge correctly', () => {
    const score: ConfidenceScore = {
      overall_score: 0.45,
      confidence_band: 'low',
      dimensions: {
        evidence_quality: 0.5,
        freshness: 0.4,
        consistency: 0.45,
        citation_coverage: 0.45,
      },
      flags: ['low_evidence'],
    };

    render(<ConfidenceBadge confidenceScore={score} />);
    expect(screen.getByText('Low Confidence')).toBeInTheDocument();
  });
});

describe('FreshnessWarning', () => {
  it('renders freshness warning with correct information', () => {
    render(
      <FreshnessWarning
        sourceTitle="Test Document"
        lastReviewedAt="2025-11-01T00:00:00Z"
        daysSinceReview={120}
      />
    );

    expect(screen.getByText('Stale Source Warning')).toBeInTheDocument();
    expect(screen.getByText(/Test Document/)).toBeInTheDocument();
    expect(screen.getByText(/120 days ago/)).toBeInTheDocument();
  });
});

describe('LimitationMessage', () => {
  it('renders limitation messages correctly', () => {
    const limitations: LimitationMessageType[] = [
      {
        type: 'low_confidence',
        severity: 'warning',
        message: 'Limited evidence available',
      },
      {
        type: 'stale_warning',
        severity: 'warning',
        message: 'Some sources are outdated',
      },
    ];

    render(<LimitationMessage limitations={limitations} />);
    expect(screen.getByText('Known Limitations')).toBeInTheDocument();
    expect(screen.getByText('Limited evidence available')).toBeInTheDocument();
    expect(screen.getByText('Some sources are outdated')).toBeInTheDocument();
  });

  it('renders nothing when no limitations', () => {
    const { container } = render(<LimitationMessage limitations={[]} />);
    expect(container.firstChild).toBeNull();
  });
});

describe('CitationPanel', () => {
  it('renders citations correctly', () => {
    const citations: CitationSummary[] = [
      {
        citation_id: 'cit-1',
        claim_text: 'Test claim',
        source_title: 'Test Source 1',
        section_path: '/section1',
        freshness_status: 'current',
        last_reviewed_at: '2026-08-01T00:00:00Z',
      },
      {
        citation_id: 'cit-2',
        claim_text: 'Another claim',
        source_title: 'Test Source 2',
        section_path: '/section2',
        freshness_status: 'stale',
        last_reviewed_at: '2025-11-01T00:00:00Z',
      },
    ];

    render(<CitationPanel citations={citations} />);
    expect(screen.getByText('Sources')).toBeInTheDocument();
    expect(screen.getByText('(2 citations)')).toBeInTheDocument();
    expect(screen.getByText('Test Source 1')).toBeInTheDocument();
    expect(screen.getByText('Test Source 2')).toBeInTheDocument();
  });

  it('renders empty state when no citations', () => {
    render(<CitationPanel citations={[]} />);
    expect(screen.getByText('No citations available')).toBeInTheDocument();
  });
});
