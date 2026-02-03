# Aarya Clothing - Failure Scenarios and Recovery Procedures

This document outlines potential failure scenarios, their impact, and recovery procedures for the Aarya Clothing production system.

---

## 1. Database Failures

### 1.1 PostgreSQL Primary Crash

**Scenario:** PostgreSQL container crashes due to OOM or hardware failure.

**Impact:**
- All write operations fail
- Read operations fail (if using synchronous replication)
- Full system outage until recovery

**Detection:**
```bash
# Check PostgreSQL status
docker ps | grep postgres

# Check logs
docker logs aarya_postgres --tail=100

# Verify connectivity
docker exec -it aarya_postgres pg_isready -U postgres
```

**Recovery Steps:**
```bash
# 1. Check if container is running
docker ps -a | grep postgres

# 2. If container exists but is not running, check exit code
docker inspect aarya_postgres | jq '.[0].State'

# 3. Attempt to restart
docker restart aarya_postgres

# 4. If restart fails, check disk space
df -h /data/postgres

# 5. Check for corrupt WAL files
docker exec -it aarya_postgres pg_controldata /var/lib/postgresql/data/pgdata

# 6. If recovery needed, restore from latest backup
./scripts/recover.sh /data/backups/postgres_$(ls -t /data/backups/postgres*.sql.gz | head -1)
```

**Recovery Time Objective (RTO):** < 2 minutes
**Recovery Point Objective (RPO):** < 5 minutes (based on WAL archiving)

**Prevention:**
- Monitor memory usage and set appropriate limits
- Configure WAL archiving for point-in-time recovery
- Regular backups

---

### 1.2 PostgreSQL Connection Pool Exhaustion

**Scenario:** All PostgreSQL connections are consumed, new requests hang.

**Impact:**
- Service timeouts
- Failed database operations
- Cascading failures in dependent services

**Detection:**
```bash
# Check connection count
docker exec -it aarya_postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Check max connections
docker exec -it aarya_postgres psql -U postgres -c "SHOW max_connections;"

# Identify problematic queries
docker exec -it aarya_postgres psql -U postgres -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
ORDER BY duration DESC;
"
```

**Recovery Steps:**
```bash
# 1. Identify long-running queries
docker exec -it aarya_postgres psql -U postgres -c "
SELECT pid, terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active' AND query_start < NOW() - INTERVAL '5 minutes';
"

# 2. Restart services to release connections
docker-compose restart core_platform commerce payment

# 3. If persistent, increase max_connections in postgresql.conf
# Then reload configuration
docker exec -it aarya_postgres psql -U postgres -c "SELECT pg_reload_conf();"
```

**Mitigation:**
- Implement query timeouts in application
- Use PgBouncer for connection pooling
- Monitor and alert on connection count
- Optimize slow queries

---

## 2. Cache Failures

### 2.1 Redis OOM (Out of Memory)

**Scenario:** Redis uses all available memory and starts evicting keys.

**Impact:**
- Session loss (users logged out)
- Cart data loss
- Increased database load
- Cache stampede

**Detection:**
```bash
# Check Redis memory
docker exec -it aarya_redis redis-cli info memory

# Check eviction policy
docker exec -it aarya_redis redis-cli CONFIG GET maxmemory-policy

# Check evicted keys
docker exec -it aarya_redis redis-cli INFO stats | grep evicted
```

**Recovery Steps:**
```bash
# 1. Check which keys are being evicted
docker exec -it aarya_redis redis-cli --stat

# 2. Identify large keys
docker exec -it aarya_redis redis-cli --bigkeys

# 3. Clear non-essential data (if needed)
docker exec -it aarya_redis redis-cli FLUSHDB async  # Only for non-critical data

# 4. Restart Redis with higher memory limit (if configured)
docker restart aarya_redis

# 5. Force key eviction of old sessions
docker exec -it aarya_redis redis-cli EVAL "
local sessions = redis.call('KEYS', 'session:*')
for i=1, #sessions do
    local ttl = redis.call('TTL', sessions[i])
    if ttl > 0 and ttl < 3600 then
        redis.call('DEL', sessions[i])
    end
end
" 0
```

