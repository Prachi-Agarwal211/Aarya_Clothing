# Docker Setup Guide - Aarya Clothing E-Commerce Platform

This guide will help you set up and run the complete Aarya Clothing e-commerce platform using Docker containers.

## 🚀 Quick Start

### Prerequisites

1. **Docker Desktop** - Install from [docker.com](https://www.docker.com/products/docker-desktop)
2. **Docker Compose** - Usually included with Docker Desktop
3. **Git** - For cloning the repository

### One-Command Setup

#### Windows Users
```bash
# Clone and setup
git clone <repository-url>
cd Aarya_Clothing
start-docker.bat
```

#### Linux/Mac Users
```bash
# Clone and setup
git clone <repository-url>
cd Aarya_Clothing
chmod +x start-docker.sh
./start-docker.sh
```

That's it! The complete platform will be running in a few minutes.

## 📋 What Gets Installed

The Docker setup includes:

### 🗄️ **Database Layer**
- **PostgreSQL 15** - Primary database (Port 5432)
- **Redis 7** - Cache and session storage (Port 6379)

### 🔧 **Backend Services**
- **Core Service** - Authentication & users (Port 8001)
- **Commerce Service** - Products, cart & orders (Port 8010)
- **Payment Service** - Payment processing (Port 8020)

### 🎨 **Frontend**
- **Next.js 16** - React application (Port 3000)

### 🌐 **Optional Reverse Proxy**
- **Nginx** - Load balancer and SSL termination (Ports 80/443)

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network                    │
├─────────────────────────────────────────────────────────────┤
│  Frontend (3000)  │  Core (8001)  │ Commerce (8010) │
│                     │                 │                 │
│                     │                 │                 │
│                     └─────────┬───────┘                 │
│                               │                        │
│                    ┌────────────▼────────────┐           │
│                    │   PostgreSQL (5432)   │           │
│                    │   Redis (6379)       │           │
│                    └─────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Configuration Files

### docker-compose.dev.yml
Development configuration with:
- Hot reload enabled
- Debug logging
- Development passwords
- Volume mounts for code changes

### Environment Variables
Development defaults are pre-configured:
- **PostgreSQL**: `postgres:postgres123`
- **Redis**: `redis:redis123`
- **JWT Secret**: `dev-secret-key-change-in-production`

## 🚀 Access Points

After startup, you can access:

### 🌐 **Applications**
- **Frontend**: http://localhost:3000
- **Admin Dashboard**: http://localhost:3000/admin

### 📚 **API Documentation**
- **Core API**: http://localhost:8001/docs
- **Commerce API**: http://localhost:8010/docs
- **Payment API**: http://localhost:8020/docs

### 🗄️ **Databases**
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 🛠️ Development Workflow

### 1. Making Code Changes
All services are mounted as volumes, so code changes are reflected immediately:

```bash
# Frontend changes
cd frontend
npm run dev  # Hot reload enabled

# Backend changes
cd services/core
# Changes are automatically reflected
```

### 2. Viewing Logs
```bash
# View all logs
./start-docker.sh logs
# or
start-docker.bat logs

# View specific service logs
docker-compose -f docker-compose.dev.yml logs -f core
docker-compose -f docker-compose.dev.yml logs -f commerce
docker-compose -f docker-compose.dev.yml logs -f payment
docker-compose -f docker-compose.dev.yml logs -f frontend
```

### 3. Restarting Services
```bash
# Restart specific service
docker-compose -f docker-compose.dev.yml restart core

# Restart all services
./start-docker.sh
# or
start-docker.bat
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using the port
netstat -tulpn | grep :3000  # Linux/Mac
netstat -ano | findstr :3000   # Windows

# Kill the process
kill -9 <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows
```

#### 2. Docker Not Running
- Start Docker Desktop
- Wait for it to fully initialize
- Try again

#### 3. Permission Issues (Linux/Mac)
```bash
# Fix Docker permissions
sudo usermod -aG docker $USER
# Log out and log back in
```

#### 4. Build Failures
```bash
# Clear Docker cache
docker system prune -a

# Rebuild from scratch
docker-compose -f docker-compose.dev.yml build --no-cache
```

#### 5. Database Connection Issues
```bash
# Check PostgreSQL health
docker exec aarya_postgres_dev pg_isready -U postgres

# Check Redis health
docker exec aarya_redis_dev redis-cli ping

# Reset database
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d postgres redis
```

### Health Checks

All services include health checks:
```bash
# Check all service health
docker-compose -f docker-compose.dev.yml ps

# Check specific service
curl http://localhost:8001/health  # Core
curl http://localhost:8010/health  # Commerce
curl http://localhost:8020/health  # Payment
curl http://localhost:3000       # Frontend
```

## 🐳 Docker Commands Reference

### Basic Commands
```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Stop all services
docker-compose -f docker-compose.dev.yml down

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# View running containers
docker-compose -f docker-compose.dev.yml ps

# Build images
docker-compose -f docker-compose.dev.yml build
```

### Advanced Commands
```bash
# Execute command in container
docker exec -it aarya_core_dev bash
docker exec -it aarya_postgres_dev psql -U postgres

# View resource usage
docker stats

# Clean up unused resources
docker system prune
```

## 🔧 Custom Configuration

### Environment Variables
Create `.env` file to override defaults:
```bash
cp .env.example .env
# Edit .env with your values
```

### Custom Ports
Modify `docker-compose.dev.yml`:
```yaml
services:
  postgres:
    ports:
      - "5433:5432"  # Use different host port
```

### Adding Nginx Reverse Proxy
```bash
# Start with Nginx
docker-compose -f docker-compose.dev.yml --profile with-nginx up -d
```

## 🚀 Production Deployment

For production deployment, use `docker-compose.yml` instead:
```bash
# Production setup
docker-compose up -d

# With SSL certificates
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📊 Monitoring

### Resource Usage
```bash
# View real-time stats
docker stats

# View disk usage
docker system df

# View container details
docker inspect aarya_core_dev
```

### Log Management
```bash
# View log size
docker-compose -f docker-compose.dev.yml logs --tail=100

# Export logs
docker-compose -f docker-compose.dev.yml logs > app.log

# Rotate logs
docker-compose -f docker-compose.dev.yml logs --no-log-prefix > app.log
```

## 🔒 Security Considerations

### Development vs Production
- Development uses weak passwords
- Production uses strong secrets
- Never use development secrets in production

### Network Security
- Services communicate within Docker network
- Only necessary ports exposed
- Nginx provides additional security layer

## 📚 Additional Resources

### Docker Documentation
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/dev-best-practices/)

### Service-Specific Documentation
- [Core Service README](services/core/README.md)
- [Commerce Service README](services/commerce/README.md)
- [Payment Service README](services/payment/README.md)
- [Frontend README](frontend/README.md)

## 🆘 Getting Help

If you encounter issues:

1. **Check logs**: `./start-docker.sh logs`
2. **Verify ports**: Ensure no conflicts
3. **Check Docker**: Ensure Docker is running
4. **Reset environment**: `docker-compose down -v && docker-compose up -d`
5. **Check documentation**: Service-specific READMEs

## 🎉 Success!

Once everything is running, you'll have:
- ✅ Complete e-commerce platform
- ✅ All microservices communicating
- ✅ Database persistence
- ✅ Hot reload for development
- ✅ API documentation
- ✅ Ready for development

Happy coding! 🚀
