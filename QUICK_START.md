# 🚀 Aarya Clothing - Quick Start VPS Deployment

## ⚡ Deploy in 3 Commands

```bash
# 1. SSH into your VPS
ssh root@72.61.255.8

# 2. Navigate to project
cd /opt/Aarya_Clothing

# 3. Pull latest changes and deploy
git pull origin testing && chmod +x *.sh && ./fix-and-redeploy.sh
```

That's it! Your site will be live at **https://aaryaclothing.cloud**

## ⚠️ SSL Security Warning

You may see a browser security warning: **"Your connection isn't private"** or **"net::ERR_CERT_AUTHORITY_INVALID"**

**This is NORMAL and SAFE!** Your site uses self-signed SSL certificates for testing.

### To Access Your Site Now:
1. Click **"Advanced"**
2. Click **"Proceed to aaryaclothing.cloud (unsafe)"**
3. Your site will load perfectly

### For Production SSL (No Warnings):
Run this command on your VPS:
```bash
./setup-letsencrypt.sh your-email@example.com
```

This will install trusted Let's Encrypt certificates. See [`SSL_SETUP.md`](SSL_SETUP.md:1) for details.

## 🔧 If Deployment Fails

If you see errors about missing TypeScript or shell variables, run:

```bash
./fix-and-redeploy.sh
```

This script will:
- Fix .env file special characters
- Clean up failed builds
- Rebuild and redeploy all services

---

## 📋 What's Ready

✅ **Docker Compose** - Configured for production with domain aaryaclothing.cloud
✅ **Nginx Reverse Proxy** - SSL, HTTPS redirect, API routing
✅ **Environment Variables** - Production-ready .env file
✅ **SSL Certificates** - Auto-generated (self-signed for now)
✅ **Deployment Scripts** - Automated setup and health checks

---

## 🌐 Access URLs

| Service | URL |
|---------|-----|
| Frontend | https://aaryaclothing.cloud |
| Auth API | https://aaryaclothing.cloud/api/auth/ |
| Products | https://aaryaclothing.cloud/api/products/ |
| Cart | https://aaryaclothing.cloud/api/cart/ |
| Orders | https://aaryaclothing.cloud/api/orders/ |
| Payments | https://aaryaclothing.cloud/api/payments/ |
| Health | https://aaryaclothing.cloud/health |

---

## 🔧 Common Commands

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop all
docker-compose down

# Start all
docker-compose up -d

# Health check
./health-check.sh
```

---

## ⚠️ Important Notes

### SSL Certificate Warning
You'll see a browser security warning because we're using self-signed certificates. This is **normal** for testing. Click "Advanced" → "Proceed to aaryaclothing.cloud" to continue.

### For Production SSL
Replace self-signed certificates with Let's Encrypt:
```bash
apt-get install certbot
certbot certonly --standalone -d aaryaclothing.cloud -d www.aaryaclothing.cloud
cp /etc/letsencrypt/live/aaryaclothing.cloud/fullchain.pem docker/nginx/ssl/aaryaclothing.cloud.crt
cp /etc/letsencrypt/live/aaryaclothing.cloud/privkey.pem docker/nginx/ssl/aaryaclothing.cloud.key
docker-compose restart nginx
```

---

## 📚 Documentation

- **DEPLOYMENT_README.md** - Complete deployment instructions
- **VPS_SETUP_GUIDE.md** - Detailed VPS setup guide
- **VPS_DEPLOYMENT.md** - Original deployment docs

---

## ✅ Success Checklist

After deployment, verify:

- [ ] Frontend loads at https://aaryaclothing.cloud
- [ ] All containers running: `docker-compose ps`
- [ ] No errors in logs: `docker-compose logs`
- [ ] Health check passes: `./health-check.sh`
- [ ] API endpoints respond

---

## 🆘 Troubleshooting

### Services not starting?
```bash
docker-compose logs
```

### Database issues?
```bash
docker exec -it aarya_postgres pg_isready -U postgres
```

### Nginx issues?
```bash
docker exec -it aarya_nginx nginx -t
```

### Port conflicts?
```bash
netstat -tulpn | grep :80
```

---

## 🔒 Security

- ✅ Strong passwords configured
- ✅ JWT secrets set
- ✅ CORS restricted to domain
- ⚠️ Enable firewall: `ufw allow 80/tcp && ufw allow 443/tcp && ufw enable`
- ⚠️ Use Let's Encrypt for production SSL

---

## 📊 Architecture

```
Internet → Nginx (443) → Frontend (3000)
                        → Core API (8001)
                        → Commerce API (8010)
                        → Payment API (8020)
                        → PostgreSQL (5432)
                        → Redis (6379)
```

---

## 🎯 You're Ready!

Run the deployment command and your e-commerce platform will be live!

**VPS**: 72.61.255.8
**Domain**: aaryaclothing.cloud
**Status**: Ready to deploy 🚀

---

*Need help? Check the logs or run `./health-check.sh`*