**Mitigation:**
- Configure appropriate eviction policies per namespace
- Set memory limits with room for overhead
- Monitor Redis memory usage with alerts
- Implement cache-aside pattern with write-through

---

### 2.2 Redis Connection Failure

**Scenario:** Redis becomes unreachable due to network or crash.

**Impact:**
- Session authentication failures
- Cart operations fail
- Rate limiting ineffective
- Distributed locks lost

**Detection:**
```bash
# Test Redis connectivity
docker exec -it aarya_redis redis-cli ping

# Check connection errors in logs
docker logs aarya_redis --tail=100 | grep -i error

# Check number of connected clients
docker exec -it aarya_redis redis-cli INFO clients
```

**Recovery Steps:**
```bash
# 1. Check if Redis is running
docker ps | grep redis

# 2. Attempt restart
docker restart aarya_redis

# 3. Wait for recovery
sleep 10

# 4. Verify
docker exec -it aarya_redis redis-cli ping
```

**Circuit Breaker Pattern:**
Services should implement circuit breaker to fallback gracefully:

```python
# Example circuit breaker configuration
class RedisCircuitBreaker:
    def __init__(self):
        self.failure_count = 0
        self.failure_threshold = 5
        self.circuit_open = False
        self.recovery_timeout = 30
        
    def execute(self, operation, fallback):
        if self.circuit_open:
            if time.time() > self.recovery_timeout:
                self.circuit_open = False
            else:
                return fallback()
        
        try:
            result = operation()
            self.failure_count = 0
            return result
        except RedisError:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.circuit_open = True
            return fallback()
```

---

## 3. Service Failures

### 3.1 Core Platform Service OOM

**Scenario:** Core Platform service runs out of memory and is killed.

**Impact:**
- User authentication fails
- Session validation fails
- All protected API endpoints fail
- Users may be logged out

**Detection:**
```bash
# Check service status
docker ps | grep core_platform

# Check memory usage
docker stats --no-stream | grep core_platform

# Check OOM events
docker events --filter 'type=container' --filter 'event=oom'
```

**Recovery Steps:**
```bash
# 1. Restart the service
docker-compose restart core_platform

# 2. Check logs for OOM
docker logs aarya_core_platform --tail=200 | grep -i "out of memory\|OOM\|killed"

# 3. Increase memory limit in docker-compose.yml if needed
# Then redeploy
docker-compose up -d core_platform

# 4. Check for memory leaks
docker exec -it aarya_core_platform ps aux
```

**Prevention:**
- Set memory limits with cgroups
- Implement memory leak detection
- Use worker processes with memory limits
- Monitor and alert on memory usage

---

### 3.2 Commerce Service Unavailable

**Scenario:** Commerce service crashes during high traffic.

**Impact:**
- Product browsing fails
- Cart operations fail
- Order placement fails
- Revenue loss

**Detection:**
```bash
# Check service health
curl -f http://localhost:8010/health

# Check error logs
docker logs aarya_commerce --tail=100 | grep -i error

# Check availability in Grafana
# Navigate to Service Health dashboard
```

**Recovery Steps:**
```bash
# 1. Restart the service
docker-compose restart commerce

# 2. Verify health
curl -f http://localhost:8010/health

# 3. Check if issue persists
docker logs aarya_commerce --tail=50

# 4. If persistent, check database connectivity
docker exec -it aarya_commerce python -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.getenv('DATABASE_URL'))
connection = engine.connect()
print('Database connection: OK')
"
```

**High Availability Pattern:**
```python
# Implement retry with exponential backoff
def retry_with_backoff(operation, max_retries=3, base_delay=1):
    for attempt in range(max_retries):
        try:
            return operation()
        except ServiceUnavailableError:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                raise
```

. Event Stream Failures

### ---

## 44.1 Redis Stream Backlog Buildup

**Scenario:** Consumers lag behind producers, messages accumulate.

**Impact:**
- Delayed notifications
- Stale analytics data
- Eventually out-of-memory
- System slowdown

**Detection:**
```bash
# Check stream lengths
docker exec -it aarya_redis redis-cli XLEN user_events
docker exec -it aarya_redis redis-cli XLEN order_events
docker exec -it aarya_redis redis-cli XLEN analytics_events

# Check consumer lag
docker exec -it aarya_redis redis-cli XPENDING user_events - +
```

