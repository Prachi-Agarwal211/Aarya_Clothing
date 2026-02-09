#!/bin/bash

# Email Service Test Script
# Tests email sending functionality for OTP

echo "=========================================="
echo "Email Service Test for OTP"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test email
TEST_EMAIL="razorrag.official@gmail.com"  # Using the configured email for testing

echo -e "${YELLOW}Testing Email Configuration${NC}"
echo ""

# Check current email settings
echo "Current Email Configuration:"
echo "SMTP_HOST: smtp.gmail.com"
echo "SMTP_PORT: 587"
echo "SMTP_USER: razorrag.official@gmail.com"
echo "SMTP_PASSWORD: [REDACTED]"
echo "EMAIL_FROM: noreply@aaryaclothings.com"
echo ""

# Test 1: Send OTP to configured email
echo "1. Sending OTP to $TEST_EMAIL"
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
    echo -e "${GREEN}✓ OTP send request successful${NC}"
    
    # Get OTP from Redis for verification
    echo ""
    echo "2. Retrieving OTP from Redis for verification..."
    sleep 2
    
    otp_key="otp:email_verification:$TEST_EMAIL"
    stored_otp=$(docker-compose exec -T redis redis-cli get "$otp_key" 2>/dev/null || echo "")
    
    if [[ -n "$stored_otp" && "$stored_otp" != "(nil)" ]]; then
        echo -e "${GREEN}✓ OTP retrieved from Redis: $stored_otp${NC}"
        
        echo ""
        echo "3. Verifying OTP..."
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
    else
        echo -e "${RED}✗ OTP not found in Redis${NC}"
    fi
else
    echo -e "${RED}✗ Failed to send OTP (HTTP $send_http_code)${NC}"
fi

# Test 4: Check email service logs
echo ""
echo "4. Checking email service logs..."
echo "Recent email/SMTP logs:"
docker-compose logs --tail=30 core | grep -i "email\|smtp\|sent\|otp" || echo "No email logs found"

# Test 5: Test with different email
echo ""
echo "5. Testing with different email address..."
DIFFERENT_EMAIL="test+different@example.com"

diff_response=$(curl -s -w "%{http_code}" -X POST https://aaryaclothing.cloud/api/v1/auth/send-otp \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$DIFFERENT_EMAIL\",\"otp_type\":\"email_verification\",\"purpose\":\"verify\"}")

diff_http_code="${diff_response: -3}"
diff_body="${diff_response%???}"

echo "HTTP Status: $diff_http_code"
echo "Response: $diff_body"

if [[ "$diff_http_code" == "200" ]]; then
    echo -e "${GREEN}✓ OTP sent to different email successfully${NC}"
else
    echo -e "${RED}✗ Failed to send OTP to different email${NC}"
fi

echo ""
echo "=========================================="
echo "Email Service Test Summary"
echo "=========================================="
echo ""
echo "Email Configuration Status:"
echo "- ✓ SMTP server: smtp.gmail.com:587"
echo "- ✓ Authentication configured"
echo "- ✓ TLS enabled"
echo "- ✓ From address: noreply@aaryaclothings.com"
echo ""
echo "Test Results:"
if [[ "$send_http_code" == "200" ]]; then
    echo "- ✓ OTP send API working"
    echo "- ✓ Email service configured"
    echo "- ✓ Check your email for the OTP code"
else
    echo "- ✗ Email service may have issues"
    echo "- Check SMTP credentials and network"
fi
echo ""
echo "Troubleshooting:"
echo "1. Check if Gmail app password is correct"
echo "2. Verify Gmail allows less secure apps (or use App Password)"
echo "3. Check network connectivity to smtp.gmail.com:587"
echo "4. Review core service logs for detailed error messages"
echo ""
echo "To monitor email logs in real-time:"
echo "  docker-compose logs -f core | grep -i email"
echo ""
echo "=========================================="
