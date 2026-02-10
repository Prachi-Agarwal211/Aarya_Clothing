# Authentication Examples - Frontend Implementation

This document provides practical code examples for implementing authentication in your frontend application.

## 🍪 Cookie-based Authentication (Recommended)

### Login Implementation

```javascript
// authService.js
class AuthService {
  constructor() {
    this.baseURL = 'http://localhost:8001';
  }

  async login(credentials) {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/auth/login`, {
        method: 'POST',
        credentials: 'include', // Important for cookies!
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  async logout() {
    try {
      await fetch(`${this.baseURL}/api/v1/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
  }

  async getCurrentUser() {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/users/me`, {
        credentials: 'include'
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Token expired, try to refresh
          await this.refreshToken();
          // Retry the request
          return this.getCurrentUser();
        }
        throw new Error('Failed to get user info');
      }

      return await response.json();
    } catch (error) {
      console.error('Get current user error:', error);
      throw error;
    }
  }

  async refreshToken() {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/auth/refresh`, {
        method: 'POST',
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Token refresh error:', error);
      // Redirect to login page
      window.location.href = '/login';
      throw error;
    }
  }
}

export const authService = new AuthService();
```

### React Hook Example

```jsx
// useAuth.js
import { useState, useEffect, createContext, useContext } from 'react';
import { authService } from './authService';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      setLoading(true);
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials) => {
    try {
      setError(null);
      setLoading(true);
      const response = await authService.login(credentials);
      setUser(response.user);
      return response;
    } catch (error) {
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
      setUser(null);
    } catch (error) {
      console.error('Logout error:', error);
      setUser(null); // Force logout even if API call fails
    }
  };

  const value = {
    user,
    loading,
    error,
    login,
    logout,
    checkAuth
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

### Login Component Example

```jsx
// Login.jsx
import { useState } from 'react';
import { useAuth } from './useAuth';

function Login() {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    remember_me: false
  });
  const [errors, setErrors] = useState({});
  const { login, loading, error } = useAuth();

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrors({});

    try {
      await login(formData);
      // Redirect to dashboard or home
      window.location.href = '/dashboard';
    } catch (error) {
      setErrors({ submit: error.message });
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="username">Email or Username:</label>
        <input
          type="text"
          id="username"
          name="username"
          value={formData.username}
          onChange={handleChange}
          required
        />
      </div>

      <div>
        <label htmlFor="password">Password:</label>
        <input
          type="password"
          id="password"
          name="password"
          value={formData.password}
          onChange={handleChange}
          required
        />
      </div>

      <div>
        <label>
          <input
            type="checkbox"
            name="remember_me"
            checked={formData.remember_me}
            onChange={handleChange}
          />
          Remember me for 24 hours
        </label>
      </div>

      {error && <div className="error">{error}</div>}
      {errors.submit && <div className="error">{errors.submit}</div>}

      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}

export default Login;
```

---

## 🎫 Authorization Header Authentication

### Token-based Implementation

```javascript
// tokenAuthService.js
class TokenAuthService {
  constructor() {
    this.baseURL = 'http://localhost:8001';
    this.tokens = this.loadTokens();
  }

  loadTokens() {
    const stored = localStorage.getItem('auth_tokens');
    return stored ? JSON.parse(stored) : null;
  }

  saveTokens(tokens) {
    this.tokens = tokens;
    localStorage.setItem('auth_tokens', JSON.stringify(tokens));
  }

  clearTokens() {
    this.tokens = null;
    localStorage.removeItem('auth_tokens');
  }

  async login(credentials) {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      const data = await response.json();
      this.saveTokens(data.tokens);
      return data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  async logout() {
    try {
      if (this.tokens?.refresh_token) {
        await fetch(`${this.baseURL}/api/v1/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.tokens.access_token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            refresh_token: this.tokens.refresh_token
          })
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.clearTokens();
    }
  }

  getAuthHeaders() {
    if (!this.tokens?.access_token) {
      return {};
    }
    return {
      'Authorization': `Bearer ${this.tokens.access_token}`
    };
  }

  async makeAuthenticatedRequest(url, options = {}) {
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
        ...options.headers
      }
    };

    try {
      const response = await fetch(url, {
        ...defaultOptions,
        ...options
      });

      if (response.status === 401) {
        // Try to refresh token
        const refreshed = await this.refreshToken();
        if (refreshed) {
          // Retry the original request with new token
          defaultOptions.headers.Authorization = `Bearer ${this.tokens.access_token}`;
          return fetch(url, {
            ...defaultOptions,
            ...options
          });
        }
      }

      return response;
    } catch (error) {
      console.error('Authenticated request error:', error);
      throw error;
    }
  }

  async refreshToken() {
    if (!this.tokens?.refresh_token) {
      return false;
    }

    try {
      const response = await fetch(`${this.baseURL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          refresh_token: this.tokens.refresh_token
        })
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      this.saveTokens(data);
      return true;
    } catch (error) {
      console.error('Token refresh error:', error);
      this.clearTokens();
      return false;
    }
  }
}

export const tokenAuthService = new TokenAuthService();
```

### API Client with Token Auth

```javascript
// apiClient.js
import { tokenAuthService } from './tokenAuthService';

class ApiClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    // For authenticated requests, use the token service
    if (options.authenticated !== false) {
      return tokenAuthService.makeAuthenticatedRequest(url, options);
    }

    // For public requests, use regular fetch
    return fetch(url, options);
  }

  // Core Service Methods
  async getCurrentUser() {
    const response = await this.request('/api/v1/users/me');
    if (!response.ok) throw new Error('Failed to get user');
    return response.json();
  }

  async updateProfile(userData) {
    const response = await this.request('/api/v1/users/me', {
      method: 'PATCH',
      body: JSON.stringify(userData)
    });
    if (!response.ok) throw new Error('Failed to update profile');
    return response.json();
  }

  // Commerce Service Methods
  async getProducts(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const response = await this.request(
      `http://localhost:8010/api/v1/products?${queryString}`,
      { authenticated: false }
    );
    return response.json();
  }

  async addToCart(userId, item) {
    const response = await this.request(
      `http://localhost:8010/api/v1/cart/${userId}/add`,
      {
        method: 'POST',
        body: JSON.stringify(item)
      }
    );
    if (!response.ok) throw new Error('Failed to add to cart');
    return response.json();
  }

  async createOrder(orderData) {
    const response = await this.request(
      'http://localhost:8010/api/v1/orders',
      {
        method: 'POST',
        body: JSON.stringify(orderData)
      }
    );
    if (!response.ok) throw new Error('Failed to create order');
    return response.json();
  }
}

export const apiClient = new ApiClient();
```

---

## 🔄 Registration Flow

### Registration Component

```jsx
// Register.jsx
import { useState } from 'react';
import { authService } from './authService';

function Register() {
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirm_password: '',
    full_name: ''
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.email) newErrors.email = 'Email is required';
    if (!formData.username) newErrors.username = 'Username is required';
    if (!formData.password) newErrors.password = 'Password is required';
    if (formData.password !== formData.confirm_password) {
      newErrors.confirm_password = 'Passwords do not match';
    }
    if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setLoading(true);
    setErrors({});

    try {
      const response = await fetch('http://localhost:8001/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          username: formData.username,
          password: formData.password,
          full_name: formData.full_name
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Registration failed');
      }

      setSuccess(true);
    } catch (error) {
      setErrors({ submit: error.message });
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div>
        <h2>Registration Successful!</h2>
        <p>Please check your email to verify your account.</p>
        <button onClick={() => window.location.href = '/login'}>
          Go to Login
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="email">Email:</label>
        <input
          type="email"
          id="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          required
        />
        {errors.email && <span className="error">{errors.email}</span>}
      </div>

      <div>
        <label htmlFor="username">Username:</label>
        <input
          type="text"
          id="username"
          name="username"
          value={formData.username}
          onChange={handleChange}
          required
        />
        {errors.username && <span className="error">{errors.username}</span>}
      </div>

      <div>
        <label htmlFor="full_name">Full Name:</label>
        <input
          type="text"
          id="full_name"
          name="full_name"
          value={formData.full_name}
          onChange={handleChange}
        />
      </div>

      <div>
        <label htmlFor="password">Password:</label>
        <input
          type="password"
          id="password"
          name="password"
          value={formData.password}
          onChange={handleChange}
          required
        />
        {errors.password && <span className="error">{errors.password}</span>}
      </div>

      <div>
        <label htmlFor="confirm_password">Confirm Password:</label>
        <input
          type="password"
          id="confirm_password"
          name="confirm_password"
          value={formData.confirm_password}
          onChange={handleChange}
          required
        />
        {errors.confirm_password && <span className="error">{errors.confirm_password}</span>}
      </div>

      {errors.submit && <div className="error">{errors.submit}</div>}

      <button type="submit" disabled={loading}>
        {loading ? 'Registering...' : 'Register'}
      </button>
    </form>
  );
}

