# Deployment Guide

## Overview
This guide covers the deployment of the Aarya Clothing microservices architecture across different environments.

## Environment Setup

### Development Environment
```bash
# Clone the repository
git clone https://github.com/Prachi-Agarwal211/Aarya_Clothing.git
cd Aarya_Clothing

# Start development services
docker-compose -f docker-compose.dev.yml up -d

# Install frontend dependencies
cd frontend
npm install
npm run dev

# Install backend dependencies (for each service)
cd ../services/user-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Staging Environment
```bash
# Deploy to staging
docker-compose -f docker-compose.staging.yml up -d

# Run database migrations
docker-compose exec user-service alembic upgrade head
docker-compose exec product-service alembic upgrade head
# ... repeat for all services
```

### Production Environment
```bash
# Deploy to production
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmaps/
kubectl apply -f k8s/secrets/
kubectl apply -f k8s/services/
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/ingress/
```

## Docker Configuration

### Multi-Service Docker Compose
```yaml
version: '3.8'

services:
  # Infrastructure Services
  postgres-users:
    image: postgres:15
    environment:
      POSTGRES_DB: users_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_users_data:/var/lib/postgresql/data
    networks:
      - aarya_network
    ports:
      - "5432:5432"

  postgres-products:
    image: postgres:15
    environment:
      POSTGRES_DB: products_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_products_data:/var/lib/postgresql/data
    networks:
      - aarya_network
    ports:
      - "5433:5432"

  postgres-orders:
    image: postgres:15
    environment:
      POSTGRES_DB: orders_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_orders_data:/var/lib/postgresql/data
    networks:
      - aarya_network
    ports:
      - "5434:5432"

  postgres-payments:
    image: postgres:15
    environment:
      POSTGRES_DB: payments_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_payments_data:/var/lib/postgresql/data
    networks:
      - aarya_network
    ports:
      - "5435:5432"

  postgres-notifications:
    image: postgres:15
    environment:
      POSTGRES_DB: notifications_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_notifications_data:/var/lib/postgresql/data
    networks:
      - aarya_network
    ports:
      - "5436:5432"

  postgres-analytics:
    image: postgres:15
    environment:
      POSTGRES_DB: analytics_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_analytics_data:/var/lib/postgresql/data
    networks:
      - aarya_network
    ports:
      - "5437:5432"

  postgres-recommendations:
    image: postgres:15
    environment:
      POSTGRES_DB: recommendations_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_recommendations_data:/var/lib/postgresql/data
    networks:
      - aarya_network
    ports:
      - "5438:5432"

  # Redis Services
  redis-cache:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_cache_data:/data
    networks:
      - aarya_network
    ports:
      - "6379:6379"

  redis-sessions:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_sessions_data:/data
    networks:
      - aarya_network
    ports:
      - "6380:6379"

  redis-events:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_events_data:/data
    networks:
      - aarya_network
    ports:
      - "6381:6379"

  # Elasticsearch
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - aarya_network
    ports:
      - "9200:9200"

  # InfluxDB for Analytics
  influxdb:
    image: influxdb:2.7
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=admin
      - DOCKER_INFLUXDB_INIT_PASSWORD=${INFLUXDB_PASSWORD}
      - DOCKER_INFLUXDB_INIT_ORG=aarya
      - DOCKER_INFLUXDB_INIT_BUCKET=analytics
    volumes:
      - influxdb_data:/var/lib/influxdb2
    networks:
      - aarya_network
    ports:
      - "8086:8086"

  # Microservices
  api-gateway:
    build:
      context: ./services/api-gateway
      dockerfile: Dockerfile
    ports:
      - "8080:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres-users:5432/users_db
      - REDIS_URL=redis://redis-sessions:6379
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - postgres-users
      - redis-sessions
    networks:
      - aarya_network
    restart: unless-stopped

  user-service:
    build:
      context: ./services/user-service
      dockerfile: Dockerfile
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres-users:5432/users_db
      - REDIS_URL=redis://redis-cache:6379
      - ELASTICSEARCH_URL=http://elasticsearch:9200
    depends_on:
      - postgres-users
      - redis-cache
      - elasticsearch
    networks:
      - aarya_network
    restart: unless-stopped

  product-service:
    build:
      context: ./services/product-service
      dockerfile: Dockerfile
    ports:
      - "8002:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres-products:5432/products_db
      - REDIS_URL=redis://redis-cache:6379
      - ELASTICSEARCH_URL=http://elasticsearch:9200
    depends_on:
      - postgres-products
      - redis-cache
      - elasticsearch
    networks:
      - aarya_network
    restart: unless-stopped

  order-service:
    build:
      context: ./services/order-service
      dockerfile: Dockerfile
    ports:
      - "8003:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres-orders:5432/orders_db
      - REDIS_URL=redis://redis-cache:6379
    depends_on:
      - postgres-orders
      - redis-cache
    networks:
      - aarya_network
    restart: unless-stopped

  payment-service:
    build:
      context: ./services/payment-service
      dockerfile: Dockerfile
    ports:
      - "8004:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres-payments:5432/payments_db
      - REDIS_URL=redis://redis-cache:6379
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
    depends_on:
      - postgres-payments
      - redis-cache
    networks:
      - aarya_network
    restart: unless-stopped

  notification-service:
    build:
      context: ./services/notification-service
      dockerfile: Dockerfile
    ports:
      - "8005:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres-notifications:5432/notifications_db
      - REDIS_URL=redis://redis-events:6379
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASS=${SMTP_PASS}
    depends_on:
      - postgres-notifications
      - redis-events
    networks:
      - aarya_network
    restart: unless-stopped

  cart-service:
    build:
      context: ./services/cart-service
      dockerfile: Dockerfile
    ports:
      - "8006:8000"
    environment:
      - REDIS_URL=redis://redis-cache:6379
    depends_on:
      - redis-cache
    networks:
      - aarya_network
    restart: unless-stopped

  search-service:
    build:
      context: ./services/search-service
      dockerfile: Dockerfile
    ports:
      - "8007:8000"
    environment:
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - REDIS_URL=redis://redis-cache:6379
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres-products:5432/products_db
    depends_on:
      - elasticsearch
      - redis-cache
      - postgres-products
    networks:
      - aarya_network
    restart: unless-stopped

  analytics-service:
    build:
      context: ./services/analytics-service
      dockerfile: Dockerfile
    ports:
      - "8008:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres-analytics:5432/analytics_db
      - REDIS_URL=redis://redis-cache:6379
      - INFLUXDB_URL=http://influxdb:8086
    depends_on:
      - postgres-analytics
      - redis-cache
      - influxdb
    networks:
      - aarya_network
    restart: unless-stopped

  recommendation-service:
    build:
      context: ./services/recommendation-service
      dockerfile: Dockerfile
    ports:
      - "8009:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres-recommendations:5432/recommendations_db
      - REDIS_URL=redis://redis-cache:6379
    depends_on:
      - postgres-recommendations
      - redis-cache
    networks:
      - aarya_network
    restart: unless-stopped

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8080
      - NEXT_PUBLIC_WS_URL=ws://localhost:8080
    depends_on:
      - api-gateway
    networks:
      - aarya_network
    restart: unless-stopped

