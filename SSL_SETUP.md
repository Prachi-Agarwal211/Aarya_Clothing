# SSL Certificate Setup Guide

## Current Status: Self-Signed Certificates

Your deployment is using **self-signed SSL certificates** which are automatically generated for testing. This is why you're seeing the security warning.

## ⚠️ Is This Safe?

**Yes, for testing purposes!** Self-signed certificates are secure for:
- Development and testing
- Internal applications
- Personal projects on your own VPS

The warning appears because your browser doesn't recognize the certificate authority (you), not because there's a security issue.

## 🔓 How to Access Your Site (Temporary Solution)

### Option 1: Accept the Warning (Chrome/Edge)
1. Click **"Advanced"**
2. Click **"Proceed to aaryaclothing.cloud (unsafe)"**
3. Your site will load normally

### Option 2: Accept the Warning (Firefox)
1. Click **"Advanced..."**
2. Click **"Accept the Risk and Continue"**
3. Your site will load normally

### Option 3: Add Exception (Firefox)
1. Click **"Advanced..."**
2. Click **"Accept the Risk and Continue"**
3. Check **"I understand the risks"**
4. Click **"Add Exception"**

## 🛡️ Production SSL with Let's Encrypt (Recommended)

For a production site, you should use Let's Encrypt certificates. Here's how:

### Step 1: Install Certbot on Your VPS

```bash
# SSH into your VPS
ssh root@72.61.255.8

# Update package list
apt-get update

# Install certbot
apt-get install certbot -y
```

### Step 2: Generate SSL Certificates

```bash
# Stop nginx temporarily to free up port 80
docker-compose stop nginx

# Generate certificates
certbot certonly --standalone -d aaryaclothing.cloud -d www.aaryaclothing.cloud

# You'll be asked for:
# - Email address (for renewal notices)
# - Terms of service agreement
# - Whether to share email with EFF
```

### Step 3: Copy Certificates to Docker

```bash
# Copy Let's Encrypt certificates to nginx ssl directory
cp /etc/letsencrypt/live/aaryaclothing.cloud/fullchain.pem /opt/Aarya_Clothing/docker/nginx/ssl/aaryaclothing.cloud.crt
cp /etc/letsencrypt/live/aaryaclothing.cloud/privkey.pem /opt/Aarya_Clothing/docker/nginx/ssl/aaryaclothing.cloud.key

# Set proper permissions
chmod 644 /opt/Aarya_Clothing/docker/nginx/ssl/aaryaclothing.cloud.crt
chmod 600 /opt/Aarya_Clothing/docker/nginx/ssl/aaryaclothing.cloud.key
```

### Step 4: Restart Nginx

```bash
# Start nginx again
docker-compose start nginx

# Verify nginx is running
docker-compose ps nginx
```

### Step 5: Verify SSL

```bash
# Check certificate
openssl x509 -in /opt/Aarya_Clothing/docker/nginx/ssl/aaryaclothing.cloud.crt -text -noout | grep -A 2 "Issuer"

# Should show: Issuer: C = US, O = Let's Encrypt, CN = R3
```

## 🔄 Auto-Renewal Setup

Let's Encrypt certificates expire every 90 days. Set up auto-renewal:

```bash
# Test renewal
certbot renew --dry-run

# Set up cron job for auto-renewal
crontab -e

# Add this line to renew certificates monthly and restart nginx
0 0 1 * * certbot renew --quiet && cp /etc/letsencrypt/live/aaryaclothing.cloud/fullchain.pem /opt/Aarya_Clothing/docker/nginx/ssl/aaryaclothing.cloud.crt && cp /etc/letsencrypt/live/aaryaclothing.cloud/privkey.pem /opt/Aarya_Clothing/docker/nginx/ssl/aaryaclothing.cloud.key && docker-compose restart nginx
```

## 📋 Quick Reference: Self-Signed vs Let's Encrypt

| Feature | Self-Signed | Let's Encrypt |
|---------|-------------|---------------|
| Cost | Free | Free |
| Browser Trust | ❌ Warning | ✅ Trusted |
| Setup | Automatic | Manual (one-time) |
| Validity | 365 days | 90 days (auto-renew) |
| Best For | Testing/Dev | Production |

## 🎯 Recommendation

### For Testing Now
- Use self-signed certificates
- Click "Advanced" → "Proceed to site"
- Your site will work perfectly

### For Production Later
- Follow Let's Encrypt setup above
- No more browser warnings
- Professional appearance

## 🔍 Verify Your SSL is Working

After setting up Let's Encrypt:

```bash
# Test SSL configuration
curl -I https://aaryaclothing.cloud

# Should show:
# HTTP/2 200
# server: nginx
# strict-transport-security: max-age=31536000
```

## 📞 Troubleshooting

### Certbot Fails
```bash
# Check if port 80 is free
netstat -tulpn | grep :80

# Stop nginx if running
docker-compose stop nginx

# Try certbot again
certbot certonly --standalone -d aaryaclothing.cloud -d www.aaryaclothing.cloud
```

### Certificate Not Loading
```bash
# Check nginx logs
docker logs aarya_nginx

# Test nginx config
docker exec -it aarya_nginx nginx -t

# Restart nginx
docker-compose restart nginx
```

### Domain Not Pointing Correctly
```bash
# Check DNS propagation
dig aaryaclothing.cloud

# Should show: 72.61.255.8
```

## ✅ Current Status

Your site is **fully operational** with self-signed certificates. The security warning is expected and doesn't affect functionality.

**Access your site now:** https://aaryaclothing.cloud

Click "Advanced" → "Proceed to aaryaclothing.cloud (unsafe)" to continue.

---

*Last Updated: 2026-02-09*