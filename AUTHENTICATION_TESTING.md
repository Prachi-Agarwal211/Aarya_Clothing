# Authentication Testing Guide

## Overview
This guide provides comprehensive testing scenarios for the Aarya Clothing authentication system. All services are now running successfully with Docker.

## Current Service Status 
- **Core Service**:  Running on http://localhost:8001
- **Commerce Service**:  Running on http://localhost:8010
- **Payment Service**:  Running on http://localhost:8020
- **PostgreSQL**:  Running on localhost:5432
- **Redis**:  Running on localhost:6379

## Prerequisites

1. **Core Service Running**: http://localhost:8001
2. **Database Ready**: PostgreSQL and Redis containers running
3. **Testing Tool**: curl, Postman, or any HTTP client

## Health Check

```bash
curl http://localhost:8001/health
```

Expected Response:
```json
{
  "status": "healthy",
  "service": "core-platform",
  "version": "1.0.0",
  "timestamp": "2025-02-08T10:00:00Z",
  "dependencies": {
    "redis": "healthy",
    "database": "healthy"
  }
}
```

## Test Scenarios

### 1. User Registration

#### Valid Registration
```bash
curl -X POST "http://localhost:8001/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "password": "TestPassword123!"
  }'
```

Expected Response (201):
```json
{
  "id": 1,
  "email": "testuser@example.com",
  "username": "testuser",
  "full_name": "Test User",
  "role": "customer",
  "is_active": true,
  "email_verified": false,
  "phone_verified": false,
  "created_at": "2025-02-08T10:00:00Z",
  "updated_at": "2025-02-08T10:00:00Z"
}
```

#### Invalid Registration Tests

**Weak Password**:
```bash
curl -X POST "http://localhost:8001/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "weak@example.com",
    "username": "weakuser",
    "full_name": "Weak User",
    "password": "123"
  }'
```

Expected Response (400):
```json
{
  "detail": "Password must be at least 8 characters; Password must contain at least one uppercase letter; Password must contain at least one number"
}
```

**Duplicate Email**:
```bash
curl -X POST "http://localhost:8001/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "username": "duplicate",
    "full_name": "Duplicate User",
    "password": "TestPassword123!"
  }'
```

Expected Response (400):
```json
{
  "detail": "User with this email or username already exists"
}
```

### 2. User Login

#### Successful Login
```bash
curl -X POST "http://localhost:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "username": "testuser",
    "password": "TestPassword123!",
    "remember_me": true
  }'
```

Expected Response (200):
```json
{
  "user": {
    "id": 1,
    "email": "testuser@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "role": "customer",
    "is_active": true,
    "email_verified": false,
    "phone_verified": false
  },
  "tokens": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer"
  },
  "session_id": "sess_1234567890abcdef"
}
```

#### Invalid Login Tests

**Wrong Password**:
```bash
curl -X POST "http://localhost:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "WrongPassword!",
    "remember_me": false
  }'
```

Expected Response (401):
```json
{
  "detail": "Invalid credentials"
}
```

**Non-existent User**:
```bash
curl -X POST "http://localhost:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "nonexistent",
    "password": "TestPassword123!",
    "remember_me": false
  }'
```

Expected Response (401):
```json
{
  "detail": "Invalid credentials"
}
```

### 3. Get Current User

#### Authenticated Request
```bash
curl -X GET "http://localhost:8001/api/v1/users/me" \
  -H "Content-Type: application/json" \
  -b cookies.txt
```

Expected Response (200):
```json
{
  "id": 1,
  "email": "testuser@example.com",
  "username": "testuser",
  "full_name": "Test User",
  "role": "customer",
  "is_active": true,
  "email_verified": false,
  "phone_verified": false,
  "created_at": "2025-02-08T10:00:00Z",
  "updated_at": "2025-02-08T10:00:00Z",
  "last_login": "2025-02-08T10:05:00Z"
}
```

#### Unauthenticated Request
```bash
curl -X GET "http://localhost:8001/api/v1/users/me" \
  -H "Content-Type: application/json"
```

Expected Response (401):
```json
{
  "detail": "Not authenticated"
}
```

### 4. Token Refresh

#### Successful Refresh
```bash
curl -X POST "http://localhost:8001/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -c cookies.txt
```

Expected Response (200):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

#### Invalid Refresh Token
```bash
curl -X POST "http://localhost:8001/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer invalid_token"
```

Expected Response (401):
```json
{
  "detail": "Refresh token not found"
}
```

### 5. Update User Profile

#### Successful Update
```bash
curl -X PATCH "http://localhost:8001/api/v1/users/me" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "full_name": "Updated Name",
    "phone": "+1234567890"
  }'
```

Expected Response (200):
```json
{
  "id": 1,
  "email": "testuser@example.com",
  "username": "testuser",
  "full_name": "Updated Name",
  "phone": "+1234567890",
  "role": "customer",
  "is_active": true,
  "email_verified": false,
  "phone_verified": false,
  "updated_at": "2025-02-08T10:10:00Z"
}
```

### 6. Change Password

#### Successful Password Change
```bash
curl -X POST "http://localhost:8001/api/v1/auth/change-password" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "current_password": "TestPassword123!",
    "new_password": "NewPassword456!"
  }'
```

Expected Response (200):
```json
{
  "detail": "Password changed successfully"
}
```

#### Wrong Current Password
```bash
curl -X POST "http://localhost:8001/api/v1/auth/change-password" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "current_password": "WrongPassword!",
    "new_password": "NewPassword456!"
  }'
```

Expected Response (400):
```json
{
  "detail": "Current password is incorrect"
}
```

### 7. Logout

