import { describe, it, expect, vi } from 'vitest';
import { POST } from '@/app/api/proxy/[...path]/route';
import { NextRequest } from 'next/server';
import { getServerSession } from 'next-auth/next';

vi.mock('next-auth/next', () => ({
  getServerSession: vi.fn(),
}));

// Mock global fetch
global.fetch = vi.fn();

describe('API Proxy Route', () => {
  it('returns 401 if no session exists', async () => {
    (getServerSession as any).mockResolvedValue(null);
    const req = new NextRequest('http://localhost/api/proxy/chat', { method: 'POST' });
    const params = Promise.resolve({ path: ['chat'] });

    const res: any = await POST(req, { params });
    const data = await res.json();
    
    expect(res.status).toBe(401);
    expect(data.error).toBe('Unauthorized');
  });

  it('proxies request to backend with auth token', async () => {
    (getServerSession as any).mockResolvedValue({ accessToken: 'test_token' });
    (global.fetch as any).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ content: 'Hello from backend' }),
    });

    const req = new NextRequest('http://localhost/api/proxy/chat', {
      method: 'POST',
      body: JSON.stringify({ messages: [] }),
    });
    const params = Promise.resolve({ path: ['chat'] });

    const res: any = await POST(req, { params });
    const data = await res.json();
    expect(data.content).toBe('Hello from backend');
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/chat'),
      expect.objectContaining({
        method: 'POST',
      })
    );
  });

  it('returns 500 if backend fetch fails', async () => {
    (getServerSession as any).mockResolvedValue({ accessToken: 'test_token' });
    (global.fetch as any).mockRejectedValue(new Error('Fetch Failed'));

    const req = new NextRequest('http://localhost/api/proxy/chat', {
      method: 'POST',
      body: JSON.stringify({ messages: [] }),
    });
    const params = Promise.resolve({ path: ['chat'] });

    const res: any = await POST(req, { params });
    const data = await res.json();

    expect(res.status).toBe(500);
    expect(data.error).toContain('Backend Unreachable');
  });
});
