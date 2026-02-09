# Dual Login System Documentation

## Overview

The Aarya Clothing authentication system supports **both email and username** for login, providing maximum flexibility for users while maintaining security and proper session management.

## Architecture

### Backend Implementation

#### 1. Authentication Service (`services/core/service/auth_service.py`)

```python
def authenticate_user(self, username: str, password: str) -> Optional[User]:
    """Authenticate a user using either email or username."""
    user = self.get_user_by_email(username) or self.get_user_by_username(username)
    
    if not user:
        return None
    
    if not self.verify_password(password, user.hashed_password):
        return None
    
    if not user.is_active:
        return None
    
    return user
```

**Key Features:**
- **Dual Lookup**: Checks both email and username fields
- **Fallback Logic**: Tries email first, then username
- **Security**: Proper password verification and active status check

#### 2. Database Model (`services/core/models/user.py`)

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    # ... other fields
```

**Key Features:**
- **Unique Constraints**: Both email and username are unique
- **Indexing**: Both fields are indexed for fast lookups
- **Validation**: Database-level uniqueness enforcement

#### 3. Redis Integration (`services/core/core/redis_client.py`)

```python
def create_session(self, session_id: str, user_id: int, ...):
    """Create a new session with Redis storage."""
    session_data = {
        "user_id": user_id,
        "user_agent": user_agent,
        "ip_address": ip_address,
        "created_at": datetime.utcnow().isoformat(),
        "last_activity": datetime.utcnow().isoformat()
    }
    
    self.client.setex(f"session:{session_id}", expires_in * 60, json.dumps(session_data))
    self.client.sadd(f"user_sessions:{user_id}", session_id)
```

**Key Features:**
- **Session Storage**: HTTP-only cookies with Redis backend
- **User Mapping**: Tracks sessions per user
- **Rate Limiting**: Login attempt tracking

### Frontend Implementation

#### 1. Login Form (`frontend/src/app/login/page.tsx`)

```typescript
const handleLogin = async (e: React.FormEvent) => {
  const username = formData.get('email') as string; // Can be email or username
  
  // Enhanced validation
  if (username.includes('@')) {
    // Email validation
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(username)) {
      setLoginError('Please enter a valid email address.');
      return;
    }
  } else {
    // Username validation
    if (username.length < 3) {
      setLoginError('Username must be at least 3 characters long.');
      return;
    }
  }
  
  const result = await login(username, password, rememberMe);
};
```

**Key Features:**
- **Smart Validation**: Detects email vs username format
- **Unified Input**: Single field accepts both types
- **Real-time Feedback**: Specific validation messages

#### 2. API Integration (`frontend/src/lib/auth.ts`)

```typescript
export const login = async (username: string, password: string, rememberMe: boolean = false) => {
  try {
    const response = await api.post<LoginResponse>('/api/v1/auth/login', {
      username, // Can be email or username
      password,
      remember_me: rememberMe
    });
    return { success: true };
  } catch (error) {
    return { success: false, message: getErrorMessage(error) };
  }
};
```

**Key Features:**
- **Single Endpoint**: `/api/v1/auth/login` handles both
- **Type Safety**: Proper TypeScript interfaces
- **Error Handling**: Comprehensive error management

## API Endpoints

### Login Endpoint
```
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",  // OR "username123"
  "password": "UserPassword123",
  "remember_me": false
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username123",
    "full_name": "John Doe",
    "role": "customer",
    "is_active": true,
    "email_verified": false,
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-01T12:00:00Z"
  },
  "tokens": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800
  },
  "session_id": "abc123def456"
}
```

## Security Features

### 1. Rate Limiting
- **Login Attempts**: 5 attempts per 5 minutes
- **OTP Requests**: 5 requests per hour
- **Password Reset**: 3 requests per hour

### 2. Account Lockout
- **Failed Attempts**: 5 failed attempts trigger lockout
- **Lock Duration**: 30 minutes
- **Auto-Reset**: Successful login resets counter

### 3. Session Management
- **HTTP-Only Cookies**: Prevents XSS attacks
- **Secure Flag**: HTTPS only in production
- **Session Expiry**: 24 hours by default
- **Multi-Device Support**: Multiple concurrent sessions

### 4. Password Security
- **Hashing**: bcrypt with salt
- **Validation**: 8+ chars, uppercase, lowercase, number
- **Strength Requirements**: Enforced at registration

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    role VARCHAR(20) DEFAULT 'customer',
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_active ON users(is_active);
```

