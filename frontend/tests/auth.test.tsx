import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { AuthProvider, useAuth } from '../src/context/AuthContext';
import sharedConfig from '../../shared_config.json';

// Mock the API module
vi.mock('../src/services/api', () => ({
  api: {
    login: vi.fn(),
  },
}));

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('should provide auth context', () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    expect(result.current).toHaveProperty('user');
    expect(result.current).toHaveProperty('token');
    expect(result.current).toHaveProperty('isAuthenticated');
    expect(result.current).toHaveProperty('login');
    expect(result.current).toHaveProperty('logout');
  });

  it('should initialize with no authentication', () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    expect(result.current.user).toBeNull();
    expect(result.current.token).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('should store token using shared config key', async () => {
    const { api } = await import('../src/services/api');
    const mockLogin = vi.mocked(api.login);

    const mockResponse = {
      [sharedConfig.auth.login_response.token_field]: 'test-token-123',
      [sharedConfig.auth.login_response.user_field]: {
        user_id: '1',
        email: 'test@example.com',
        display_name: 'Test User',
        roles: ['end_user'],
      },
    };

    mockLogin.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await act(async () => {
      await result.current.login('test@example.com', 'password');
    });

    const storedToken = localStorage.getItem(sharedConfig.auth.storage_key);
    expect(storedToken).toBe('test-token-123');
  });

  it('should clear authentication on logout', async () => {
    localStorage.setItem(sharedConfig.auth.storage_key, 'test-token');
    localStorage.setItem('user', JSON.stringify({ user_id: '1', email: 'test@example.com' }));

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    act(() => {
      result.current.logout();
    });

    expect(localStorage.getItem(sharedConfig.auth.storage_key)).toBeNull();
    expect(localStorage.getItem('user')).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });
});
