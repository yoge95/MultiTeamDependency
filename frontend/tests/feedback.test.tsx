import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { FeedbackForm } from '../src/components/FeedbackForm';

// Mock the API
vi.mock('../src/services/api', () => ({
  submitFeedback: vi.fn().mockResolvedValue({
    feedback_id: '123',
    answer_id: '456',
    feedback_type: 'helpful',
    triage_status: 'pending',
    created_at: new Date().toISOString(),
    message: 'Thank you for your feedback!'
  })
}));

describe('FeedbackForm', () => {
  it('renders feedback form with all elements', () => {
    render(
      <FeedbackForm
        answerId="test-answer-id"
        questionText="Test question?"
      />
    );

    expect(screen.getByText('Share Your Feedback')).toBeInTheDocument();
    expect(screen.getByText('Help us improve the quality of our answers')).toBeInTheDocument();
    expect(screen.getByText('Test question?')).toBeInTheDocument();
    expect(screen.getByText('How helpful was this answer?')).toBeInTheDocument();
  });

  it('renders all rating options', () => {
    render(
      <FeedbackForm
        answerId="test-answer-id"
        questionText="Test question?"
      />
    );

    expect(screen.getByText('Poor')).toBeInTheDocument();
    expect(screen.getByText('Fair')).toBeInTheDocument();
    expect(screen.getByText('Good')).toBeInTheDocument();
    expect(screen.getByText('Great')).toBeInTheDocument();
    expect(screen.getByText('Excellent')).toBeInTheDocument();
  });

  it('renders improvement options checkboxes', () => {
    render(
      <FeedbackForm
        answerId="test-answer-id"
        questionText="Test question?"
      />
    );

    expect(screen.getByText('Answer was incomplete or missing information')).toBeInTheDocument();
    expect(screen.getByText('Answer was inaccurate or outdated')).toBeInTheDocument();
    expect(screen.getByText('Citations were missing or unclear')).toBeInTheDocument();
  });

  it('updates character count for comments', () => {
    render(
      <FeedbackForm
        answerId="test-answer-id"
        questionText="Test question?"
      />
    );

    const textarea = screen.getByPlaceholderText(/Tell us more about your experience/i);
    
    fireEvent.change(textarea, { target: { value: 'Test comment' } });

    expect(screen.getByText(/12 \/ 500/)).toBeInTheDocument();
  });

  it('disables submit button when no rating selected', () => {
    render(
      <FeedbackForm
        answerId="test-answer-id"
        questionText="Test question?"
      />
    );

    const submitButton = screen.getByText('Submit Feedback').closest('button');
    expect(submitButton).toBeDisabled();
  });

  it('submits feedback successfully when rating selected', async () => {
    const onSuccess = vi.fn();
    
    render(
      <FeedbackForm
        answerId="test-answer-id"
        questionText="Test question?"
        onSuccess={onSuccess}
      />
    );

    // Select a rating
    const excellentButton = screen.getByText('Excellent').closest('button');
    if (excellentButton) {
      fireEvent.click(excellentButton);
    }

    // Submit
    const submitButton = screen.getByText('Submit Feedback');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalled();
    });
  });

  it('calls onCancel when cancel button is clicked', () => {
    const onCancel = vi.fn();
    
    render(
      <FeedbackForm
        answerId="test-answer-id"
        questionText="Test question?"
        onCancel={onCancel}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(onCancel).toHaveBeenCalled();
  });
});
