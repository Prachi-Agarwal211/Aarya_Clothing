# Aarya Clothing - Production-Optimized Microservices Architecture

## Executive Summary

This document outlines the production-optimized architecture for Aarya Clothing, designed for a single 16GB VPS with horizontal scaling capabilities for future growth. Key optimizations include service consolidation, resilience engineering, and IPC efficiency improvements.

---

## 1. Service Consolidation Strategy

### 1.1 Merged Services (Modular Monolith Approach)

For single-node efficiency, we've consolidated related microservices while maintaining logical separation:

```
Merged Service Architecture:
├── Core Platform Service (Ports 8001-8003)
│   ├── User Service (logical)
│   ├── Auth Service (logical)
│   └── Session Service (logical)
│
├── Commerce Service (Ports 8010-8012)
│   ├── Product Service (logical)
│   ├── Inventory Service (logical)
│   ├── Cart Service (logical)
│   └── Order Service (logical)
│
├── Payment Service (Port 8020)
│   ├── Payment Processing
│   └── Fraud Detection
│
├── Content Services (Ports 8030-8031)
│   ├── Notification Service (logical)
│   └── Analytics Service (logical)
│
├── Search & Discovery (Port 8040)
│   ├── Search Service (logical)
│   └── Recommendation Service (logical)
│
└── API Gateway (Port 8080)
    ├── Routing
    ├── Rate Limiting
    └── WebSocket Management
```

### 1.2 Service Merge Rationale

| Original Services | Merged Into | Rationale |
|-----------------|-------------|-----------|
| User + Auth + Session | Core Platform | Tight coupling, shared data access patterns |
| Product + Inventory + Cart + Order | Commerce | E-commerce transaction pipeline |
| Notification + Analytics | Content Services | Both are event consumers, write-heavy |
| Search + Recommendation | Search & Discovery | Share indexing infrastructure, complementary queries |
| Payment (standalone) | Payment Service | PCI compliance isolation, security boundary |

---

## 2. Network Architecture

### 2.1 Communication Patterns

```
Frontend (Next.js:3000)
    │
    ▼
┌─────────────────────────────────────┐
│         API Gateway (8080)          │
│  ├── REST → External APIs           │
│  ├── WebSocket → Real-time          │
│  └── gRPC → Internal Services       │
└─────────────────────────────────────┘
    │
    ├── TCP (localhost) → Core Platform
    ├── TCP (localhost) → Commerce
    ├── TCP (localhost) → Payment
    ├── TCP (localhost) → Content Services
    └── TCP (localhost) → Search & Discovery
```

### 2.2 Unix Domain Sockets (Internal Only)

For maximum performance, internal service-to-service communication uses Unix domain sockets:

```
Internal Socket Paths:
├── /var/run/aarya/core.sock      → Core Platform Service
├── /var/run/aarya/commerce.sock  → Commerce Service
├── /var/run/aarya/payment.sock   → Payment Service
├── /var/run/aarya/content.sock   → Content Services
└── /var/run/aarya/search.sock    → Search & Discovery
```

**Benefits:**
- 20-30% latency reduction vs TCP
- Zero packet routing overhead
- Reduced kernel context switching

### 2.3 gRPC for Internal Communication

For high-throughput internal calls, use gRPC with Protocol Buffers:

```
gRPC Service Definitions:
├── core.proto
│   ├── GetUser(id) → User
│   ├── GetSession(id) → Session
│   └── ValidateToken(token) → ValidationResult
│
├── commerce.proto
│   ├── GetProduct(id) → Product
│   ├── UpdateInventory(request) → InventoryUpdate
│   ├── CreateOrder(request) → Order
│   └── AddToCart(request) → CartItem
│
├── payment.proto
│   ├── ProcessPayment(request) → PaymentResult
│   ├── RefundPayment(request) → RefundResult
│   └── CheckFraud(request) → FraudAssessment
│
└── search.proto
    ├── SearchProducts(query) → ProductResults
    └── GetRecommendations(user_id) → RecommendedProducts
```

