import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QuestionPage } from '../src/pages/QuestionPage';
import { api } from '../src/services/api';

// Mock the API
vi.mock('../src/services/api', () => ({
  api: {
    submitQuestion: vi.fn(),
  },
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('QuestionPage', () => {
  it('renders question input form', () => {
    render(
      <BrowserRouter>
        <QuestionPage />
      </BrowserRouter>
    );

    expect(screen.getByText('What can I help you find?')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Example: Who owns the payment service/)).toBeInTheDocument();
    expect(screen.getByText('Ask Question')).toBeInTheDocument();
  });

  it('has 2000 character maxLength attribute', () => {
    render(
      <BrowserRouter>
        <QuestionPage />
      </BrowserRouter>
    );

    const textarea = screen.getByPlaceholderText(/Example: Who owns the payment service/) as HTMLTextAreaElement;
    
    // Check that maxLength is set to 2000
    expect(textarea.maxLength).toBe(2000);
  });

  it('shows character counter', () => {
    render(
      <BrowserRouter>
        <QuestionPage />
      </BrowserRouter>
    );

    const textarea = screen.getByPlaceholderText(/Example: Who owns the payment service/);
    
    expect(screen.getByText('0 / 2000')).toBeInTheDocument();
    
    fireEvent.change(textarea, { target: { value: 'Test question' } });
    
    expect(screen.getByText('13 / 2000')).toBeInTheDocument();
  });

  it('disables submit button when question is empty', () => {
    render(
      <BrowserRouter>
        <QuestionPage />
      </BrowserRouter>
    );

    const submitButton = screen.getByText('Ask Question').closest('button');
    expect(submitButton).toBeDisabled();
  });

  it('enables submit button when question has text', () => {
    render(
      <BrowserRouter>
        <QuestionPage />
      </BrowserRouter>
    );

    const textarea = screen.getByPlaceholderText(/Example: Who owns the payment service/);
    fireEvent.change(textarea, { target: { value: 'Who owns the payment service?' } });

    const submitButton = screen.getByText('Ask Question').closest('button');
    expect(submitButton).not.toBeDisabled();
  });

  it('shows loading state during submission', async () => {
    const mockSubmit = vi.fn().mockImplementation(() => new Promise(() => {})); // Never resolves
    (api.submitQuestion as ReturnType<typeof vi.fn>).mockImplementation(mockSubmit);

    render(
      <BrowserRouter>
        <QuestionPage />
      </BrowserRouter>
    );

    const textarea = screen.getByPlaceholderText(/Example: Who owns the payment service/);
    fireEvent.change(textarea, { target: { value: 'Who owns the payment service?' } });

    const submitButton = screen.getByText('Ask Question').closest('button');
    fireEvent.click(submitButton!);

    await waitFor(() => {
      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });
  });

  it('renders popular question cards', () => {
    render(
      <BrowserRouter>
        <QuestionPage />
      </BrowserRouter>
    );

    expect(screen.getByText('Popular Questions')).toBeInTheDocument();
    expect(screen.getByText('Team Ownership')).toBeInTheDocument();
    expect(screen.getByText('Dependencies')).toBeInTheDocument();
    expect(screen.getByText('Runbooks')).toBeInTheDocument();
  });

  it('populates textarea when clicking popular question', () => {
    render(
      <BrowserRouter>
        <QuestionPage />
      </BrowserRouter>
    );

    const ownershipCard = screen.getByText('Team Ownership').closest('div');
    fireEvent.click(ownershipCard!);

    const textarea = screen.getByPlaceholderText(/Example: Who owns the payment service/) as HTMLTextAreaElement;
    expect(textarea.value).toBe('Who owns the payment service?');
  });
});