#### Successful Logout
```bash
curl -X POST "http://localhost:8001/api/v1/auth/logout" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -c cookies.txt
```

Expected Response (200):
```json
{
  "detail": "Successfully logged out"
}
```

#### Verify Logout
```bash
curl -X GET "http://localhost:8001/api/v1/users/me" \
  -H "Content-Type: application/json" \
  -b cookies.txt
```

Expected Response (401):
```json
{
  "detail": "Not authenticated"
}
```

### 8. Admin User Tests

#### Login as Admin
```bash
curl -X POST "http://localhost:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -c admin_cookies.txt \
  -d '{
    "username": "admin",
    "password": "admin123",
    "remember_me": false
  }'
```

#### List All Users (Admin Only)
```bash
curl -X GET "http://localhost:8001/api/v1/admin/users" \
  -H "Content-Type: application/json" \
  -b admin_cookies.txt
```

Expected Response (200):
```json
[
  {
    "id": 1,
    "email": "admin@aarya.com",
    "username": "admin",
    "full_name": "System Administrator",
    "role": "admin",
    "is_active": true,
    "email_verified": false,
    "phone_verified": false
  },
  {
    "id": 2,
    "email": "testuser@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "role": "customer",
    "is_active": true,
    "email_verified": false,
    "phone_verified": false
  }
]
```

## Security Tests

### 1. Rate Limiting
```bash
# Try multiple failed logins quickly
for i in {1..6}; do
  curl -X POST "http://localhost:8001/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
      "username": "testuser",
      "password": "WrongPassword'$i'",
      "remember_me": false
    }'
  echo ""
done
```

After 5 failed attempts, the account should be locked.

### 2. SQL Injection Protection
```bash
curl -X POST "http://localhost:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin'; DROP TABLE users; --",
    "password": "anything",
    "remember_me": false
  }'
```

Should return 401, not a database error.

### 3. XSS Protection
```bash
curl -X POST "http://localhost:8001/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "<script>alert(1)</script>",
    "full_name": "Test User",
    "password": "TestPassword123!"
  }'
```

Should sanitize or reject malicious input.

## Performance Tests

### 1. Concurrent Login Requests
Use a tool like Apache Bench (ab) or wrk to test concurrent requests:

```bash
ab -n 100 -c 10 -H "Content-Type: application/json" \
   -p login_data.json http://localhost:8001/api/v1/auth/login
```

### 2. Token Validation Performance
```bash
# Test token validation speed
time curl -X GET "http://localhost:8001/api/v1/users/me" \
  -H "Content-Type: application/json" \
  -b cookies.txt
```

## Automated Testing Script

Create a test script `test_auth.sh`:

```bash
#!/bin/bash

# Authentication Test Script
BASE_URL="http://localhost:8001"
COOKIE_FILE="test_cookies.txt"

echo "Starting Authentication Tests..."

# Test 1: Health Check
echo "1. Testing health check..."
curl -s "$BASE_URL/health" | jq .

# Test 2: Registration
echo "2. Testing user registration..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "password": "TestPassword123!"
  }')

echo "$REGISTER_RESPONSE" | jq .

# Test 3: Login
echo "3. Testing user login..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -c "$COOKIE_FILE" \
  -d '{
    "username": "testuser",
    "password": "TestPassword123!",
    "remember_me": true
  }')

echo "$LOGIN_RESPONSE" | jq .

# Test 4: Get Current User
echo "4. Testing get current user..."
curl -s -X GET "$BASE_URL/api/v1/users/me" \
  -H "Content-Type: application/json" \
  -b "$COOKIE_FILE" | jq .

# Test 5: Logout
echo "5. Testing logout..."
curl -s -X POST "$BASE_URL/api/v1/auth/logout" \
  -H "Content-Type: application/json" \
  -b "$COOKIE_FILE" \
  -c "$COOKIE_FILE"

# Test 6: Verify Logout
echo "6. Verifying logout..."
curl -s -X GET "$BASE_URL/api/v1/users/me" \
  -H "Content-Type: application/json" \
  -b "$COOKIE_FILE" | jq .

# Cleanup
rm -f "$COOKIE_FILE"

echo "Authentication tests completed!"
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL container is running
   - Check DATABASE_URL in .env file
   - Verify database exists: `docker-compose exec postgres psql -U postgres -d aarya_clothing`

2. **Redis Connection Error**
   - Ensure Redis container is running
   - Check REDIS_URL in .env file
   - Test Redis: `docker-compose exec redis redis-cli ping`

3. **Token Validation Errors**
   - Check JWT_SECRET_KEY in .env file
   - Verify system time is correct
   - Clear browser cookies and re-login

4. **CORS Issues**
   - Check ALLOWED_ORIGINS in .env file
   - Ensure frontend URL is included

### Debug Commands

```bash
# Check service logs
docker-compose logs -f postgres redis

# Check database tables
docker-compose exec postgres psql -U postgres -d aarya_clothing -c "\dt"

# Check Redis keys
docker-compose exec redis redis-cli keys "*"

# Test database connection
docker-compose exec postgres psql -U postgres -d aarya_clothing -c "SELECT COUNT(*) FROM users;"
```

## Success Criteria

All tests should pass with the following results:

1. ✅ Health check returns healthy status
2. ✅ User registration creates new user
3. ✅ Login returns tokens and sets cookies
4. ✅ Protected endpoints require authentication
5. ✅ Token refresh works correctly
6. ✅ Logout invalidates tokens
7. ✅ Password validation works
8. ✅ Rate limiting prevents brute force
9. ✅ Admin endpoints require admin role
10. ✅ Input validation prevents malicious data

---

**Last Updated**: February 2025  
**Version**: 1.0.0