---

## 3. Database Architecture

### 3.1 PostgreSQL Optimization

#### WAL Separation Configuration

```sql
-- PostgreSQL postgresql.conf optimizations
wal_level = replica
max_wal_size = 2GB
min_wal_size = 512MB
checkpoint_completion_target = 0.9
wal_compression = on
effective_io_concurrency = 200  # For SSD/NVMe
random_page_cost = 1.1  # For SSD/NVMe

-- Connection pooling
max_connections = 200
shared_buffers = 4GB  # 25% of RAM
work_mem = 64MB
maintenance_work_mem = 1GB
```

#### Read/Write Splitting

```
Database Access Pattern:
┌─────────────────────────────────────┐
│         Application Layer            │
│  ├── Writes → Primary Connection     │
│  └── Reads  → Read Replica(s)        │
└─────────────────────────────────────┘
              │
    ┌─────────┴─────────┐
    ▼                   ▼
┌─────────┐      ┌─────────────┐
│ Primary │      │   Replica   │
│ (write) │ ───► │ (read only) │
└─────────┘      └─────────────┘
```

**Implementation:**
```python
# Database router configuration
DATABASE_ROUTERS = ['core.db.ReadReplicaRouter']

class ReadReplicaRouter:
    def db_for_read(self, model, **hints):
        return 'replica'
    
    def db_for_write(self, model, **hints):
        return 'default'
```

### 3.2 Redis Optimization

#### Keyspace Isolation with Eviction Policies

```
Redis Namespaces & Policies:
┌────────────────────────────────────────────────────────┐
│ Redis Instance                                          │
├────────────────────────────────────────────────────────┤
│ │ Namespace        │ Pattern          │ Policy         │
├────────────────────────────────────────────────────────┤
│ │ cache:          │ cache:{key}      │ volatile-lru   │
│ │ session:        │ session:{id}     │ noeviction     │
│ │ cart:           │ cart:{user_id}   │ noeviction     │
│ │ stream:         │ stream:*         │ noeviction     │
│ │ lock:           │ lock:{name}      │ volatile-ttl   │
│ │ metrics:        │ metrics:{name}   │ allkeys-lru    │
└────────────────────────────────────────────────────────┘
```

**Redis Configuration (redis.conf):**
```conf
# Memory management
maxmemory 8gb
maxmemory-policy noeviction

# Persistence
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# Performance
tcp-keepalive 300
timeout 0
tcp-backlog 511
```

---

## 4. Event Pipeline Architecture

### 4.1 Redis Streams with TTL and Compaction

```
Event Stream Architecture:
┌──────────────────────────────────────────────────────────┐
│ Event Producers                                           │
│ ├── Core Platform Service                                │
│ ├── Commerce Service                                     │
│ ├── Payment Service                                      │
│ └── Content Services                                     │
└──────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────┐
│ Redis Streams (with Consumer Groups)                     │
│ ┌─────────────────┬───────────────┬─────────────────┐    │
│ │ Stream Name     │ Max Length    │ Retention       │    │
│ ├─────────────────┼───────────────┼─────────────────┤    │
│ │ user_events     │ 100,000       │ 24 hours        │    │
│ │ product_events  │ 100,000       │ 24 hours        │    │
│ │ order_events    │ 50,000        │ 7 days          │    │
│ │ payment_events  │ 50,000        │ 30 days         │    │
│ │ analytics       │ 1,000,000     │ 1 hour          │    │
│ │ notifications   │ 100,000       │ 7 days          │    │
│ └─────────────────┴───────────────┴─────────────────┘    │
└──────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────┐
│ Background Compactor (Cron Job)                          │
│ ├── Batch read stream events                             │
│ ├── Aggregate/Compress                                    │
│ ├── Archive to PostgreSQL                                 │
│ └── Delete compacted events from stream                   │
└──────────────────────────────────────────────────────────┘
```

