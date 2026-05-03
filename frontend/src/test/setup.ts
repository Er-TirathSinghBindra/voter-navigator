import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
  usePathname: () => '/',
}));

// Mock next-auth
vi.mock('next/server', () => {
  return {
    NextRequest: class {
      url: string;
      method: string;
      _body: any;
      constructor(url: string, init?: any) {
        this.url = url;
        this.method = init?.method || 'GET';
        this._body = init?.body ? JSON.parse(init.body) : null;
      }
      async json() { return this._body; }
    },
    NextResponse: {
      json: vi.fn((data, init) => ({
        json: async () => data,
        status: init?.status || 200,
      })),
    },
  };
});

// Mock next-auth
vi.mock('next-auth/react', () => ({
  useSession: vi.fn(() => ({ data: null, status: 'unauthenticated' })),
  signIn: vi.fn(),
  signOut: vi.fn(),
  SessionProvider: ({ children }: { children: React.ReactNode }) => children,
}));