volumes:
  postgres_users_data:
  postgres_products_data:
  postgres_orders_data:
  postgres_payments_data:
  postgres_notifications_data:
  postgres_analytics_data:
  postgres_recommendations_data:
  redis_cache_data:
  redis_sessions_data:
  redis_events_data:
  elasticsearch_data:
  influxdb_data:

networks:
  aarya_network:
    driver: bridge
```

## Kubernetes Deployment

### Namespace
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: aarya-clothing
```

### ConfigMaps
```yaml
# k8s/configmaps/app-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: aarya-clothing
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  REDIS_HOST: "redis-service"
  ELASTICSEARCH_HOST: "elasticsearch-service"
  INFLUXDB_HOST: "influxdb-service"
```

### Secrets
```yaml
# k8s/secrets/app-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: aarya-clothing
type: Opaque
data:
  POSTGRES_PASSWORD: <base64-encoded-password>
  JWT_SECRET: <base64-encoded-jwt-secret>
  STRIPE_SECRET_KEY: <base64-encoded-stripe-key>
  SMTP_PASS: <base64-encoded-smtp-password>
```

### Service Deployments
```yaml
# k8s/deployments/user-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  namespace: aarya-clothing
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
      - name: user-service
        image: aarya/user-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://postgres:$(POSTGRES_PASSWORD)@postgres-users:5432/users_db"
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: POSTGRES_PASSWORD
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: user-service
  namespace: aarya-clothing
spec:
  selector:
    app: user-service
  ports:
  - protocol: TCP
    port: 8001
    targetPort: 8000
  type: ClusterIP
```

