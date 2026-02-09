# VPS Deployment for Authentication Fixes

## 🚀 Quick Deployment

### Option 1: Automated Deployment (Recommended)

```bash
# SSH into your VPS
ssh root@your-vps-ip

# Navigate to project directory
cd /root/Aarya_Clothing

# Make the deployment script executable
chmod +x quick-deploy-vps.sh

# Run the automated deployment
./quick-deploy-vps.sh

# Or specify custom directory and branch
./quick-deploy-vps.sh /path/to/project testing
```

### Option 2: Manual Step-by-Step

```bash
# 1. Connect to VPS
ssh root@your-vps-ip

# 2. Navigate to project
cd /root/Aarya_Clothing

# 3. Pull latest changes
git checkout testing
git pull origin testing

# 4. Stop current services
docker-compose down

# 5. Build and start services
docker-compose up --build -d

# 6. Wait for services to be healthy
docker-compose ps

# 7. Test the deployment
curl https://aaryaclothing.cloud/api/v1/health
```

## 📋 What's Being Deployed

### ✅ Frontend Changes
- **Enhanced Login Page**: Supports both email and username login
- **Registration Flow**: Complete with password validation and auto-login
- **OTP Integration**: Optional email verification with 6-digit codes
- **Better UX**: Loading states, error messages, and user feedback

### ✅ Backend Changes
- **Dual Login Support**: Backend accepts both email and username
- **Enhanced Validation**: Password strength requirements enforced
- **OTP System**: Email service with rate limiting and Redis storage
- **Security Improvements**: Rate limiting, account lockout, session management

### ✅ New Features
- **Auto-Login**: Users are automatically logged in after registration
- **Password Confirmation**: Prevents typos during registration
- **Optional OTP**: Users can register without OTP verification
- **Smart Validation**: Detects email vs username format automatically

## 🐳 Docker Configuration

### Services Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Core        │    │   PostgreSQL    │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Database)    │
│   Port: 3000    │    │   Port: 8001    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │     Redis       │    │   Commerce      │
│  (Reverse Proxy)│    │   (Cache/Session)│    │   (Products)    │
│  Ports: 80,443  │    │   Port: 6379    │    │   Port: 8010    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Environment Variables
```yaml
# Core Service (Port 8001)
- DATABASE_URL=postgresql://postgres:password@postgres:5432/aarya_clothing
- REDIS_URL=redis://redis:6379/0
- SMTP_HOST=smtp.gmail.com
- SMTP_PORT=587
- SMTP_USER=razorrag.official@gmail.com
- SMTP_PASSWORD=dbvn-cxml-ahoc-ndmy
- OTP_CODE_LENGTH=6
- OTP_EXPIRY_MINUTES=10

# Frontend (Port 3000)
- NEXT_PUBLIC_API_URL=https://aaryaclothing.cloud/api
```

## 🧪 Testing the Deployment

### 1. Health Check
```bash
# Test core service
curl http://localhost:8001/api/v1/health

# Test through nginx
curl https://aaryaclothing.cloud/api/v1/health
```

### 2. Authentication Testing
```bash
# Test OTP endpoint
curl -X POST https://aaryaclothing.cloud/api/v1/auth/send-otp \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@example.com","otp_type":"email_verification","purpose":"verify"}'

# Test login endpoint
curl -X POST https://aaryaclothing.cloud/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"test@example.com","password":"TestPass123","remember_me":false}'
```

### 3. Frontend Testing
Visit: https://aaryaclothing.cloud/login

Test these scenarios:
1. ✅ **Registration**: Create new account with strong password
2. ✅ **Email Login**: Login using email address
3. ✅ **Username Login**: Login using username
4. ✅ **OTP Verification**: Optional email verification
5. ✅ **Password Reset**: Forgot password flow
6. ✅ **Auto-Login**: Automatic login after registration

## 🔍 Troubleshooting

### Common Issues and Solutions

#### Frontend Not Updating
```bash
# Restart frontend service
docker-compose restart frontend

# Check frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose up --build -d frontend
```

#### OTP Not Working
```bash
# Check core service logs
docker-compose logs core | grep -i otp

# Check email service logs
docker-compose logs core | grep -i email

# Check Redis OTP keys
docker-compose exec redis redis-cli keys "otp:*"

# Test SMTP connection
docker-compose exec core python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('razorrag.official@gmail.com', 'dbvn-cxml-ahoc-ndmy')
print('SMTP connection successful')
server.quit()
"
```

#### Database Issues
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Connect to database
docker-compose exec postgres psql -U postgres -d aarya_clothing

# Check user table
SELECT COUNT(*) FROM users;
SELECT email, username, is_active FROM users LIMIT 5;
```

#### Service Not Starting
```bash
# Check all service status
docker-compose ps

# Check system resources
docker stats
free -h
df -h

# Check service logs
docker-compose logs [service_name]
```

#### SSL/HTTPS Issues
```bash
# Check nginx configuration
docker-compose exec nginx nginx -t

# Check SSL certificates
docker-compose exec nginx ls -la /etc/nginx/ssl/

# Reload nginx
docker-compose exec nginx nginx -s reload
```

## 📊 Monitoring

### Real-time Logs
```bash
# Monitor all services
docker-compose logs -f

# Monitor specific service
docker-compose logs -f core
docker-compose logs -f frontend
```

### Performance Monitoring
```bash
# Check container resource usage
docker stats

# Check system resources
htop
free -h
df -h
```

### Health Monitoring
```bash
# Create health check script
cat > health-check.sh << 'EOF'
#!/bin/bash
echo "=== Service Health ==="
docker-compose ps

echo ""
echo "=== Core Service Health ==="
curl -s http://localhost:8001/api/v1/health || echo "Core service down"

echo ""
echo "=== External Health ==="
curl -s https://aaryaclothing.cloud/api/v1/health || echo "External access down"

echo ""
echo "=== Redis Status ==="
docker-compose exec redis redis-cli ping

echo ""
echo "=== PostgreSQL Status ==="
docker-compose exec postgres pg_isready -U postgres
EOF

chmod +x health-check.sh
./health-check.sh
```

## 🔄 Updating in the Future

### For Future Updates
```bash
# Pull latest changes
git pull origin testing

# Redeploy
./quick-deploy-vps.sh

# Or manual update
docker-compose down
docker-compose up --build -d
```

### Branch Management
```bash
# Switch to production branch when ready
git checkout production
git merge testing
git push origin production

# Deploy production
./quick-deploy-vps.sh /path/to/project production
```

## 🎯 Success Criteria

Your deployment is successful if:

✅ **All services are healthy**: `docker-compose ps` shows all services as "healthy"
✅ **Health endpoint works**: `curl https://aaryaclothing.cloud/api/v1/health` returns 200
✅ **Frontend loads**: Website loads at https://aaryaclothing.cloud
✅ **Registration works**: Users can create new accounts
✅ **Login works**: Users can login with email or username
✅ **OTP works**: Optional email verification functions
✅ **No errors in logs**: `docker-compose logs` shows no critical errors

## 🎉 Post-Deployment

After successful deployment:

1. **Test all authentication flows** manually
2. **Monitor logs** for any issues
3. **Set up monitoring** alerts if needed
4. **Backup database** for safety
5. **Document any custom configurations**

---

## 📞 Support

If you encounter issues:

1. **Check logs**: `docker-compose logs [service]`
2. **Run health check**: `./health-check.sh`
3. **Review troubleshooting guide** above
4. **Restart services**: `docker-compose restart [service]`

The authentication system is now fully functional with dual login support, optional OTP verification, and enhanced security! 🚀