**Recovery Steps:**
```bash
# 1. Identify slow consumers
docker logs aarya_content_services --tail=100 | grep "slow\|lag\|behind"

# 2. Temporarily increase consumer throughput
# Scale up content services (if using Swarm)
docker-compose up -d --scale content_services=2

# 3. If still lagging, run event compactor manually
docker-compose run --rm event_compactor python compact_analytics.py

# 4. If critical, clear old events (with backup)
docker exec -it aarya_redis redis-cli XREADGROUP STREAM user_events COUNT 1000
# Archive to PostgreSQL before deletion

# 5. Trim stream to manageable size
docker exec -it aarya_redis redis-cli XTRIM user_events MAXLEN 50000
```

**Prevention:**
- Monitor stream lengths and consumer lag
- Implement backpressure
- Regular event compaction
- Scale consumers based on lag

---

## 5. Infrastructure Failures

### 5.1 Disk Space Exhaustion

**Scenario:** Disk fills up, causing write failures.

**Impact:**
- Database writes fail
- Log rotation stops
- Container crashes
- Complete system outage

**Detection:**
```bash
# Check disk usage
df -h

# Check large files
du -sh /var/lib/docker/* | sort -h | tail -10

# Check log sizes
du -sh /var/lib/docker/containers/*/*-json.log | sort -h | tail -10
```

**Recovery Steps:**
```bash
# 1. Identify largest consumers
du -sh /data/* | sort -h

# 2. Clear Docker logs (if any exceed limit)
# Edit /etc/docker/daemon.json with log rotation
# Then: systemctl restart docker

# 3. Clear old backups
rm -f /data/backups/$(ls -t /data/backups/*.sql.gz | tail -20)

# 4. Compact Redis AOF
docker exec -it aarya_redis redis-cli BGREWRITEAOF

# 5. Clean up Docker
docker system df
docker system prune -af --volumes

# 6. If still full, expand disk volume
# (Cloud provider specific)
```

**Prevention:**
- Implement log rotation
- Configure Docker log limits
- Monitor disk usage with alerts
- Schedule regular cleanup

---

### 5.2 Network Partition

**Scenario:** Network connectivity lost between services.

**Impact:**
- Services can't communicate
- Distributed operations fail
- Potential data inconsistency

**Detection:**
```bash
# Check network connectivity
docker network inspect aarya_clothing_backend_network

# Check service connectivity
docker exec -it aarya_core_platform ping -c 1 commerce

# Check DNS resolution
docker exec -it aarya_core_platform nslookup postgres
```

**Recovery Steps:**
```bash
# 1. Check Docker network status
docker network ls

# 2. Recreate network if needed
docker network rm aarya_clothing_backend_network
docker-compose down
docker-compose up -d

# 3. If DNS issues, restart Docker daemon
systemctl restart docker

# 4. Verify all services can reach each other
for service in core_platform commerce payment content_services search_recommendation; do
    docker exec -it aarya_$service ping -c 1 postgres
done
```

**Mitigation:**
- Use Docker networks with proper configuration
- Implement service discovery
- Use health checks for dependent services
- Design for graceful degradation

---

## 6. Security Incidents

### 6.1 Suspicious Activity Detection

**Scenario:** Unusual API request patterns detected.

**Indicators:**
- High rate of 401/403 responses
- Multiple failed login attempts
- Unusual data access patterns
- Potential SQL injection attempts

**Detection:**
```bash
# Check for SQL injection patterns in logs
docker logs aarya_api_gateway --tail=1000 | grep -i "sql\|union\|select\|drop" | head -20

# Check authentication failures
docker logs aarya_core_platform --tail=1000 | grep "authentication\|login\|failed" | wc -l

# Check IP reputation (if configured)
# Check WAF logs
```

