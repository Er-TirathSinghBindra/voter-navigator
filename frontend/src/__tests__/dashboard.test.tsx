import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Dashboard from '@/app/dashboard/page';
import { useSession, signIn, signOut } from 'next-auth/react';

// Mock fetch
global.fetch = vi.fn();

describe('Dashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders sign-in button when unauthenticated', () => {
    (useSession as any).mockReturnValue({ data: null, status: 'unauthenticated' });
    render(<Dashboard />);
    expect(screen.getByText(/Authentication Required/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign in with Google/i })).toBeInTheDocument();
  });

  it('renders chat interface when authenticated', () => {
    (useSession as any).mockReturnValue({
      data: { user: { email: 'test@example.com' } },
      status: 'authenticated',
    });
    render(<Dashboard />);
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Ask about polling locations/i)).toBeInTheDocument();
  });

  it('sends a message and displays assistant response', async () => {
    (useSession as any).mockReturnValue({
      data: { user: { email: 'test@example.com' } },
      status: 'authenticated',
    });
    
    (global.fetch as any).mockResolvedValue({
      json: async () => ({ content: 'I am here to help!' }),
    });

    render(<Dashboard />);
    
    const input = screen.getByPlaceholderText(/Ask about polling locations/i);
    const sendButton = screen.getByRole('button', { name: /Send message/i });

    fireEvent.change(input, { target: { value: 'Where do I vote?' } });
    fireEvent.click(sendButton);

    expect(screen.getByText('Where do I vote?')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('I am here to help!')).toBeInTheDocument();
    });
  });

  it('displays error message when API fails', async () => {
    (useSession as any).mockReturnValue({
      data: { user: { email: 'test@example.com' } },
      status: 'authenticated',
    });
    
    (global.fetch as any).mockRejectedValue(new Error('Network Error'));

    render(<Dashboard />);
    
    const input = screen.getByPlaceholderText(/Ask about polling locations/i);
    const sendButton = screen.getByRole('button', { name: /Send message/i });

    fireEvent.change(input, { target: { value: 'Test Error' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText(/Sorry, I encountered an error/i)).toBeInTheDocument();
    });
  });

  it('displays loading state', () => {
    (useSession as any).mockReturnValue({ data: null, status: 'loading' });
    render(<Dashboard />);
    expect(screen.getByText(/Loading session data/i)).toBeInTheDocument();
  });

  it('handles backend error field', async () => {
    (useSession as any).mockReturnValue({
      data: { user: { email: 'test@example.com' } },
      status: 'authenticated',
    });
    
    (global.fetch as any).mockResolvedValue({
      json: async () => ({ error: 'Simulated API Error' }),
    });

    render(<Dashboard />);
    const input = screen.getByPlaceholderText(/Ask about polling locations/i);
    const sendButton = screen.getByRole('button', { name: /Send message/i });

    fireEvent.change(input, { target: { value: 'Trigger Error' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText(/Error: Simulated API Error/i)).toBeInTheDocument();
    });
  });

  it('calls signIn on login click', () => {
    (useSession as any).mockReturnValue({ data: null, status: 'unauthenticated' });
    render(<Dashboard />);
    fireEvent.click(screen.getByRole('button', { name: /Sign in with Google/i }));
    expect(signIn).toHaveBeenCalledWith('google');
  });

  it('calls signOut on logout click', () => {
    (useSession as any).mockReturnValue({
      data: { user: { email: 'test@example.com' } },
      status: 'authenticated',
    });
    render(<Dashboard />);
    fireEvent.click(screen.getByRole('button', { name: /Sign out/i }));
    expect(signOut).toHaveBeenCalled();
  });
});