### 4.2 Event Compaction Strategy

```python
# Event Compactor Service
class EventCompactor:
    def compact_analytics_events(self):
        """Aggregate high-frequency analytics events"""
        # Read analytics stream in batches
        # Aggregate: page_view → daily_count
        # Archive: aggregated_data → PostgreSQL analytics_db
        # Delete: original events from stream
        
    def archive_order_events(self):
        """Archive order lifecycle events"""
        # Read completed order events
        # Store: order_snapshot → PostgreSQL orders_db
        # Delete: events older than 7 days
        
    def cleanup_expired_events(self):
        """Remove expired events based on TTL"""
        # XTRIM stream events exceeding retention
```

---

## 5. Resilience Engineering

### 5.1 Service Mesh Light (Envoy)

For single-node resilience without Kubernetes overhead:

```
Envoy Configuration Structure:
envoy.yaml
├── admin:
│   └── address: unix:///var/run/envoy/admin.sock
├── static_resources:
│   ├── listeners:
│   │   ├── frontend_listener:
│   │   │   └── address: 0.0.0.0:8080
│   │   └── internal_listener:
│   │       └── address: unix:///var/run/envoy/internal.sock
│   └── clusters:
│       ├── core_cluster:
│       │   ├── hosts: unix:///var/run/aarya/core.sock
│       │   ├── circuit_breakers:
│       │   │   └── max_pending_requests: 1000
│       │   ├── retry_policy:
│       │   │   └── num_retries: 3
│       │   └── timeout: 5s
│       ├── commerce_cluster:
│       │   └── ...
│       └── payment_cluster:
│           └── ...
└── http_filters:
    ├── health_check
    ├── router
    └──熔断器
```

**Benefits:**
- Automatic circuit breaking
- Retry with exponential backoff
- Request timeouts
- Load balancing across workers

### 5.2 Resource Limits (cgroups/Docker)

```yaml
# Docker Compose with Resource Limits
services:
  core_platform:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    mem_limit: 1g
    memswap_limit: 1g
    cpu_shares: 512
    oom_kill_disable: true
    restart_policy:
      max_attempts: 3
      delay: 5s

  commerce:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1.5G
    mem_limit: 1.5g
    cpu_shares: 512
```

### 5.3 Backpressure System

```
Backpressure Implementation:
┌──────────────────────────────────────────────────────────┐
│ Gateway Layer                                             │
│ ├── Request Queue Limit: 1000                            │
│ ├── Rate Limiter: 100 req/s per IP                      │
│ └── Timeout: 30s per request                             │
└──────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────┐
│ Redis Streams                                             │
│ ├── XREADGROUP with BLOCK 5000                           │
│ ├── Consumer slow-ack protection                         │
│ └── Max stream length enforcement                        │
└──────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────┐
│ Database Layer                                            │
│ ├── PgBouncer pool limits                                │
│ ├── Query timeout enforcement                            │
│ └── Connection pool saturation protection                │
└──────────────────────────────────────────────────────────┘
```

---

## 6. Monitoring & Observability

### 6.1 Key Metrics

```yaml
# Prometheus Metrics Configuration
metrics:
  - name: http_requests_total
    type: counter
    labels: [service, method, path, status]
    
  - name: http_request_duration_seconds
    type: histogram
    labels: [service, method, path]
    buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
    
  - name: redis_commands_total
    type: counter
    labels: [command, status]
    
  - name: postgres_connections
    type: gauge
    labels: [state]
    
  - name: stream_consumer_lag
    type: gauge
    labels: [stream, consumer_group]
    
  - name: service_health_status
    type: gauge
    labels: [service]
```

### 6.2 Alert Rules