**Response Steps:**
```bash
# 1. Identify attack source IP
docker logs aarya_api_gateway --tail=1000 | grep -oE "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" | sort | uniq -c | sort -rn | head -10

# 2. Block suspicious IP at firewall
sudo iptables -A INPUT -s $SUSPICIOUS_IP -j DROP

# 3. Enable WAF blocking (if configured)
# Reload Nginx with updated rules

# 4. Rotate any potentially compromised credentials
./scripts/rotate_secrets.sh

# 5. Document incident
cat > /opt/aarya/incidents/$(date +%Y%m%d)_security_incident.md << EOF
# Security Incident Report
Date: $(date)
Source IP: $SUSPICIOUS_IP
Type: $ATTACK_TYPE
Actions Taken:
- IP blocked via iptables
- WAF rules updated
- Secrets rotated
Resolution: $(date)
EOF

# 6. Notify security team
curl -X POST -H "Content-Type: application/json" \
    -d '{"text":"Security incident detected. IP: '$SUSPICIOUS_IP'"}' \
    $SLACK_WEBHOOK_URL
```

---

## 7. Cascading Failures

### 7.1 Slow Database Causes Cascade

**Scenario:** Database slowdown causes service timeouts, which cause more load on database.

**Detection:**
```bash
# Check database query times
docker exec -it aarya_postgres psql -U postgres -c "
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC LIMIT 5;
"

# Check service timeouts
docker logs aarya_commerce --tail=500 | grep -i "timeout|timed out" | wc -l
```

**Recovery Steps:**
```bash
# 1. Identify blocking query
docker exec -it aarya_postgres psql -U postgres -c "
SELECT pid, usename, query, state, wait_event_type, wait_event
FROM pg_stat_activity
WHERE wait_event IS NOT NULL;
"

# 2. Terminate blocking query if safe
docker exec -it aarya_postgres psql -U postgres -c "
SELECT pg_terminate_backend(<blocking_pid>);
"

# 3. Scale down traffic temporarily
docker-compose up -d --scale commerce=1

# 4. Restart services to clear connection pools
docker-compose restart core_platform commerce

# 5. Gradually scale back up
docker-compose up -d --scale commerce=2
```

**Prevention:**
- Implement circuit breakers
- Set appropriate timeouts
- Use read replicas for heavy queries
- Implement rate limiting
- Monitor and alert on latency

---

## 8. Rollback Procedures

### 8.1 Application Rollback

```bash
# Check current version
git describe --tags

# List previous versions
git tag -l | sort -V | tail -10

# Rollback to previous version
git checkout previous_tag

# Rebuild and deploy
docker-compose down
docker-compose pull
docker-compose up -d

# Verify rollback
curl -f https://api.yourdomain.com/health

# If issues persist, rollback further
git checkout earlier_tag
docker-compose up -d
```

### 8.2 Database Rollback

```bash
# Stop application
docker-compose stop core_platform commerce payment

# Restore from backup
./scripts/recover.sh /data/backups/postgres_$(ls -t /data/backups/postgres*.sql.gz | head -1 | xargs basename)

# Start application
docker-compose start core_platform commerce payment

# Verify
curl -f https://api.yourdomain.com/api/v1/health
```

---

## 9. Communication Plan

### Incident Communication Template

```markdown
# Incident Report

**Incident ID:** INC-$(date +%Y%m%d)-001
**Severity:** [P1/P2/P3]
**Status:** [Investigating/Identified/Monitoring/Resolved]
**Start Time:** $(date)

## Summary
[Brief description of the incident]

## Impact
- [List of affected services]
- [Estimated number of affected users]
- [Business impact]

## Timeline
| Time | Action |
|------|--------|
| $(date) | Incident detected |
| $(date) | Investigation started |
| $(date) | Root cause identified |
| $(date) | Fix deployed |
| $(date) | Monitoring |
| $(date) | Resolved |

## Root Cause
[Detailed explanation of what caused the incident]

## Resolution
[What was done to fix the issue]

## Follow-up Actions
- [ ] Action item 1
- [ ] Action item 2
- [ ] Action item 3
```

---

## 10. Post-Incident Review

### Checklist

- [ ] Timeline documented
- [ ] Root cause identified
- [ ] Impact assessed
- [ ] Fix verified
- [ ] Monitoring enhanced
- [ ] Documentation updated
- [ ] Runbooks updated
- [ ] Team trained on new procedures
- [ ] Preventative measures implemented
- [ ] Lessons learned shared
