import { describe, it, expect } from 'vitest';
import { authOptions } from '@/lib/auth';

describe('Auth Configuration', () => {
  it('has GoogleProvider configured', () => {
    const googleProvider = authOptions.providers.find(p => p.id === 'google');
    expect(googleProvider).toBeDefined();
  });

  it('jwt callback persists accessToken from account', async () => {
    const token = {};
    const account = { access_token: 'test_token' };
    const result: any = await (authOptions.callbacks as any).jwt({ token, account });
    expect(result.accessToken).toBe('test_token');
  });

  it('jwt callback returns token as is if no account', async () => {
    const token = { accessToken: 'existing' };
    const result: any = await (authOptions.callbacks as any).jwt({ token });
    expect(result.accessToken).toBe('existing');
  });

  it('session callback injects accessToken from token', async () => {
    const session = { user: {} };
    const token = { accessToken: 'test_token' };
    const result: any = await (authOptions.callbacks as any).session({ session, token });
    expect(result.accessToken).toBe('test_token');
  });
});
