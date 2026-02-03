# Aarya Clothing - Complete Authentication Flow

## Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Database Schema](#2-database-schema)
3. [API Endpoints](#3-api-endpoints)
4. [Request/Response Flow](#4-requestresponse-flow)
5. [Token Management](#5-token-management)
6. [OTP Verification](#6-otp-verification-email--whatsapp)
7. [Cookie-Based Sessions](#7-cookie-based-sessions)
8. [Frontend Integration](#8-frontend-integration)
9. [Security Measures](#9-security-measures)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Login     │  │   Register  │  │   Profile   │             │
│  │   Page      │  │   Page      │  │   Page      │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                 │                 │                     │
│         └─────────────────┼─────────────────┘                     │
│                           │                                       │
│                    HTTP + Cookies                                 │
│                           │                                       │
│                           ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    API Gateway / Nginx                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │                                       │
│                           ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Core Platform Service                 │    │
│  │                   (FastAPI - Port 8001)                 │    │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────────────┐   │    │
│  │  │  Auth     │  │   User    │  │  OTP Service      │   │    │
│  │  │  Service  │  │  Service  │  │  (Email/WhatsApp) │   │    │
│  │  └─────┬─────┘  └─────┬─────┘  └───────────────────┘   │    │
│  │        │              │                                  │    │
│  │        └──────────────┼──────────────────────────────────┘    │
│  │                       │                                       │
│  │              HTTP-Only Cookies                              │
│  │                       │                                       │
│  └───────────────────────┼───────────────────────────────────────┘
│                          │
│         ┌────────────────┼────────────────┐
│         │                │                │
│         ▼                ▼                ▼
│  ┌───────────┐    ┌───────────┐    ┌───────────┐
│  │ PostgreSQL│    │   Redis   │    │ SMTP/Whats│
│  │  (Users)  │    │ (Sessions)│    │   App API │
│  └───────────┘    └───────────┘    └───────────┘
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Database Schema

### Users Table
```sql
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    username        VARCHAR(50) NOT NULL UNIQUE,
    full_name       VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    phone           VARCHAR(20),
    address         TEXT,
    
    -- Status
    is_active           BOOLEAN DEFAULT TRUE,
    is_admin            BOOLEAN DEFAULT FALSE,
    email_verified      BOOLEAN DEFAULT FALSE,
    phone_verified      BOOLEAN DEFAULT FALSE,
    
    -- Security
    failed_login_attempts   INTEGER DEFAULT 0,
    locked_until           TIMESTAMP,
    
    -- Timestamps
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login  TIMESTAMP,
    
    CONSTRAINT users_email_check 
        CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);
```

### OTPs Table
```sql
CREATE TABLE otps (
    id SERIAL PRIMARY KEY,
    otp_code VARCHAR(10) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    otp_type VARCHAR(20) NOT NULL,      -- email_verification, phone_verification, password_reset
    purpose VARCHAR(50) NOT NULL,        -- verify, reset
    is_used BOOLEAN DEFAULT FALSE,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);
```

### Sessions Table (Optional - Redis preferred)
```sql
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    user_agent TEXT,
    ip_address VARCHAR(45),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/auth/register` | Register new user | No |
| POST | `/api/v1/auth/login` | Login, returns cookies | No |
| POST | `/api/v1/auth/refresh` | Refresh session | No (cookie) |
| POST | `/api/v1/auth/logout` | Logout, clear cookies | Yes |
| POST | `/api/v1/auth/logout-all` | Logout all devices | Yes |
| POST | `/api/v1/auth/change-password` | Change password | Yes |
| POST | `/api/v1/auth/send-otp` | Send OTP (email/WhatsApp) | No |
| POST | `/api/v1/auth/verify-otp` | Verify OTP | No |
| POST | `/api/v1/auth/resend-otp` | Resend OTP | No |

### User Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/users/me` | Get current user | Required |
| PATCH | `/api/v1/users/me` | Update profile | Required |
| GET | `/api/v1/users/{id}` | Get user by ID | Required |
| GET | `/api/v1/admin/users` | List all users | Admin |
| PATCH | `/api/v1/admin/users/{id}/activate` | Activate user | Admin |
| PATCH | `/api/v1/admin/users/{id}/deactivate` | Deactivate user | Admin |

---

## 4. Request/Response Flow

### 4.1 User Registration with OTP Verification

**Frontend Request:**
```javascript
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "john@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "password": "SecurePass123",
  "confirm_password": "SecurePass123",
  "phone": "+1234567890",
  "address": "123 Main St"
}
```

**Backend Processing:**
```
1. Receive request
2. Validate request body (Pydantic)
3. Check email uniqueness
4. Check username uniqueness
5. Validate password strength
6. Hash password
7. Create user (is_active=false initially)
8. Send OTP via email
9. Return pending verification status
```

**Backend Response:**
```json
{
  "id": 1,
  "email": "john@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "is_active": false,
  "email_verified": false,
  "message": "Registration successful. Please verify your email with OTP sent to john@example.com"
}
```

### 4.2 OTP Verification Flow

**Step 1: Send OTP**
```javascript
POST /api/v1/auth/send-otp
Content-Type: application/json

{
  "email": "john@example.com",
  "otp_type": "email_verification",
  "purpose": "verify",
  "user_id": 1
}
```

**Response:**
```json
{
  "message": "OTP sent successfully",
  "otp_type": "email_verification",
  "destination": "j***@example.com",
  "expires_in": 600,
  "remaining_attempts": 3,
  "next_resend_available": 60
}
```

**Step 2: Verify OTP**
```javascript
POST /api/v1/auth/verify-otp
Content-Type: application/json

{
  "otp_code": "123456",
  "email": "john@example.com",
  "otp_type": "email_verification",
  "purpose": "verify"
}
```

**Response:**
```json
{
  "valid": true,
  "message": "OTP verified successfully",
  "user_id": 1,
  "is_verified": true
}
```

### 4.3 Login with 24-Hour Cookie Session

**Frontend Request:**
```javascript
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "johndoe",
  "password": "SecurePass123",
  "remember_me": true
}
```

**Backend Processing:**
```
1. Validate credentials
2. Check rate limiting (Redis)
3. Verify password
4. Check account lockout
5. Reset failed attempts
6. Generate JWT access token (30 min)
7. Generate refresh token (24 hours if remember_me=true)
8. Store session in Redis
9. Set HTTP-Only cookies
10. Return user data
```

**Backend Response (Cookies Set):**
```
Set-Cookie: access_token=eyJ...; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=1800
Set-Cookie: refresh_token=eyJ...; HttpOnly; Secure; SameSite=Lax; Path=/auth/refresh; Max-Age=86400
Set-Cookie: session_id=abc123; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=86400

{
  "user": {
    "id": 1,
    "email": "john@example.com",
    "username": "johndoe",
    "full_name": "John Doe",
    "is_active": true,
    "is_admin": false,
    "email_verified": true
  },
  "session": {
    "id": "abc123",
    "expires_in": 86400,
    "token_type": "24-hour session"
  }
}
```

---

## 5. Token Management

### Token Types

| Token | Lifetime | Storage | Purpose |
|-------|----------|---------|---------|
| Access Token | 30 min | HTTP-Only Cookie | API requests |
| Refresh Token | 24 hours | HTTP-Only Cookie | Session refresh |
| Session ID | 24 hours | HTTP-Only Cookie + Redis | Session validation |

### JWT Token Structure

```
Access Token Payload:
{
  "sub": "john@example.com",   // User email
  "exp": 1705326600,          // Expiration timestamp
  "type": "access",            // Token type
  "iat": 1705324800,          // Issued at
  "jti": "token_unique_id"   // Token ID
}

Refresh Token Payload:
{
  "sub": "1",                 // User ID
  "exp": 1705931400,          // 24 hours
  "type": "refresh",
  "jti": "refresh_unique_id",
  "session_id": "abc123"
}
```

### Cookie Configuration

```python
# Cookie settings for production
COOKIE_SETTINGS = {
    "access_token": {
        "name": "access_token",
        "max_age": 1800,          # 30 minutes
        "httponly": True,
        "secure": True,           # HTTPS only
        "samesite": "lax",
        "path": "/"
    },
    "refresh_token": {
        "name": "refresh_token",
        "max_age": 86400,         # 24 hours
        "httponly": True,
        "secure": True,
        "samesite": "lax",
        "path": "/api/v1/auth/refresh"
    },
    "session_id": {
        "name": "session_id",
        "max_age": 86400,         # 24 hours
        "httponly": True,
        "secure": True,
        "samesite": "lax",
        "path": "/"
    }
}
```

### Redis Session Storage

```
Key: session:{session_id}
Value: {
  "user_id": 1,
  "email": "john@example.com",
  "username": "johndoe",
  "is_admin": false,
  "created_at": "2024-01-15T10:30:00Z",
  "expires_at": "2024-01-16T10:30:00Z",
  "last_activity": "2024-01-15T11:00:00Z",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}
TTL: 86400 seconds (24 hours)
```

---

## 6. OTP Verification (Email & WhatsApp)

### OTP Types

| Type | Purpose | Delivery |
|------|---------|----------|
| email_verification | Verify email address | Email / WhatsApp |
| phone_verification | Verify phone number | WhatsApp |
| password_reset | Reset forgotten password | Email / WhatsApp |

### OTP Flow

```
User Registration
        │
        ▼
    Create User (inactive)
        │
        ▼
    Send OTP (email_verification)
        │
        ▼
    User enters OTP
        │
        ├──── Valid ──► Activate user, set email_verified=true
        │
        └──── Invalid ──► Show error, remaining attempts--
        │
        ▼
    Max attempts exceeded? ──► Lock OTP, require resend
```

### WhatsApp Integration

```python
# WhatsApp OTP message template
WHATSAPP_TEMPLATES = {
    "verification": (
        "Aarya Clothing: Your verification code is *{otp_code}*. "
        "This code expires in {expires_minutes} minutes. "
        "Don't share this with anyone."
    ),
    "password_reset": (
        "Aarya Clothing: Your password reset code is *{otp_code}*. "
        "This code expires in {expires_minutes} minutes. "
        "If you didn't request this, ignore this message."
    )
}

# Send via Twilio
from twilio.rest import Client

def send_whatsapp_otp(phone: str, otp_code: str, purpose: str):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    message = WHATSAPP_TEMPLATES[purpose].format(
        otp_code=otp_code,
        expires_minutes=10
    )
    
    message = client.messages.create(
        from_=TWILIO_WHATSAPP_NUMBER,
        body=message,
        to=f"whatsapp:{phone}"
    )
```

---

## 7. Cookie-Based Sessions

### Login Flow with Cookies

```javascript
// Frontend login
async function login(username, password, rememberMe = true) {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, remember_me: rememberMe })
  });

  // Cookies are automatically set by the server
  // No manual token storage needed
  
  if (response.ok) {
    const data = await response.json();
    return data.user; // User is logged in!
  }
}

// Subsequent requests - cookies sent automatically
async function getUserProfile() {
  const response = await fetch('/api/v1/users/me');
  // Cookies are automatically included
  return response.json();
}
```

### Server-Side Cookie Setting

```python
from fastapi import Response

@app.post("/api/v1/auth/login")
async def login(response: Response, ...):
    # Generate tokens
    access_token = create_access_token(...)
    refresh_token = create_refresh_token(...)
    session_id = create_session_id(...)
    
    # Set cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=1800,  # 30 minutes
        path="/"
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=86400,  # 24 hours
        path="/api/v1/auth/refresh"
    )
    
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=86400,  # 24 hours
        path="/"
    )
    
    return {"user": user, "message": "Login successful"}
```

### Logout (Clear Cookies)

```python
@app.post("/api/v1/auth/logout")
async def logout(response: Response):
    # Clear all auth cookies
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/v1/auth/refresh")
    response.delete_cookie("session_id", path="/")
    
    # Optionally revoke session in Redis
    session_id = request.cookies.get("session_id")
    redis_client.delete(f"session:{session_id}")
    
    return {"message": "Logged out successfully"}
```

### Session Refresh (Automatic)

```python
@app.post("/api/v1/auth/refresh")
async def refresh_token(response: Response, refresh_token: str = Cookie(...)):
    # Validate refresh token
    payload = decode_token(refresh_token)
    user_id = payload["sub"]
    session_id = payload["session_id"]
    
    # Verify session is still valid in Redis
    session = redis_client.get(f"session:{session_id}")
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Generate new access token
    new_access_token = create_access_token({"sub": session["email"]})
    
    # Set new access token cookie
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=1800,
        path="/"
    )
    
    return {"message": "Token refreshed"}
```

---

## 8. Frontend Integration

### 8.1 API Client with Automatic Cookie Handling

```javascript
// lib/api.js
class ApiClient {
  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
  }

  // Login - cookies handled automatically
  async login(username, password, rememberMe = true) {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, remember_me: rememberMe }),
      credentials: 'include'  // Important: include cookies
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    // User is now logged in - cookies are set automatically
    return response.json();
  }

  // Logout - clears cookies
  async logout() {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/logout`, {
      method: 'POST',
      credentials: 'include'
    });

    if (response.ok) {
      // Cookies cleared automatically
    }
  }

  // Get current user - cookies sent automatically
  async getCurrentUser() {
    const response = await fetch(`${this.baseUrl}/api/v1/users/me`, {
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error('Not authenticated');
    }

    return response.json();
  }

  // Check if logged in
  async isLoggedIn() {
    try {
      await this.getCurrentUser();
      return true;
    } catch {
      return false;
    }
  }

  // Send OTP
  async sendOTP(email, otpType, purpose, userId) {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/send-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, otp_type: otpType, purpose, user_id: userId }),
      credentials: 'include'
    });
    return response.json();
  }

  // Verify OTP
  async verifyOTP(otpCode, email, otpType, purpose) {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/verify-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ otp_code: otpCode, email, otp_type: otpType, purpose }),
      credentials: 'include'
    });
    return response.json();
  }
}

