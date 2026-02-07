# Aarya Clothing - E-Commerce Platform

## 🚀 One-Command Production Deployment

**VPS:** 72.61.255.8 | **Domain:** aaryaclothing.cloud | **Password:** Root@2026

### ⚡ Single Command Deployment
```bash
./deploy.sh
```

That's it! This single command sets up EVERYTHING:
- ✅ All microservices (Frontend, Core, Commerce, Payment)
- ✅ SSL certificates & HTTPS
- ✅ Database with seed data
- ✅ Firewall & security
- ✅ Monitoring & backups
- ✅ Reverse proxy (Nginx)

## 📁 Project Structure
```
Aarya_Clothing/
├── deploy.sh                    # 🎯 ONE-COMMAND DEPLOYMENT
├── .env                         # Production environment
├── docker-compose.prod.yml      # Production Docker setup
├── nginx/nginx.conf            # SSL reverse proxy
├── services/                   # Microservices
│   ├── core/                   # User management (Port 8001)
│   ├── commerce/               # Products/orders (Port 8010)
│   └── payment/                # Payment processing (Port 8020)
└── frontend/                   # Next.js app (Port 3000)
```

## 🌐 Live URLs After Deployment
- **Main Site:** https://aaryaclothing.cloud
- **API:** https://aaryaclothing.cloud/api/core/, /api/commerce/, /api/payment/
- **Monitoring:** http://72.61.255.8:3001 (Grafana: admin/Root@2026_Grafana_Admin)

## 🔧 Management Commands
```bash
./manage.sh start      # Start all services
./manage.sh stop       # Stop services
./manage.sh logs       # View logs
./manage.sh status     # Check status
./manage.sh backup     # Manual backup
./manage.sh update     # Update application
```

## 🏗️ Architecture
- **Frontend:** Next.js with TypeScript
- **Backend:** FastAPI microservices
- **Database:** PostgreSQL 15
- **Cache:** Redis 7
- **Proxy:** Nginx with SSL
- **Monitoring:** Prometheus + Grafana

## 🔐 Security Features
- HTTPS enforced with SSL/TLS
- Firewall with rate limiting
- Automated daily backups
- Strong password policies
- CORS & XSS protection

---

**Just run `./deploy.sh` and your entire e-commerce platform goes live!** 🎉
