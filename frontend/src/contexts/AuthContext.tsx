"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api, getErrorMessage } from '@/lib/api';
import { User, UserRole } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';

interface LoginResponse {
  user: User;
  tokens: {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
  };
  session_id: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<{ success: boolean; message?: string }>;
  logout: () => Promise<void>;
  register: (data: any) => Promise<{ success: boolean; message?: string }>;
  forgotPassword: (email: string) => Promise<{ success: boolean; message?: string }>;
  resetPassword: (token: string, newPassword: string) => Promise<{ success: boolean; message?: string }>;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isStaff: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  // Check auth status on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await api.get<User>('/api/v1/users/me');
        setUser(response.data);
      } catch (err: any) {
        // Silent fail if not authenticated
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (username: string, password: string, rememberMe: boolean = false) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post<LoginResponse>('/api/v1/auth/login', {
        username, // Matches LoginRequest schema
        password,
        remember_me: rememberMe
      });

      setUser(response.data.user);
      return { success: true };
    } catch (err: any) {
      const message = getErrorMessage(err);
      setError(message);
      return { success: false, message };
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await api.post('/api/v1/auth/logout');
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setUser(null);
      router.push('/login');
    }
  };

  const register = async (userData: any) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post<User>('/api/v1/auth/register', userData);
      // Note: Registration might not auto-login depending on backend.
      // Assuming it returns created user but doesn't set session cookies automatically unless specified.
      return { success: true, message: 'Registration successful. Please login.' };
    } catch (err: any) {
      const message = getErrorMessage(err);
      setError(message);
      return { success: false, message };
    } finally {
      setLoading(false);
    }
  };

  const forgotPassword = async (email: string) => {
    setLoading(true);
    setError(null);

    try {
      await api.post('/api/v1/auth/forgot-password', { email });
      return { success: true, message: 'Password reset link sent to your email' };
    } catch (err: any) {
      const message = getErrorMessage(err);
      setError(message);
      return { success: false, message };
    } finally {
      setLoading(false);
    }
  };

  const resetPassword = async (token: string, newPassword: string) => {
    setLoading(true);
    setError(null);

    try {
      await api.post('/api/v1/auth/reset-password', { token, new_password: newPassword });
      return { success: true, message: 'Password reset successful' };
    } catch (err: any) {
      const message = getErrorMessage(err);
      setError(message);
      return { success: false, message };
    } finally {
      setLoading(false);
    }
  };

  const value = {
    user,
    loading,
    error,
    login,
    logout,
    register,
    forgotPassword,
    resetPassword,
    isAuthenticated: !!user,
    isAdmin: user?.role === UserRole.ADMIN,
    isStaff: user?.role === UserRole.STAFF || user?.role === UserRole.ADMIN
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