## Redis Keys

### Session Storage
- `session:{session_id}`: Session data (JSON)
- `user_sessions:{user_id}`: Set of user's session IDs

### Rate Limiting
- `ratelimit:login:{identifier}`: Login attempt counter
- `ratelimit:otp_send:{identifier}`: OTP send counter

### OTP Storage
- `otp:{type}:{identifier}`: OTP code
- `otp_attempts:{type}:{identifier}`: Failed OTP attempts

## Testing

### Automated Tests
```bash
# Test dual login functionality
./test-dual-login.sh

# Test complete authentication system
./test-auth-all-fixes.sh

# Test OTP functionality
./test-otp-complete.sh
```

### Manual Testing Checklist
1. **Email Login**: Test with valid email address
2. **Username Login**: Test with valid username
3. **Invalid Email**: Test with malformed email
4. **Invalid Username**: Test with short/invalid username
5. **Wrong Password**: Test authentication failure
6. **Non-existent User**: Test with unknown credentials
7. **Session Persistence**: Test cookie-based sessions
8. **Logout**: Test session termination

## Error Handling

### Frontend Errors
- **Validation Errors**: Real-time form validation
- **Network Errors**: API failure handling
- **Authentication Errors**: Clear user feedback

### Backend Errors
- **Invalid Credentials**: HTTP 400 with specific message
- **Account Locked**: HTTP 400 with lockout duration
- **Rate Limited**: HTTP 429 with retry information
- **Server Errors**: HTTP 500 with generic message

## Performance Considerations

### Database Optimization
- **Indexes**: Email and username fields indexed
- **Unique Constraints**: Database-level validation
- **Query Optimization**: Efficient lookups

### Redis Optimization
- **Session Expiry**: Automatic cleanup
- **Rate Limiting**: Efficient counters
- **Memory Management**: TTL-based expiration

### Frontend Optimization
- **Debounced Validation**: Prevent excessive API calls
- **Loading States**: User feedback during operations
- **Error Caching**: Avoid repeated failed attempts

## Troubleshooting

### Common Issues

1. **Login Not Working**
   - Check if user exists in database
   - Verify password hash
   - Check Redis connection

2. **Session Not Persisting**
   - Verify cookie settings
   - Check Redis storage
   - Validate session expiry

3. **Rate Limiting Too Strict**
   - Adjust limits in configuration
   - Check Redis key expiration
   - Verify user identification

### Debug Commands
```bash
# Check Redis sessions
docker-compose exec redis redis-cli keys "session:*"

# Check user data
docker-compose exec postgres psql -U postgres -d aarya_clothing -c "SELECT id, email, username, is_active FROM users;"

# Check service logs
docker-compose logs core | grep -i "login\|auth"
```

## Future Enhancements

### Planned Features
1. **Social Login**: OAuth providers (Google, Facebook)
2. **Two-Factor Auth**: TOTP integration
3. **Biometric Auth**: WebAuthn support
4. **Audit Logging**: Comprehensive security logs
5. **Advanced Rate Limiting**: User-based limits

### Scalability Considerations
- **Database Sharding**: User data distribution
- **Redis Cluster**: Session storage scaling
- **Load Balancing**: Multiple service instances
- **CDN Integration**: Global performance

---

## Summary

The dual login system provides a robust, secure, and flexible authentication solution that supports both email and username login methods. The implementation includes comprehensive security measures, proper session management, and excellent user experience.

**Key Benefits:**
- ✅ **Flexibility**: Users choose their preferred login method
- ✅ **Security**: Multiple layers of protection
- ✅ **Performance**: Optimized database and Redis queries
- ✅ **Scalability**: Designed for high-traffic applications
- ✅ **Maintainability**: Clean, well-documented code

The system is production-ready and can handle enterprise-scale authentication requirements.