```yaml
# Prometheus Alert Rules
groups:
  - name: aarya_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on {{ $labels.service }}"
          
      - alert: DatabaseConnectionPoolExhausted
        expr: pg_stat_activity_count / pg_settings_max_connections > 0.9
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "PostgreSQL connection pool near capacity"
          
      - alert: RedisMemoryHigh
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis memory usage above 85%"
          
      - alert: StreamConsumerLagHigh
        expr: stream_consumer_lag > 10000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Consumer lag on {{ $labels.stream }} exceeds 10000"
```

---

## 7. Security Architecture

### 7.1 Network Security

```yaml
# Network Segmentation
networks:
  frontend_network:
    driver: bridge
    internal: false
    attachable: true
    
  backend_network:
    driver: bridge
    internal: true
    attachable: false
    
  payment_network:
    driver: bridge
    internal: true
    attachable: false
    # Only payment service can access
```

### 7.2 Secret Management

```bash
# Environment-based secret injection
# Use Docker secrets or external vault (HashiCorp Vault)

SECRETS:
├── DATABASE_URL → PostgreSQL connection
├── REDIS_URL → Redis connection
├── JWT_SECRET → Token signing
├── ENCRYPTION_KEY → Data encryption
├── PAYMENT_API_KEY → Payment gateway
└── SMTP credentials → Email service
```

---

## 8. Failure Scenarios & Recovery

### 8.1 Failure Matrix

| Component | Failure Mode | Impact | Recovery | RTO |
|-----------|-------------|--------|----------|-----|
| PostgreSQL | Crash | Complete outage | Auto-restart, replay WAL | < 2 min |
| Redis | OOM | Cache misses, session loss | Restart, restore from RDB | < 1 min |
| Core Platform | OOM | Auth failures | Restart, cgroup kill | < 30 sec |
| Commerce | High latency | Slow checkout | Scale horizontal | < 5 min |
| Payment | Unavailable | Failed transactions | Queue + retry | < 5 min |

### 8.2 Recovery Procedures

```bash
#!/bin/bash
# recovery.sh - Automated recovery procedures

case "$1" in
  postgres)
    # Check PostgreSQL health
    pg_isready -h postgres
    
    # If unhealthy, attempt restart
    if [ $? -ne 0 ]; then
      docker-compose restart postgres
      # Wait for recovery
      sleep 30
      # Verify
      pg_isready -h postgres
    fi
    ;;
    
  redis)
    # Check Redis health
    redis-cli ping
    
    # If unhealthy, restart
    if [ $? != "PONG" ]; then
      docker-compose restart redis
      sleep 10
    fi
    ;;
    
  service)
    SERVICE=$2
    # Check service health
    curl -f http://localhost:8080/health || {
      echo "Service $SERVICE unhealthy, restarting..."
      docker-compose restart $SERVICE
    }
    ;;
esac
```

---

## 9. Future Scaling Path

### 9.1 Horizontal Scaling Readiness

```
Current State (Single Node)          Future State (Multi-Node)
─────────────────────────             ─────────────────────────
app:3000                              Load Balancer (Nginx)
    │                                      │
    ├── core:8001                         ├── core_cluster (3x)
    ├── commerce:8010                     ├── commerce_cluster (3x)
    ├── payment:8020                     ├── payment_cluster (2x)
    ├── content:8030                     ├── content_cluster (2x)
    └── search:8040                      └── search_cluster (2x)
         │                                      │
    postgres:5432                         PostgreSQL Cluster (Patroni)
    redis:6379                            Redis Cluster
    elasticsearch:9200                    Elasticsearch Cluster
```

### 9.2 Stateless Service Requirements

All services must follow these rules for horizontal scaling:

1. **No local filesystem storage**
   - Upload files → Object Storage (S3/R2)
   - Temp files → /tmp with cleanup

2. **No in-memory sessions**
   - Sessions → Redis
   - Caches → Redis

3. **Idempotent operations**
   - Design all API endpoints to be retry-safe
   - Use idempotency keys for payments

4. **Configuration externalization**
   - All config → Environment variables
   - Feature flags → Database/Redis