export default Register;
```

---

## 📱 OTP Verification

### OTP Component

```jsx
// OTPVerification.jsx
import { useState } from 'react';

function OTPVerification({ identifier, onVerified, onResend }) {
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [timeLeft, setTimeLeft] = useState(600); // 10 minutes
  const [canResend, setCanResend] = useState(false);

  // Timer for OTP expiry
  useEffect(() => {
    if (timeLeft > 0) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
      return () => clearTimeout(timer);
    } else {
      setCanResend(true);
    }
  }, [timeLeft]);

  const handleChange = (index, value) => {
    if (value.length > 1) return; // Only allow one digit
    
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    // Auto-focus next input
    if (value && index < 5) {
      const nextInput = document.getElementById(`otp-${index + 1}`);
      nextInput?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      const prevInput = document.getElementById(`otp-${index - 1}`);
      prevInput?.focus();
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const otpCode = otp.join('');
    
    if (otpCode.length !== 6) {
      setError('Please enter all 6 digits');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8001/api/v1/auth/verify-otp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          identifier,
          otp_code: otpCode,
          otp_type: 'EMAIL'
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'OTP verification failed');
      }

      const data = await response.json();
      onVerified(data);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (!canResend) return;

    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8001/api/v1/auth/resend-otp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          identifier,
          otp_type: 'EMAIL'
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to resend OTP');
      }

      // Reset timer
      setTimeLeft(600);
      setCanResend(false);
      setOtp(['', '', '', '', '', '']);
      onResend();
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <form onSubmit={handleSubmit}>
      <h3>Enter OTP</h3>
      <p>We've sent a 6-digit code to {identifier}</p>
      
      <div className="otp-inputs">
        {otp.map((digit, index) => (
          <input
            key={index}
            id={`otp-${index}`}
            type="text"
            maxLength={1}
            value={digit}
            onChange={(e) => handleChange(index, e.target.value)}
            onKeyDown={(e) => handleKeyDown(index, e)}
            className="otp-input"
          />
        ))}
      </div>

      {error && <div className="error">{error}</div>}

      <div className="timer">
        {timeLeft > 0 ? (
          <p>Code expires in {formatTime(timeLeft)}</p>
        ) : (
          <p>Code has expired</p>
        )}
      </div>

      <button type="submit" disabled={loading || otp.join('').length !== 6}>
        {loading ? 'Verifying...' : 'Verify'}
      </button>

      <button
        type="button"
        onClick={handleResend}
        disabled={!canResend || loading}
        className="resend-btn"
      >
        {canResend ? 'Resend OTP' : `Resend in ${formatTime(timeLeft)}`}
      </button>
    </form>
  );
}