export const api = new ApiClient();
```

### 8.2 React Auth Context

```javascript
// contexts/AuthContext.js
'use client';

import { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../lib/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check auth status on mount
    const checkAuth = async () => {
      try {
        const userData = await api.getCurrentUser();
        setUser(userData);
      } catch (error) {
        setUser(null);
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (username, password, rememberMe = true) => {
    const result = await api.login(username, password, rememberMe);
    setUser(result.user);
    return result;
  };

  const logout = async () => {
    await api.logout();
    setUser(null);
  };

  const sendOTP = async (email, otpType, purpose, userId) => {
    return api.sendOTP(email, otpType, purpose, userId);
  };

  const verifyOTP = async (otpCode, email, otpType, purpose) => {
    return api.verifyOTP(otpCode, email, otpType, purpose);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, sendOTP, verifyOTP, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
```

### 8.3 Registration with OTP Flow

```javascript
// RegistrationPage.js
'use client';

import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function RegistrationPage() {
  const { sendOTP, verifyOTP } = useAuth();
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({});
  const [otpCode, setOtpCode] = useState('');
  
  const handleRegister = async (data) => {
    setFormData(data);
    
    // Register user
    const response = await fetch('/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    if (response.ok) {
      const user = await response.json();
      // Send OTP for verification
      await sendOTP(data.email, 'email_verification', 'verify', user.id);
      setStep(2);
    }
  };
  
  const handleVerifyOTP = async () => {
    const result = await verifyOTP(
      otpCode,
      formData.email,
      'email_verification',
      'verify'
    );
    
    if (result.valid) {
      setStep(3); // Success!
    }
  };

  return (
    <div>
      {step === 1 && (
        <RegistrationForm onSubmit={handleRegister} />
      )}
      
      {step === 2 && (
        <OTPVerificationForm 
          destination={formData.email}
          onVerify={handleVerifyOTP}
          onResend={() => sendOTP(
            formData.email, 
            'email_verification', 
            'verify', 
            formData.id
          )}
        />
      )}
      
      {step === 3 && (
        <SuccessMessage />
      )}
    </div>
  );
}
```

---

## 9. Security Measures

### 9.1 Password Security

| Rule | Requirement |
|------|-------------|
| Minimum Length | 8 characters |
| Uppercase | At least 1 |
| Lowercase | At least 1 |
| Number | At least 1 |
| Hashing | bcrypt (cost factor 12) |

### 9.2 Cookie Security

```python
# Production cookie settings
SECURE_COOKIE_CONFIG = {
    "httponly": True,      # JavaScript cannot access
    "secure": True,        # HTTPS only
    "samesite": "lax",     # CSRF protection
    "path": "/",           # Available on all paths
    "max_age": 86400       # 24 hours
}
```

### 9.3 Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/login` | 5 attempts | 5 minutes |
| `/send-otp` | 5 attempts | 1 hour |
| `/verify-otp` | 3 attempts | Per OTP |
| `/register` | 10 attempts | 1 hour |

### 9.4 Account Lockout

```
Failed Attempts ─────► Lockout Duration
─────────────────────────────────────
5 attempts      ─────► 30 minutes
10 attempts     ─────► 1 hour
```

### 9.5 Session Security

- Session ID stored in both cookie and Redis
- Session validated on every API request
- Session automatically refreshed on activity
- Logout from all devices supported
- Session expires after 24 hours of inactivity

---

## 10. Complete Request Examples

### 10.1 Full Registration + OTP Flow

```bash
# Step 1: Register
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "username": "johndoe",
    "full_name": "John Doe",
    "password": "SecurePass123",
    "confirm_password": "SecurePass123"
  }'

# Step 2: Send OTP
curl -X POST http://localhost:8001/api/v1/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "otp_type": "email_verification",
    "purpose": "verify",
    "user_id": 1
  }'

# Step 3: Verify OTP
curl -X POST http://localhost:8001/api/v1/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "otp_code": "123456",
    "email": "john@example.com",
    "otp_type": "email_verification",
    "purpose": "verify"
  }'

# Step 4: Login (cookies set)
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "username": "johndoe",
    "password": "SecurePass123",
    "remember_me": true
  }'

# Step 5: Access protected route (cookies sent)
curl -X GET http://localhost:8001/api/v1/users/me \
  -b cookies.txt
```

### 10.2 Cookie-Based Session Test

```javascript
// Test with curl showing cookies
// 1. Login
curl -v -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"johndoe","password":"SecurePass123","remember_me":true}' \
  -c cookies.txt

# Response shows:
# Set-Cookie: access_token=eyJ...; HttpOnly; Secure; Max-Age=1800
# Set-Cookie: refresh_token=eyJ...; HttpOnly; Secure; Max-Age=86400
# Set-Cookie: session_id=abc123; HttpOnly; Secure; Max-Age=86400

# 2. Access protected route (cookies sent automatically)
curl -X GET http://localhost:8001/api/v1/users/me -b cookies.txt

# 3. Refresh token (only refresh_token cookie sent)
curl -X POST http://localhost:8001/api/v1/auth/refresh -b cookies.txt

# 4. Logout (all cookies cleared)
curl -X POST http://localhost:8001/api/v1/auth/logout -b cookies.txt -c cookies.txt
```

---

## Summary

✅ **User Registration** - With email/password
✅ **OTP Verification** - Email or WhatsApp (user's choice)
✅ **JWT Tokens** - 30-minute access token
✅ **Cookie Sessions** - 24-hour persistent login
✅ **Refresh Tokens** - Automatic session renewal
✅ **Rate Limiting** - Protection against abuse
✅ **Account Lockout** - Security after failed attempts
✅ **Session Management** - Redis-backed sessions
✅ **Full Frontend Integration** - React Context + API client