### Ingress Configuration
```yaml
# k8s/ingress/main-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: main-ingress
  namespace: aarya-clothing
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/websocket-services: "api-gateway"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
spec:
  tls:
  - hosts:
    - api.aaryaclothing.com
    - app.aaryaclothing.com
    secretName: aarya-tls
  rules:
  - host: api.aaryaclothing.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 8000
  - host: app.aaryaclothing.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000
```

## Monitoring and Logging

### Prometheus Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'api-gateway'
    static_configs:
      - targets: ['api-gateway:8000']
    metrics_path: '/metrics'

  - job_name: 'user-service'
    static_configs:
      - targets: ['user-service:8000']
    metrics_path: '/metrics'

  - job_name: 'product-service'
    static_configs:
      - targets: ['product-service:8000']
    metrics_path: '/metrics'

  # Add other services...
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Aarya Clothing Services",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{service}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

## CI/CD Pipeline

### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest
    - name: Run tests
      run: pytest

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    - name: Login to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    - name: Build and push images
      run: |
        docker build -t ghcr.io/${{ github.repository }}/user-service:${{ github.sha }} ./services/user-service
        docker push ghcr.io/${{ github.repository }}/user-service:${{ github.sha }}
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/user-service user-service=ghcr.io/${{ github.repository }}/user-service:${{ github.sha}}
        kubectl rollout status deployment/user-service
```

## Environment Variables

### Development (.env)
```bash
# Database
POSTGRES_PASSWORD=dev_password
POSTGRES_USER=postgres

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT
JWT_SECRET=dev_secret_key

# Payment
STRIPE_SECRET_KEY=sk_test_dev_key
STRIPE_PUBLISHABLE_KEY=pk_test_dev_key

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=dev@aaryaclothing.com
SMTP_PASS=dev_email_password

# External APIs
ELASTICSEARCH_URL=http://localhost:9200
INFLUXDB_URL=http://localhost:8086
```

### Production (.env.prod)
```bash
# Database
POSTGRES_PASSWORD=secure_production_password
POSTGRES_USER=postgres

# Redis
REDIS_HOST=redis-service
REDIS_PORT=6379

# JWT
JWT_SECRET=secure_production_jwt_secret

# Payment
STRIPE_SECRET_KEY=sk_live_production_key
STRIPE_PUBLISHABLE_KEY=pk_live_production_key

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=production_sendgrid_key

# External APIs
ELASTICSEARCH_URL=http://elasticsearch-service:9200
INFLUXDB_URL=http://influxdb-service:8086
```

## Backup and Recovery

### Database Backup Script
```bash
#!/bin/bash
# scripts/backup-databases.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup each database
databases=("users_db" "products_db" "orders_db" "payments_db" "notifications_db" "analytics_db" "recommendations_db")

for db in "${databases[@]}"; do
    docker exec postgres-$db pg_dump -U postgres $db > $BACKUP_DIR/${db}_${DATE}.sql
    gzip $BACKUP_DIR/${db}_${DATE}.sql
done

# Upload to cloud storage (AWS S3 example)
aws s3 sync $BACKUP_DIR s3://aarya-backups/database/

# Clean up old backups (keep last 7 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

### Recovery Script
```bash
#!/bin/bash
# scripts/restore-database.sh

DB_NAME=$1
BACKUP_FILE=$2

if [ -z "$DB_NAME" ] || [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <database_name> <backup_file>"
    exit 1
fi

# Download backup from S3
aws s3 cp s3://aarya-backups/database/$BACKUP_FILE /tmp/

# Extract backup
gunzip /tmp/$BACKUP_FILE

# Restore database
docker exec postgres-$DB_NAME psql -U postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
docker exec postgres-$DB_NAME psql -U postgres -c "CREATE DATABASE $DB_NAME;"
docker exec -i postgres-$DB_NAME psql -U postgres $DB_NAME < /tmp/${BACKUP_FILE%.gz}

echo "Database $DB_NAME restored successfully"
```

## Security Considerations

### Network Policies
```yaml
# k8s/network-policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: aarya-network-policy
  namespace: aarya-clothing
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: aarya-clothing
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: aarya-clothing
    ports:
    - protocol: TCP
      port: 5432
    - protocol: TCP
      port: 6379
    - protocol: TCP
      port: 9200
```

### SSL/TLS Configuration
```yaml
# k8s/secrets/tls-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: aarya-tls
  namespace: aarya-clothing
type: kubernetes.io/tls
data:
  tls.crt: <base64-encoded-certificate>
  tls.key: <base64-encoded-private-key>
```

This deployment guide provides comprehensive instructions for deploying the Aarya Clothing microservices architecture across different environments with proper monitoring, security, and backup strategies.
