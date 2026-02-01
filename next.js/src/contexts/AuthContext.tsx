// Authentication context and state management
"use client";

import { createContext, useContext, useState, ReactNode } from 'react';
import { authenticateUser, TEST_CREDENTIALS, UserCredentials } from '@/lib/credentials';

interface User extends Omit<UserCredentials, 'password'> {}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => { success: boolean; message?: string };
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const login = (email: string, password: string) => {
    const result = authenticateUser(email, password);
    
    if (result.success && result.user) {
      setUser(result.user);
      return { success: true };
    } else {
      return { success: false, message: result.message };
    }
  };

  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      login,
      logout,
      isAuthenticated: !!user
    }}>
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
