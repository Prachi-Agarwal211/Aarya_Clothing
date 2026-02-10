# 🔐 Frontend Authentication Guide - Aarya Clothing

**Complete guide for implementing authentication in frontend applications**

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Authentication Flow](#authentication-flow)
3. [API Endpoints](#api-endpoints)
4. [Implementation Examples](#implementation-examples)
5. [Cookie vs Token Auth](#cookie-vs-token-auth)
6. [Error Handling](#error-handling)
7. [Security Best Practices](#security-best-practices)

---

## 🏗️ System Overview

### Authentication Architecture

We use a **dual authentication system** with:
- **JWT Tokens** (Access + Refresh tokens)
- **Cookie-based Sessions** (24-hour login persistence)
- **Role-based Access Control** (Admin, Staff, Customer)

### Services & Ports

| Service | Port | Purpose | Health Check |
|---------|------|---------|--------------|
| **Core Platform** | 8001 | Authentication, Users, Sessions | `/health` |

### User Roles

```typescript
enum UserRole {
  ADMIN = "admin",      // Full system access
  STAFF = "staff",      // Limited admin access
  CUSTOMER = "customer" // Regular users (default)
}
```

---

## 🔄 Authentication Flow

### 1. User Registration
```
Frontend → POST /api/v1/auth/register → Create User → Return User Data
```

### 2. User Login
```
Frontend → POST /api/v1/auth/login → Validate Credentials → 
         Set Cookies + Return Tokens + User Data
```

### 3. Authenticated Requests
```
Frontend → API Call (with cookies or token) → Validate → Return Data
```

### 4. Token Refresh
```
Frontend → POST /api/v1/auth/refresh → Validate Refresh Token → 
         Set New Access Token → Continue
```

### 5. Logout
```
Frontend → POST /api/v1/auth/logout → Clear Cookies + Revoke Tokens
```

---

## 🚀 API Endpoints

### Base URL
```
Development: http://localhost:8001
Production: https://yourdomain.com/api
```

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/register` | Register new user | ❌ |
| POST | `/api/v1/auth/login` | User login | ❌ |
| POST | `/api/v1/auth/refresh` | Refresh access token | ❌ |
| POST | `/api/v1/auth/logout` | Logout | ❌ |
| POST | `/api/v1/auth/logout-all` | Logout from all devices | ❌ |
| POST | `/api/v1/auth/change-password` | Change password | ✅ |
| POST | `/api/v1/auth/forgot-password` | Request password reset | ❌ |
| POST | `/api/v1/auth/reset-password` | Reset password with token | ❌ |
| GET | `/api/v1/auth/verify-reset-token/{token}` | Verify reset token | ❌ |
| POST | `/api/v1/auth/forgot-password-otp` | Request password reset OTP | ❌ |
| POST | `/api/v1/auth/reset-password-otp` | Reset password with OTP | ❌ |

### OTP Verification

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/send-otp` | Send OTP (Email/WhatsApp) | ❌ |
| POST | `/api/v1/auth/verify-otp` | Verify OTP code | ❌ |
| POST | `/api/v1/auth/resend-otp` | Resend OTP | ❌ |

### User Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/users/me` | Get current user info | ✅ |
| PATCH | `/api/v1/users/me` | Update user profile | ✅ |
| GET | `/api/v1/users/{user_id}` | Get user by ID | ✅ (admin/self) |

### Admin Role Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| PATCH | `/api/v1/admin/users/{user_id}/role` | Update user role | ✅ Admin |
| GET | `/api/v1/admin/users/role/{role}` | List users by role | ✅ Admin |

---

## 💻 Implementation Examples

### Cookie-based Authentication (Recommended)

#### Auth Service Class

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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      return await response.json();
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

  async requestPasswordResetOTP(identifier, otpType = 'EMAIL') {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/auth/forgot-password-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          identifier,
          otp_type: otpType
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to send password reset OTP');
      }

      return await response.json();
    } catch (error) {
      console.error('Request password reset OTP error:', error);
      throw error;
    }
  }

  async resetPasswordWithOTP(identifier, otpCode, newPassword, otpType = 'EMAIL') {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/auth/reset-password-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          identifier,
          otp_code: otpCode,
          new_password: newPassword,
          otp_type: otpType
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Password reset failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Reset password error:', error);
      throw error;
    }
  }

  async register(userData) {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Registration failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  }
}

export const authService = new AuthService();
```

#### React Hook Implementation

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

  const register = async (userData) => {
    try {
      setError(null);
      setLoading(true);
      const response = await authService.register(userData);
      return response;
    } catch (error) {
      setError(error.message);
      throw error;
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
    checkAuth,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'ADMIN',
    isStaff: user?.role === 'STAFF',
    isCustomer: user?.role === 'CUSTOMER'
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

#### Login Component

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

    // Basic validation
    if (!formData.username || !formData.password) {
      setErrors({ submit: 'Username and password are required' });
      return;
    }

    try {
      await login(formData);
      // Redirect to dashboard or home
      window.location.href = '/dashboard';
    } catch (error) {
      setErrors({ submit: error.message });
    }
  };

  return (
    <div className="login-container">
      <h2>Login to Aarya Clothing</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
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

        <div className="form-group">
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

        <div className="form-group">
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
    </div>
  );
}

export default Login;
```

#### Registration Component

```jsx
// Register.jsx
import { useState } from 'react';
import { useAuth } from './useAuth';

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
  const { register } = useAuth();

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
      await register({
        email: formData.email,
        username: formData.username,
        password: formData.password,
        full_name: formData.full_name
      });

      setSuccess(true);
    } catch (error) {
      setErrors({ submit: error.message });
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="success-message">
        <h2>Registration Successful!</h2>
        <p>Your account has been created. You can now login.</p>
        <button onClick={() => window.location.href = '/login'}>
          Go to Login
        </button>
      </div>
    );
  }

  return (
    <div className="register-container">
      <h2>Create Account</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
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

        <div className="form-group">
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

        <div className="form-group">
          <label htmlFor="full_name">Full Name:</label>
          <input
            type="text"
            id="full_name"
            name="full_name"
            value={formData.full_name}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
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

        <div className="form-group">
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
    </div>
  );
}

export default Register;
```

#### OTP Password Reset Component

```jsx
// PasswordResetOTP.jsx
import { useState } from 'react';
import { authService } from './authService';

function PasswordResetOTP() {
  const [step, setStep] = useState(1); // 1: email, 2: otp, 3: success
  const [formData, setFormData] = useState({
    identifier: '',
    otpCode: '',
    newPassword: '',
    confirmPassword: '',
    otpType: 'EMAIL'
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [timeLeft, setTimeLeft] = useState(600); // 10 minutes

  const handleIdentifierSubmit = async (e) => {
    e.preventDefault();
    setErrors({});
    setLoading(true);

    try {
      await authService.requestPasswordResetOTP(
        formData.identifier,
        formData.otpType
      );
      setStep(2);
      // Start OTP timer
      const timer = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (error) {
      setErrors({ submit: error.message });
    } finally {
      setLoading(false);
    }
  };

  const handleOTPSubmit = async (e) => {
    e.preventDefault();
    setErrors({});

    if (formData.newPassword !== formData.confirmPassword) {
      setErrors({ confirmPassword: 'Passwords do not match' });
      return;
    }

    if (formData.newPassword.length < 8) {
      setErrors({ newPassword: 'Password must be at least 8 characters' });
      return;
    }

    setLoading(true);

    try {
      await authService.resetPasswordWithOTP(
        formData.identifier,
        formData.otpCode,
        formData.newPassword,
        formData.otpType
      );
      setStep(3);
    } catch (error) {
      setErrors({ submit: error.message });
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  if (step === 3) {
    return (
      <div className="success-message">
        <h2>Password Reset Successful!</h2>
        <p>Your password has been reset successfully. You can now login with your new password.</p>
        <button onClick={() => window.location.href = '/login'}>
          Go to Login
        </button>
      </div>
    );
  }

  return (
    <div className="password-reset-otp">
      <h2>Reset Password with OTP</h2>
      
      {step === 1 && (
        <form onSubmit={handleIdentifierSubmit}>
          <div className="form-group">
            <label htmlFor="identifier">Email or Phone Number:</label>
            <input
              type="text"
              id="identifier"
              value={formData.identifier}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                identifier: e.target.value
              }))}
              placeholder="Enter your email or phone number"
              required
            />
          </div>

          <div className="form-group">
            <label>Send OTP via:</label>
            <div className="radio-group">
              <label>
                <input
                  type="radio"
                  value="EMAIL"
                  checked={formData.otpType === 'EMAIL'}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    otpType: e.target.value
                  }))}
                />
                Email
              </label>
              <label>
                <input
                  type="radio"
                  value="WHATSAPP"
                  checked={formData.otpType === 'WHATSAPP'}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    otpType: e.target.value
                  }))}
                />
                WhatsApp
              </label>
            </div>
          </div>

          {errors.submit && <div className="error">{errors.submit}</div>}
          
          <button type="submit" disabled={loading}>
            {loading ? 'Sending OTP...' : 'Send OTP'}
          </button>
        </form>
      )}

      {step === 2 && (
        <form onSubmit={handleOTPSubmit}>
          <div className="otp-info">
            <p>We've sent a 6-digit code to {formData.identifier}</p>
            {timeLeft > 0 && (
              <p>Code expires in {formatTime(timeLeft)}</p>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="otpCode">Enter OTP:</label>
            <input
              type="text"
              id="otpCode"
              value={formData.otpCode}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                otpCode: e.target.value
              }))}
              placeholder="Enter 6-digit code"
              maxLength={6}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="newPassword">New Password:</label>
            <input
              type="password"
              id="newPassword"
              value={formData.newPassword}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                newPassword: e.target.value
              }))}
              placeholder="Enter new password"
              required
            />
            {errors.newPassword && <span className="error">{errors.newPassword}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm New Password:</label>
            <input
              type="password"
              id="confirmPassword"
              value={formData.confirmPassword}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                confirmPassword: e.target.value
              }))}
              placeholder="Confirm new password"
              required
            />
            {errors.confirmPassword && <span className="error">{errors.confirmPassword}</span>}
          </div>

          {errors.submit && <div className="error">{errors.submit}</div>}
          
          <button type="submit" disabled={loading}>
            {loading ? 'Resetting Password...' : 'Reset Password'}
          </button>

          <button
            type="button"
            className="secondary"
            onClick={() => setStep(1)}
            disabled={loading}
          >
            Back
          </button>
        </form>
      )}
    </div>
  );
}

export default PasswordResetOTP;
```

---

## 🍪 Cookie vs Token Auth

### Cookie-based Authentication (Recommended)

**Pros:**
- Automatic token management
- CSRF protection built-in
- More secure (HttpOnly cookies)
- Simpler frontend code

**Cons:**
- Requires same-origin or proper CORS
- Less flexible for mobile apps

**Implementation:**
```javascript
// Just include credentials: 'include' in all requests
fetch('/api/v1/users/me', {
  credentials: 'include' // This sends cookies automatically
});
```

### Token-based Authentication

**Pros:**
- Works across domains
- Better for mobile apps
- More control over token storage

**Cons:**
- Manual token management
- Security risks if stored improperly
- More complex implementation

**Implementation:**
```javascript
// Store tokens in localStorage/memory
const tokens = JSON.parse(localStorage.getItem('auth_tokens'));

// Include token in headers
fetch('/api/v1/users/me', {
  headers: {
    'Authorization': `Bearer ${tokens.access_token}`
  }
});
```

---

## 🚨 Error Handling

### Common Error Responses

```typescript
// Validation Error (400)
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}

// Authentication Error (401)
{
  "detail": "Could not validate credentials"
}

// Forbidden Error (403)
{
  "detail": "Admin access required"
}

// Rate Limit Error (429)
{
  "detail": "Too many login attempts"
}
```

### Error Handling Implementation

```javascript
class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

async function handleApiCall(url, options = {}) {
  try {
    const response = await fetch(url, {
      credentials: 'include',
      ...options
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      
      if (response.status === 401) {
        // Token expired, try refresh
        await authService.refreshToken();
        // Retry the request
        return handleApiCall(url, options);
      }
      
      throw new ApiError(
        errorData.detail || 'Request failed',
        response.status,
        errorData
      );
    }

    return response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    
    // Network or other errors
    throw new ApiError('Network error', 0, { originalError: error });
  }
}
```

---

## 🔒 Security Best Practices

### 1. Password Security
- Minimum 8 characters
- Require uppercase, lowercase, and numbers
- Implement password strength indicators

### 2. Session Management
- Use secure, HttpOnly cookies
- Implement proper logout
- Clear sensitive data on logout

### 3. Token Security
- Short-lived access tokens (30 minutes)
- Refresh tokens with longer expiry (24 hours)
- Store tokens securely

### 4. Rate Limiting
- Login attempts: 5 per 5 minutes
- OTP requests: 5 per hour
- Account lockout after 5 failed attempts

### 5. CSRF Protection
- Use SameSite cookie attributes
- Include CSRF tokens for state-changing requests
- Validate origin headers

### 6. Input Validation
- Validate all user inputs
- Sanitize data before sending to API
- Use proper error messages (don't expose sensitive info)

---

## 📱 Mobile App Considerations

For mobile applications, use token-based authentication:

```javascript
// Mobile Auth Service
class MobileAuthService {
  constructor() {
    this.tokens = null;
  }

  async login(credentials) {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });
    
    const data = await response.json();
    this.tokens = data.tokens;
    
    // Store securely (Keychain/Keystore)
    await SecureStorage.set('auth_tokens', this.tokens);
    
    return data;
  }

  getAuthHeaders() {
    return {
      'Authorization': `Bearer ${this.tokens?.access_token}`
    };
  }
}
```

---

## 🧪 Testing Authentication

### Test Login Flow

```javascript
// Test login
async function testLogin() {
  try {
    const result = await authService.login({
      username: 'test@example.com',
      password: 'TestPass123!',
      remember_me: true
    });
    
    console.log('Login successful:', result);
    
    // Test getting user info
    const user = await authService.getCurrentUser();
    console.log('Current user:', user);
    
  } catch (error) {
    console.error('Login test failed:', error);
  }
}
```

### Test Registration Flow

```javascript
// Test registration
async function testRegistration() {
  try {
    const result = await authService.register({
      email: 'newuser@example.com',
      username: 'newuser',
      password: 'SecurePass123!',
      full_name: 'New User'
    });
    
    console.log('Registration successful:', result);
  } catch (error) {
    console.error('Registration test failed:', error);
  }
}
```

---

## 🔄 Next Steps

1. **Set up environment variables** for API URLs
2. **Implement auth service** in your frontend framework
3. **Create login/register components**
4. **Add protected routes** with role-based access
5. **Implement error handling** and user feedback
6. **Test thoroughly** with different scenarios
7. **Add security measures** like CSRF protection

---

## 📞 Support

For authentication issues:
1. Check API health: `GET /health`
2. Verify network connectivity
3. Check browser console for errors
4. Ensure proper CORS configuration
5. Review rate limiting headers

---

**Happy coding! 🚀**
