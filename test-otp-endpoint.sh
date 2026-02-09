#!/bin/bash

# Test OTP Endpoint with Correct Request Format
# This script tests the OTP functionality with proper request format

echo "=========================================="
echo "Testing OTP Endpoint"
echo "=========================================="
echo ""

# Test 1: Send OTP for email verification
echo "Test 1: Send OTP for email verification"
echo "Request: POST /api/v1/auth/send-otp"
echo "Payload: {\"email\":\"test@example.com\",\"otp_type\":\"email_verification\",\"purpose\":\"verify\"}"
echo ""

response=$(curl -s -X POST https://aaryaclothing.cloud/api/v1/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","otp_type":"email_verification","purpose":"verify"}')

echo "Response:"
echo "$response"
echo ""

# Check if OTP was stored in Redis
echo "Checking Redis for OTP keys..."
sleep 2
otp_keys=$(docker-compose exec -T redis redis-cli keys "otp:*")
echo "OTP keys in Redis: $otp_keys"
echo ""

# Test 2: Verify OTP (will fail since we don't have the actual code)
echo "Test 2: Verify OTP (will fail - expected behavior)"
echo "Request: POST /api/v1/auth/verify-otp"
echo "Payload: {\"email\":\"test@example.com\",\"otp_code\":\"123456\",\"otp_type\":\"email_verification\",\"purpose\":\"verify\"}"
echo ""

verify_response=$(curl -s -X POST https://aaryaclothing.cloud/api/v1/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","otp_code":"123456","otp_type":"email_verification","purpose":"verify"}')

echo "Response:"
echo "$verify_response"
echo ""

# Test 3: Check core service logs
echo "Test 3: Checking core service logs for OTP activity"
echo "Recent OTP-related logs:"
docker-compose logs --tail=50 core | grep -i "otp\|email\|redis" || echo "No OTP-related logs found"
echo ""

# Test 4: Check if email was sent (look for email logs)
echo "Test 4: Checking for email send logs"
docker-compose logs --tail=100 core | grep -i "email\|smtp\|sent" || echo "No email logs found"
echo ""

echo "=========================================="
echo "Test Complete"
echo "=========================================="
echo ""
echo "If OTP was sent successfully, you should see:"
echo "  ✓ Success response from send-otp endpoint"
echo "  ✓ OTP key stored in Redis"
echo "  ✓ Email send logs in core service"
echo ""
echo "To monitor real-time logs:"
echo "  docker-compose logs -f core"
echo ""
echo "To check Redis for OTP keys:"
echo "  docker-compose exec redis redis-cli keys 'otp:*'"
echo ""
echo "=========================================="