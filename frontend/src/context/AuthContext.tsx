import React, { createContext, useContext, useState, useEffect } from 'react';
import sharedConfig from '../../../shared_config.json';
import { api } from '../services/api';
import type { User, AuthContextType } from '../types/auth';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Authentication context provider
 * Manages user authentication state, token storage, and login/logout operations
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore authentication state from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem(sharedConfig.auth.storage_key);
    const storedUser = localStorage.getItem('user');

    if (storedToken && storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser);
        setToken(storedToken);
        setUser(parsedUser);
      } catch (error) {
        console.error('Failed to parse stored user data:', error);
        localStorage.removeItem(sharedConfig.auth.storage_key);
        localStorage.removeItem('user');
      }
    }

    setIsLoading(false);
  }, []);

  /**
   * Login with email and password
   */
  const login = async (email: string, password: string) => {
    try {
      const response = await api.login({ email, password });
      
      // Extract token and user from response using shared config field names
      const authToken = response[sharedConfig.auth.login_response.token_field as keyof typeof response] as string;
      const userData = response[sharedConfig.auth.login_response.user_field as keyof typeof response] as User;

      // Store in state
      setToken(authToken);
      setUser(userData);

      // Persist to localStorage
      localStorage.setItem(sharedConfig.auth.storage_key, authToken);
      localStorage.setItem('user', JSON.stringify(userData));
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  /**
   * Logout and clear authentication state
   */
  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem(sharedConfig.auth.storage_key);
    localStorage.removeItem('user');
  };

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated: !!token && !!user,
    login,
    logout,
  };

  // Don't render children until we've checked for existing auth
  if (isLoading) {
    return null;
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to access authentication context
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