---

## 10. Performance Tuning Checklist

### 10.1 Database Tuning

- [ ] `shared_buffers` set to 25% of RAM
- [ ] `effective_io_concurrency` set to 200 (SSD)
- [ ] `random_page_cost` set to 1.1 (SSD)
- [ ] Connection pooling via PgBouncer
- [ ] Query optimization with EXPLAIN ANALYZE
- [ ] Index strategy for frequent queries

### 10.2 Redis Tuning

- [ ] `maxmemory` configured
- [ ] Appropriate eviction policy per namespace
- [ ] AOF persistence enabled
- [ ] Connection pooling in application
- [ ] Pipeline for bulk operations

### 10.3 Application Tuning

- [ ] Connection pool sizing (10-20 per service)
- [ ] Request timeout enforcement (30s)
- [ ] Response compression (gzip/brotli)
- [ ] Database query optimization
- [ ] Redis caching strategy (cache-aside)
- [ ] Async processing for non-critical paths

### 10.4 Infrastructure Tuning

- [ ] NVMe disk for PostgreSQL WAL
- [ ] Separate volumes for data and WAL
- [ ] `noatime` mount option
- [ ] Kernel parameters: `vm.swappiness=10`
- [ ] File descriptor limits: `65535`

---

## 11. Deployment Checklist

### 11.1 Pre-Deployment

```bash
# 1. Verify resource availability
free -h
df -h
iostat -x 1 5

# 2. Check Docker resources
docker stats

# 3. Backup current data
pg_dump -Fc aarya_clothing > backup_$(date +%Y%m%d).dump
redis-cli BGSAVE

# 4. Verify configuration
docker-compose config

# 5. Check certificate validity (if HTTPS)
openssl s_client -connect domain:443 -servername domain
```

### 11.2 Deployment Steps

```bash
# 1. Pull latest images
docker-compose pull

# 2. Build services
docker-compose build --no-cache

# 3. Run health checks
docker-compose up -d
sleep 30
docker-compose ps

# 4. Verify external connectivity
curl -f https://api.domain.com/health
curl -f https://domain.com/health

# 5. Check logs for errors
docker-compose logs --tail=100
```

### 11.3 Post-Deployment Verification

```bash
# 1. Run smoke tests
./tests/smoke_test.sh

# 2. Verify database migrations
alembic current
alembic history --verbose

# 3. Check monitoring dashboards
# - Grafana: Service health, latency, error rates
# - Prometheus: Alert firing status

# 4. Load test (if applicable)
./tests/load_test.sh --duration=300 --users=100

# 5. Document deployment
echo "$(date): Deployment completed" >> deployment_log.txt
```

---

## 12. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          AARYA CLOTHING                             │
│                    Production Architecture (16GB VPS)               │
└─────────────────────────────────────────────────────────────────────┘

     ┌──────────────────────────────────────────────────────────┐
     │                      FRONTEND LAYER                      │
     │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
     │  │   CDN    │  │  Next.js │  │   WebSocket│  │  Static  │ │
     │  │  (R2)    │  │  (:3000) │  │  Client   │  │   Files  │ │
     │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
     └──────────────────────────────────────────────────────────┘
                                    │
                                    ▼
     ┌──────────────────────────────────────────────────────────┐
     │                     API GATEWAY (:8080)                   │
     │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
     │  │   Nginx     │  │   Rate     │  │  Auth/JWT   │       │
     │  │  (Reverse   │  │  Limiting   │  │  Validation │       │
     │  │   Proxy)    │  │             │  │             │       │
     │  └─────────────┘  └─────────────┘  └─────────────┘       │
     └──────────────────────────────────────────────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
           ▼                        ▼                        ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   CORE PLATFORM  │  │    COMMERCE      │  │     PAYMENT      │