export default OTPVerification;
```

### Role Management

```javascript
// Role Management Service
class RoleService {
  constructor() {
    this.baseURL = 'http://localhost:8001';
  }

  async updateUserRole(userId, newRole) {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/admin/users/${userId}/role`, {
        method: 'PATCH',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ role: newRole })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update user role');
      }

      return await response.json();
    } catch (error) {
      console.error('Update role error:', error);
      throw error;
    }
  }

  async getUsersByRole(role, skip = 0, limit = 100) {
    try {
      const response = await fetch(
        `${this.baseURL}/api/v1/admin/users/role/${role}?skip=${skip}&limit=${limit}`,
        {
          credentials: 'include'
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch users by role');
      }

      return await response.json();
    } catch (error) {
      console.error('Get users by role error:', error);
      throw error;
    }
  }
}

export const roleService = new RoleService();
```

### Role Management Component

```jsx
// UserRoleManager.jsx
import { useState } from 'react';
import { roleService } from './roleService';

function UserRoleManager({ user, onRoleUpdated }) {
  const [selectedRole, setSelectedRole] = useState(user.role);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const roles = [
    { value: 'CUSTOMER', label: 'Customer' },
    { value: 'STAFF', label: 'Staff' },
    { value: 'ADMIN', label: 'Admin' }
  ];

  const handleRoleChange = async (newRole) => {
    if (newRole === user.role) return;

    setLoading(true);
    setError('');

    try {
      const updatedUser = await roleService.updateUserRole(user.id, newRole);
      setSelectedRole(newRole);
      onRoleUpdated(updatedUser);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="role-manager">
      <h4>Role Management</h4>
      <div className="user-info">
        <span><strong>User:</strong> {user.username}</span>
        <span><strong>Current Role:</strong> {user.role}</span>
      </div>
      
      <div className="role-selector">
        <label>Change Role:</label>
        <select
          value={selectedRole}
          onChange={(e) => handleRoleChange(e.target.value)}
          disabled={loading}
        >
          {roles.map(role => (
            <option key={role.value} value={role.value}>
              {role.label}
            </option>
          ))}
        </select>
      </div>

      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Updating role...</div>}
    </div>
  );
}

export default UserRoleManager;
```

### Users by Role Component

```jsx
// UsersByRole.jsx
import { useState, useEffect } from 'react';
import { roleService } from './roleService';

function UsersByRole() {
  const [users, setUsers] = useState([]);
  const [selectedRole, setSelectedRole] = useState('CUSTOMER');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const roles = [
    { value: 'CUSTOMER', label: 'Customers' },
    { value: 'STAFF', label: 'Staff Members' },
    { value: 'ADMIN', label: 'Administrators' }
  ];

  useEffect(() => {
    loadUsers();
  }, [selectedRole]);

  const loadUsers = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await roleService.getUsersByRole(selectedRole);
      setUsers(response.users || []);
    } catch (error) {
      setError(error.message);
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="users-by-role">
      <h3>Users by Role</h3>
      
      <div className="role-tabs">
        {roles.map(role => (
          <button
            key={role.value}
            className={`tab ${selectedRole === role.value ? 'active' : ''}`}
            onClick={() => setSelectedRole(role.value)}
          >
            {role.label}
          </button>
        ))}
      </div>

      {loading && <div className="loading">Loading users...</div>}
      {error && <div className="error">{error}</div>}

      <div className="users-list">
        {users.map(user => (
          <div key={user.id} className="user-card">
            <div className="user-info">
              <h4>{user.username}</h4>
              <p>{user.email}</p>
              <p><strong>Full Name:</strong> {user.full_name}</p>
              <p><strong>Role:</strong> <span className="role-badge">{user.role}</span></p>
              <p><strong>Status:</strong> 
                <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                  {user.is_active ? 'Active' : 'Inactive'}
                </span>
              </p>
            </div>
            
            <UserRoleManager 
              user={user} 
              onRoleUpdated={(updatedUser) => {
                setUsers(users.map(u => 
                  u.id === updatedUser.id ? updatedUser : u
                ));
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

export default UsersByRole;
```

---

## 🔒 Protected Routes

### Route Guard Component

```jsx
// ProtectedRoute.jsx
import { useAuth } from './useAuth';
import { useEffect, useState } from 'react';

function ProtectedRoute({ children }) {
  const { user, loading, checkAuth } = useAuth();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const verifyAuth = async () => {
      try {
        await checkAuth();
      } catch (error) {
        console.error('Auth check failed:', error);
      } finally {
        setChecking(false);
      }
    };

    if (!loading) {
      verifyAuth();
    }
  }, [loading, checkAuth]);

  if (loading || checking) {
    return <div>Loading...</div>;
  }

  if (!user) {
    // Redirect to login
    window.location.href = '/login';
    return null;
  }

  return children;
}

export default ProtectedRoute;
```

### Usage in App Router

```jsx
// App.jsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './useAuth';
import ProtectedRoute from './ProtectedRoute';
import Login from './Login';
import Register from './Register';
import Dashboard from './Dashboard';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Home />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
```

These examples provide a complete foundation for implementing authentication in your frontend application. Choose the cookie-based approach for web browsers or the token-based approach for mobile apps or when you need more control over token storage.
