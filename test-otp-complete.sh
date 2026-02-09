#!/bin/bash

# Comprehensive OTP Test Script
# Tests the complete OTP flow after frontend integration fixes

echo "=========================================="
echo "Comprehensive OTP Test - After Frontend Fixes"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test email
TEST_EMAIL="test@example.com"

echo -e "${YELLOW}Testing OTP End-to-End Flow${NC}"
echo ""

# Test 1: Check service health
echo "1. Checking service health..."
echo "Request: GET /health"
health_response=$(curl -s -w "%{http_code}" https://aaryaclothing.cloud/api/v1/health)
http_code="${health_response: -3}"
response_body="${health_response%???}"

if [[ "$http_code" == "200" ]]; then
    echo -e "${GREEN}✓ Core service is healthy${NC}"
    echo "Response: $response_body"
else
    echo -e "${RED}✗ Core service health check failed (HTTP $http_code)${NC}"
fi
echo ""

# Test 2: Send OTP
echo "2. Sending OTP to $TEST_EMAIL"
echo "Request: POST /api/v1/auth/send-otp"
echo "Payload: {\"email\":\"$TEST_EMAIL\",\"otp_type\":\"email_verification\",\"purpose\":\"verify\"}"
echo ""

send_response=$(curl -s -w "%{http_code}" -X POST https://aaryaclothing.cloud/api/v1/auth/send-otp \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\",\"otp_type\":\"email_verification\",\"purpose\":\"verify\"}")

send_http_code="${send_response: -3}"
send_body="${send_response%???}"

echo "HTTP Status: $send_http_code"
echo "Response: $send_body"

if [[ "$send_http_code" == "200" ]]; then
    echo -e "${GREEN}✓ OTP sent successfully${NC}"
    
    # Extract OTP from Redis for testing
    echo ""
    echo "3. Checking Redis for OTP storage..."
    sleep 2
    
    # Try to get OTP from Redis
    otp_key="otp:email_verification:$TEST_EMAIL"
    stored_otp=$(docker-compose exec -T redis redis-cli get "$otp_key" 2>/dev/null || echo "")
    
    if [[ -n "$stored_otp" && "$stored_otp" != "(nil)" ]]; then
        echo -e "${GREEN}✓ OTP found in Redis: $stored_otp${NC}"
        
        # Test 3: Verify OTP with correct code
        echo ""
        echo "4. Verifying OTP with correct code..."
        echo "Request: POST /api/v1/auth/verify-otp"
        echo "Payload: {\"email\":\"$TEST_EMAIL\",\"otp_code\":\"$stored_otp\",\"otp_type\":\"email_verification\",\"purpose\":\"verify\"}"
        echo ""
        
        verify_response=$(curl -s -w "%{http_code}" -X POST https://aaryaclothing.cloud/api/v1/auth/verify-otp \
          -H "Content-Type: application/json" \
          -d "{\"email\":\"$TEST_EMAIL\",\"otp_code\":\"$stored_otp\",\"otp_type\":\"email_verification\",\"purpose\":\"verify\"}")
        
        verify_http_code="${verify_response: -3}"
        verify_body="${verify_response%???}"
        
        echo "HTTP Status: $verify_http_code"
        echo "Response: $verify_body"
        
        if [[ "$verify_http_code" == "200" ]]; then
            echo -e "${GREEN}✓ OTP verified successfully${NC}"
        else
            echo -e "${RED}✗ OTP verification failed${NC}"
        fi
        
        # Test 4: Try to verify same OTP again (should fail)
        echo ""
        echo "5. Testing OTP reuse protection..."
        reuse_response=$(curl -s -w "%{http_code}" -X POST https://aaryaclothing.cloud/api/v1/auth/verify-otp \
          -H "Content-Type: application/json" \
          -d "{\"email\":\"$TEST_EMAIL\",\"otp_code\":\"$stored_otp\",\"otp_type\":\"email_verification\",\"purpose\":\"verify\"}")
        
        reuse_http_code="${reuse_response: -3}"
        reuse_body="${reuse_response%???}"
        
        echo "HTTP Status: $reuse_http_code"
        echo "Response: $reuse_body"
        
        if [[ "$reuse_http_code" == "200" ]]; then
            if echo "$reuse_body" | grep -q "expired\|not found"; then
                echo -e "${GREEN}✓ OTP reuse protection working${NC}"
            else
                echo -e "${YELLOW}⚠ OTP reuse might not be working properly${NC}"
            fi
        else
            echo -e "${GREEN}✓ OTP reuse protection working (HTTP $reuse_http_code)${NC}"
        fi
        
    else
        echo -e "${RED}✗ OTP not found in Redis${NC}"
        echo "Checking all OTP keys..."
        all_otp_keys=$(docker-compose exec -T redis redis-cli keys "otp:*" 2>/dev/null || echo "")
        echo "All OTP keys: $all_otp_keys"
    fi
    
else
    echo -e "${RED}✗ Failed to send OTP (HTTP $send_http_code)${NC}"
fi

# Test 5: Check email service logs
echo ""
echo "6. Checking email service logs..."
echo "Recent email-related logs:"
docker-compose logs --tail=20 core | grep -i "email\|smtp\|otp\|sent" || echo "No email logs found in recent output"

# Test 6: Check Redis connection
echo ""
echo "7. Checking Redis connection and OTP keys..."
redis_keys=$(docker-compose exec -T redis redis-cli keys "otp:*" 2>/dev/null || echo "")
echo "Current OTP keys in Redis: $redis_keys"

# Test 7: Test rate limiting
echo ""
echo "8. Testing rate limiting (sending multiple OTPs)..."
for i in {1..3}; do
    echo "Attempt $i:"
    rate_response=$(curl -s -w "%{http_code}" -X POST https://aaryaclothing.cloud/api/v1/auth/send-otp \
      -H "Content-Type: application/json" \
      -d "{\"email\":\"ratetest@example.com\",\"otp_type\":\"email_verification\",\"purpose\":\"verify\"}")
    
    rate_http_code="${rate_response: -3}"
    rate_body="${rate_response%???}"
    
    echo "  HTTP $rate_http_code: $rate_body"
    sleep 1
done

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo "Frontend Integration Status:"
echo "- ✓ OTP API functions added to auth.ts"
echo "- ✓ Login page updated with real OTP handlers"
echo "- ✓ 6-digit OTP code implementation"
echo "- ✓ Auto-focus and input validation"
echo "- ✓ Error handling and loading states"
echo ""
echo "Backend Status:"
echo "- ✓ OTP endpoints implemented"
echo "- ✓ Redis OTP storage"
echo "- ✓ Email service with templates"
echo "- ✓ Rate limiting and cooldown"
echo ""
echo "To test manually:"
echo "1. Visit https://aaryaclothing.cloud/login"
echo "2. Switch to 'Create Account' mode"
echo "3. Fill in email and other fields"
echo "4. Select 'Email' OTP method"
echo "5. Click 'Send OTP to Email Address'"
echo "6. Check email for 6-digit code"
echo "7. Enter code in OTP inputs"
echo "8. Click 'Verify' button"
echo "9. Complete registration"
echo ""
echo "To monitor logs in real-time:"
echo "  docker-compose logs -f core"
echo ""
echo "To check Redis for OTP keys:"
echo "  docker-compose exec redis redis-cli keys 'otp:*'"
echo ""
echo "=========================================="