│   (:8001-8003)   │  │   (:8010-8012)   │  │     (:8020)      │
│  ┌────────────┐  │  │  ┌────────────┐  │  │  ┌────────────┐  │
│  │   User     │  │  │  │  Product   │  │  │  │  Payment   │  │
│  │   Auth     │  │  │  │  Inventory │  │  │  │  Fraud     │  │
│  │   Session  │  │  │  │  Cart      │  │  │  │  Refund    │  │
│  └────────────┘  │  │  │  Order     │  │  │  └────────────┘  │
│       │          │  │  └────────────┘  │  │        │         │
│       │          │  │       │          │  │        │         │
└───────┼──────────┘  └───────┼──────────┘  └────────┼──────────┘
        │                     │                      │
        │                     │                      │
        └─────────────────────┴──────────────────────┘
                                │
                                ▼
     ┌──────────────────────────────────────────────────────────┐
     │                      DATA LAYER                          │
     │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
     │  │  PostgreSQL  │  │    Redis     │  │Elasticsearch │    │
     │  │   (:5432)    │  │   (:6379)    │  │   (:9200)    │    │
     │  │  ┌────────┐  │  │  ┌────────┐  │  │             │    │
     │  │  │ Primary│  │  │  │ Cache  │  │  │  Products   │    │
     │  │  │ Write  │  │  │  │ Session│  │  │  Search      │    │
     │  │  └────────┘  │  │  │ Streams│  │  │  Index      │    │
     │  │  ┌────────┐  │  │  │ Cart   │  │  └────────────┘  │
     │  │  │ Replica│  │  │  │ Locks  │  │                  │
     │  │  │ Read   │  │  │  └────────┘  │                  │
     │  │  └────────┘  │  │               │                  │
     │  └──────────────┘  └───────────────┘                  │
     └──────────────────────────────────────────────────────────┘
                                │
                                ▼
     ┌──────────────────────────────────────────────────────────┐
     │                  EVENT & MESSAGING                        │
     │  ┌─────────────────────────────────────────────────────┐ │
     │  │                 Redis Streams                         │ │
     │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │ │
     │  │  │  User   │ │ Product │ │  Order  │ │Payment  │    │ │
     │  │  │ Events  │ │ Events  │ │ Events  │ │ Events  │    │ │
     │  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘    │ │
     │  │  ┌─────────┐ ┌─────────┐                              │ │
     │  │  │Analytics│ │Notify   │                              │ │
     │  │  │ Events  │ │ Events  │                              │ │
     │  │  └─────────┘ └─────────┘                              │ │
     │  └─────────────────────────────────────────────────────┘ │
     └──────────────────────────────────────────────────────────┘
                                │
                                ▼
     ┌──────────────────────────────────────────────────────────┐
     │                  CONTENT SERVICES (:8030-8040)          │
     │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
     │  │ Notification│  │  Analytics  │  │ Search & Recs   │  │
     │  │  Service    │  │  Service    │  │  Service        │  │
     │  └─────────────┘  └─────────────┘  └─────────────────┘  │
     └──────────────────────────────────────────────────────────┘

     ┌──────────────────────────────────────────────────────────┐
     │                   MONITORING STACK                       │
     │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
     │  │Prometheus│  │  Grafana │  │   ELK     │  │  Health  │ │
     │  │Metrics   │  │Dashboards│  │  Logging  │  │  Checks  │ │
     │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
     └──────────────────────────────────────────────────────────┘
```

---

## Summary

This architecture provides:

1. **Service Consolidation**: Reduced from 11 services to 5 for single-node efficiency
2. **Resilience Engineering**: Circuit breakers, resource limits, backpressure
3. **Performance Optimization**: Unix sockets, gRPC, connection pooling
4. **Operational Excellence**: Monitoring, alerting, automated recovery
5. **Future-Ready**: Stateless design enabling horizontal scaling

Key production principles applied:
- **Failure isolation** prevents cascading outages
- **Resource limits** protect against runaway services
- **Backpressure** ensures graceful degradation
- **Observability** enables rapid diagnosis
