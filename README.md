# Aarya Clothing - E-Commerce Platform

A modern, scalable e-commerce platform for women's clothing built with microservices architecture. Features include user authentication, product catalog, shopping cart, order management, and secure payment processing.

## 🚀 Quick Start

### Prerequisites
- **Docker & Docker Compose** (version 29.2.0+)
- **Node.js 18+** (Node.js 25.6.0+ recommended)
- **Python 3.11+**

### One-Command Setup
```bash
# Clone the repository
git clone <repository-url>
cd Aarya_Clothing

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker-compose up -d --build

# Check service status
docker-compose ps
```

### Access Points
- **Frontend**: http://localhost:3000
- **Core API**: http://localhost:8001 (Authentication & Users)
- **Commerce API**: http://localhost:8010 (Products & Orders)
- **Payment API**: http://localhost:8020 (Payment Processing)
- **API Documentation**: http://localhost:8001/docs

## 🏗️ Architecture

### Microservices Design
```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js)                      │
│                       Port 3000                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌───────────┐  ┌───────────┐  ┌───────────┐
│   CORE    │  │ COMMERCE  │  │  PAYMENT  │
│ Port 8001 │  │ Port 8010 │  │ Port 8020 │
│  Auth &   │  │ Products  │  │ Razorpay  │
│  Users    │  │ Cart/Ord  │  │  Stripe   │
└─────┬─────┘  └─────┬─────┘  └─────┬─────┘
      │              │              │
      └──────────────┼──────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
  ┌───────────┐            ┌───────────┐
  │ PostgreSQL│            │   Redis   │
  │  Port 5432│            │  Port 6379│
  └───────────┘            └───────────┘
```

### Technology Stack

#### Frontend
- **Next.js 16.1.6** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Lucide React** - Modern icon library
- **AWS SDK** - S3 integration for assets
- **Jose** - JWT token handling

#### Backend Services
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Primary database
- **Redis** - Caching and session storage
- **SQLAlchemy** - ORM for database operations
- **Pydantic** - Data validation and serialization

#### Payment Processing
- **Razorpay** - Primary payment gateway for India
- **Stripe** - International payment support

## 📁 Project Structure

```
Aarya_Clothing/
├── README.md                    # This file
├── docker-compose.yml           # Docker orchestration
├── .env.example                 # Environment template
├── DEVELOPMENT_SETUP.md         # Detailed setup guide
├── docs/                        # Documentation
│   ├── architecture.md          # System architecture
│   ├── deployment-guide.md      # Deployment instructions
│   └── deployment-checklist.md # Production checklist
├── frontend/                    # Next.js frontend
│   ├── src/                     # Source code
│   ├── package.json             # Dependencies
│   └── Dockerfile               # Frontend container
├── services/                    # Backend services
│   ├── core/                    # Authentication service
│   │   ├── main.py              # Application entry
│   │   ├── requirements.txt     # Python dependencies
│   │   └── Dockerfile           # Core service container
│   ├── commerce/                # Product/order service
│   │   ├── main.py              # Application entry
│   │   ├── requirements.txt     # Python dependencies
│   │   ├── MIGRATION.md         # Database migrations
│   │   └── Dockerfile           # Commerce service container
│   └── payment/                 # Payment processing
│       ├── main.py              # Application entry
│       ├── requirements.txt     # Python dependencies
│       ├── README.md            # Payment service docs
│       └── Dockerfile           # Payment service container
├── docker/                      # Docker configurations
│   ├── postgres/init.sql        # Database initialization
│   └── redis/redis.conf         # Redis configuration
└── tests/                       # Test suites
```

## ✨ Features

### 🛍️ E-Commerce Core
- **Product Catalog** - Organized categories and product management
- **Shopping Cart** - Real-time cart updates with Redis
- **Order Management** - Complete order lifecycle tracking
- **Inventory Management** - Stock tracking and variants

### 👤 User Management
- **Secure Authentication** - JWT-based with refresh tokens
- **User Profiles** - Complete user account management
- **OTP Verification** - Email and phone verification
- **Password Security** - Secure password handling and reset

### 💳 Payment Processing
- **Multiple Gateways** - Razorpay (India) and Stripe (International)
- **Secure Transactions** - PCI-compliant payment processing
- **Refund Management** - Automated refund processing
- **Payment History** - Complete transaction tracking

### 🔧 Developer Experience
- **API Documentation** - Auto-generated OpenAPI docs
- **Health Checks** - Service monitoring endpoints
- **Docker Support** - Containerized deployment
- **Environment Management** - Comprehensive configuration

## 🔧 Development

### Local Development Setup

For detailed development instructions, see [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md).

### Quick Development Commands
```bash
# Start databases only
docker-compose up -d postgres redis

# Start all services with local development
start-local.bat  # Windows
# or
./start-local.sh  # Linux/Mac

# Test connections
test-connection.bat  # Windows
# or
./test-connection.sh  # Linux/Mac
```

### Service Ports
| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | Next.js application |
| Core API | 8001 | Authentication & users |
| Commerce API | 8010 | Products, cart, orders |
| Payment API | 8020 | Payment processing |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache & sessions |

## 🚀 Deployment

### Production Deployment
For production deployment instructions, see:
- [Deployment Guide](docs/deployment-guide.md)
- [Deployment Checklist](docs/deployment-checklist.md)

### Docker Production
```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d --build

# Scale services if needed
docker-compose -f docker-compose.prod.yml up -d --scale core=2 --scale commerce=2
```

## 📚 Documentation

- **[Development Setup](DEVELOPMENT_SETUP.md)** - Complete development guide
- **[Architecture](docs/architecture.md)** - System architecture and design
- **[Payment Service](services/payment/README.md)** - Payment processing details
- **[Commerce Migration](services/commerce/MIGRATION.md)** - Database migration guide

## 🔒 Security

- **JWT Authentication** - Secure token-based authentication
- **Password Encryption** - Bcrypt hashing for passwords
- **CORS Protection** - Cross-origin request security
- **Input Validation** - Comprehensive data validation
- **SQL Injection Prevention** - Parameterized queries
- **Rate Limiting** - API endpoint protection

## 🧪 Testing

### Health Checks
```bash
# Test all services
curl http://localhost:8001/health  # Core service
curl http://localhost:8010/health  # Commerce service
curl http://localhost:8020/health  # Payment service
```

### API Testing
All services expose interactive API documentation at:
- Core: http://localhost:8001/docs
- Commerce: http://localhost:8010/docs
- Payment: http://localhost:8020/docs

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support:
1. Check the [troubleshooting section](DEVELOPMENT_SETUP.md#troubleshooting)
2. Review service logs: `docker-compose logs -f <service-name>`
3. Check API documentation at `/docs` endpoints
4. Open an issue with detailed information

## 📊 Version History

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

---

**Version**: 2.0.0  
**Last Updated**: February 2026  
**Compatible**: Python 3.11, Docker 29.2.0, Node.js 25.6.03e\udd1d Contributing\n\nContributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.\n\n## \ud83d\udcdd Changelog\n\nSee [CHANGELOG.md](CHANGELOG.md) for version history and updates.\n\n## \ud83d\udcc4 License\n\nThis project is licensed under the MIT License - see the LICENSE file for details.\n\n## \ud83c\udd98 Support\n\nFor support, please open an issue in the repository or contact the development team.\n\n## \ud83d\ude4f Acknowledgments\n\n- Built with [Next.js](https://nextjs.org/)\n- Backend powered by [FastAPI](https://fastapi.tiangolo.com/)\n- Payment processing by [Razorpay](https://razorpay.com/)\n- Icons by [Lucide](https://lucide.dev/)"]