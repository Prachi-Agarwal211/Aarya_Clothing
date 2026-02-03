# Aarya Clothing - Real-time Microservices Architecture

## Overview
Real-time e-commerce platform with event-driven microservices, search capabilities, and distributed data management.

## Microservices Architecture

### 1. Frontend Service (Next.js)
```
Frontend Service
├── Port: 3000
├── Real-time Features:
│   ├── WebSocket connections
│   ├── Server-Sent Events (SSE)
│   ├── Live inventory updates
│   ├── Real-time order tracking
│   └── Live chat support
├── Technologies:
│   ├── Next.js 14
│   ├── Socket.io-client
│   ├── SWR for real-time data
│   └── React Query
└── Connections:
    ├── API Gateway (REST/WebSocket)
    └── Direct WebSocket to services
```

### 2. API Gateway
```
API Gateway Service
├── Port: 8080
├── Responsibilities:
│   ├── Route management
│   ├── Authentication/Authorization
│   ├── Rate limiting
│   ├── Load balancing
│   ├── WebSocket proxy
│   └── Request transformation
├── Real-time Features:
│   ├── WebSocket connection management
│   ├── SSE streaming
│   └── Event broadcasting
└── Technologies:
    ├── FastAPI + WebSockets
    ├── Nginx/Traefik
    └── Redis for session storage
```

### 3. User Service
```
User Service
├── Port: 8001
├── Database: PostgreSQL (users_db)
├── Cache: Redis (user sessions, profiles)
├── Real-time Features:
│   ├── Online status tracking
│   ├── Profile updates broadcasting
│   ├── Activity feeds
│   └── Real-time notifications
├── Tables:
│   ├── users (id, email, username, full_name, avatar, is_online, last_seen)
│   ├── user_profiles (user_id, bio, preferences, settings)
│   ├── user_sessions (session_id, user_id, device, last_activity)
│   ├── user_activities (id, user_id, activity_type, timestamp, metadata)
│   └── user_social (user_id, followers, following, blocked)
├── Events:
│   ├── user.created
│   ├── user.updated
│   ├── user.online
│   ├── user.offline
│   └── user.activity
└── Connections:
    ├── Redis Streams (events)
    ├── PostgreSQL (data)
    └── Elasticsearch (search indexing)
```

### 4. Product Service
```
Product Service
├── Port: 8002
├── Database: PostgreSQL (products_db)
├── Search: Elasticsearch (product_search)
├── Cache: Redis (product cache, inventory)
├── Real-time Features:
│   ├── Live inventory updates
│   ├── Price change notifications
│   ├── Product view tracking
│   ├── Stock alerts
│   └── Recommendation updates
├── Tables:
│   ├── products (id, name, description, price, category_id, brand_id, is_active)
│   ├── product_variants (id, product_id, size, color, sku, inventory_count)
│   ├── product_images (id, product_id, image_url, is_primary)
│   ├── categories (id, name, parent_id, description, is_active)
│   ├── brands (id, name, logo_url, description)
│   ├── product_reviews (id, product_id, user_id, rating, review, created_at)
│   ├── product_view_history (id, product_id, user_id, viewed_at)
│   └── inventory_logs (id, product_id, old_quantity, new_quantity, reason)
├── Events:
│   ├── product.created
│   ├── product.updated
│   ├── product.inventory.updated
│   ├── product.viewed
│   └── product.reviewed
└── Connections:
    ├── Redis Streams (events)
    ├── PostgreSQL (data)
    ├── Elasticsearch (search)
    └── Redis Cache (performance)
```

### 5. Order Service
```
Order Service
├── Port: 8003
├── Database: PostgreSQL (orders_db)
├── Cache: Redis (order cache, cart sessions)
├── Real-time Features:
│   ├── Real-time order tracking
│   ├── Order status updates
│   ├── Delivery tracking
│   └── Order notifications
├── Tables:
│   ├── orders (id, user_id, total_amount, status, shipping_address, created_at)
│   ├── order_items (id, order_id, product_id, quantity, price, variant_id)
│   ├── order_status_history (id, order_id, status, timestamp, notes)
│   ├── shipping_addresses (id, user_id, address_line1, city, state, postal_code)
│   ├── order_tracking (id, order_id, tracking_number, current_location, estimated_delivery)
│   └── abandoned_carts (id, user_id, items, total_amount, abandoned_at)
├── Events:
│   ├── order.created
│   ├── order.status.updated
│   ├── order.payment.completed
│   ├── order.shipped
│   └── cart.abandoned
└── Connections:
    ├── Redis Streams (events)
    ├── PostgreSQL (data)
    └── Payment Service (integration)
```

### 6. Payment Service
```
Payment Service
├── Port: 8004
├── Database: PostgreSQL (payments_db)
├── Cache: Redis (payment sessions)
├── Real-time Features:
│   ├── Real-time payment processing
│   ├── Payment status updates
│   ├── Fraud detection alerts
│   └── Refund processing
├── Tables:
│   ├── payments (id, order_id, amount, status, payment_method, gateway_response)
│   ├── payment_methods (id, user_id, type, provider, is_default, token)
│   ├── refunds (id, payment_id, amount, status, reason, processed_at)
│   ├── payment_attempts (id, payment_id, attempt_number, status, gateway_response)
│   └── fraud_flags (id, payment_id, risk_score, flags, resolved)
├── Events:
│   ├── payment.initiated
│   ├── payment.completed
│   ├── payment.failed
│   ├── refund.processed
│   └── fraud.detected
└── Connections:
    ├── Redis Streams (events)
    ├── PostgreSQL (data)
    └── External Payment Gateways
```

### 7. Cart Service
```
Cart Service
├── Port: 8006
├── Database: Redis (cart storage)
├── Cache: Redis (cart cache)
├── Real-time Features:
│   ├── Real-time cart updates
│   ├── Cross-device cart sync
│   ├── Cart abandonment tracking
│   └── Live inventory checking
├── Data Structure (Redis):
│   ├── cart:{user_id} (Hash) - cart items
│   ├── cart:session:{session_id} (Hash) - guest cart
│   ├── cart:analytics (Stream) - cart events
│   └── inventory:lock (Set) - temporary inventory locks
├── Events:
│   ├── cart.updated
│   ├── cart.item_added
│   ├── cart.item_removed
│   └── cart.abandoned
└── Connections:
    ├── Redis Streams (events)
    ├── Redis Storage (data)
    └── Product Service (inventory)
```

### 8. Notification Service
```
Notification Service
├── Port: 8005
├── Database: PostgreSQL (notifications_db)
├── Queue: Redis (notification queue)
├── Real-time Features:
│   ├── Real-time push notifications
│   ├── Email notifications
│   ├── SMS notifications
│   ├── In-app notifications
│   └── WebSocket notifications
├── Tables:
│   ├── notifications (id, user_id, type, title, message, is_read, created_at)
│   ├── notification_templates (id, name, subject, body_html, body_text)
│   ├── notification_preferences (user_id, email_enabled, sms_enabled, push_enabled)
│   ├── email_logs (id, to, subject, status, sent_at, error_message)
│   └── sms_logs (id, phone_number, message, status, sent_at, error_message)
├── Events:
│   ├── notification.email
│   ├── notification.sms
│   ├── notification.push
│   └── notification.in_app
└── Connections:
    ├── Redis Streams (events)
    ├── PostgreSQL (data)
    └── External Services (Email/SMS providers)
```

### 9. Search Service
```
Search Service
├── Port: 8007
├── Search Engine: Elasticsearch
├── Cache: Redis (search cache)
├── Real-time Features:
│   ├── Real-time search indexing
│   ├── Auto-complete suggestions
│   ├── Search analytics
│   └── Personalized search results
├── Elasticsearch Indices:
│   ├── products (name, description, category, brand, price, attributes)
│   ├── users (username, full_name, bio, location)
│   ├── orders (order_id, user_id, status, products)
│   └── search_suggestions (query, frequency, category)
├── Tables (PostgreSQL):
│   ├── search_queries (id, user_id, query, results_count, timestamp)
│   ├── search_analytics (id, query, filters, results, clicked_result)
│   └── search_trends (id, query, frequency, date)
├── Events:
│   ├── search.query
│   ├── search.result.clicked
│   └── search.index.updated
└── Connections:
    ├── Elasticsearch (search)
    ├── Redis Cache (performance)
    └── PostgreSQL (analytics)
```

### 10. Analytics Service
```
Analytics Service
├── Port: 8008
├── Database: PostgreSQL (analytics_db)
├── Time Series: InfluxDB (metrics)
├── Cache: Redis (aggregated data)
├── Real-time Features:
│   ├── Real-time analytics dashboard
│   ├── Live sales tracking
│   ├── User behavior analytics
│   └── Performance metrics
├── Tables:
│   ├── page_views (id, user_id, page, timestamp, session_id)
│   ├── user_events (id, user_id, event_type, properties, timestamp)
│   ├── sales_metrics (id, date, total_sales, order_count, avg_order_value)
│   ├── product_metrics (id, product_id, views, add_to_carts, purchases)
│   └── user_sessions (id, user_id, session_id, start_time, end_time, pages_visited)
├── Events:
│   ├── analytics.page_view
│   ├── analytics.user_event
│   ├── analytics.sale
│   └── analytics.conversion
└── Connections:
    ├── Redis Streams (events)
    ├── PostgreSQL (analytics data)
    └── InfluxDB (time series)
```

### 11. Recommendation Service
```
Recommendation Service
├── Port: 8009
├── Database: PostgreSQL (recommendations_db)
├── Cache: Redis (recommendation cache)
├── ML: Python/Scikit-learn
├── Real-time Features:
│   ├── Real-time product recommendations
│   ├── Personalized content
│   ├── Collaborative filtering
│   └── Content-based filtering
├── Tables:
│   ├── user_preferences (user_id, category_preferences, brand_preferences)
│   ├── product_recommendations (user_id, product_id, score, reason)
│   ├── user_interactions (user_id, product_id, interaction_type, timestamp)
│   ├── recommendation_models (id, name, version, accuracy, is_active)
│   └── recommendation_feedback (user_id, product_id, recommended, clicked, purchased)
├── Events:
│   ├── recommendation.generated
│   ├── recommendation.clicked
│   └── recommendation.purchased
└── Connections:
    ├── Redis Streams (events)
    ├── PostgreSQL (data)
    └── ML Models (recommendations)
```

## Event Bus Architecture

### Redis Streams Configuration
```
Event Streams:
├── user_events (user service events)
├── product_events (product service events)
├── order_events (order service events)
├── payment_events (payment service events)
├── notification_events (notification service events)
├── cart_events (cart service events)
├── search_events (search service events)
├── analytics_events (analytics service events)
└── recommendation_events (recommendation service events)

Consumer Groups:
├── notification_consumer (notification service)
├── analytics_consumer (analytics service)
├── search_consumer (search service)
├── recommendation_consumer (recommendation service)
└── audit_consumer (audit logging)
```

## Database Architecture

### PostgreSQL Clusters
```
users_db:
├── users
├── user_profiles
├── user_sessions
├── user_activities
└── user_social

products_db:
├── products
├── product_variants
├── product_images
├── categories
├── brands
├── product_reviews
├── product_view_history
└── inventory_logs

orders_db:
├── orders
├── order_items
├── order_status_history
├── shipping_addresses
├── order_tracking
└── abandoned_carts

payments_db:
├── payments
├── payment_methods
├── refunds
├── payment_attempts
└── fraud_flags

notifications_db:
├── notifications
├── notification_templates
├── notification_preferences
├── email_logs
└── sms_logs

analytics_db:
├── page_views
├── user_events
├── sales_metrics
├── product_metrics
└── user_sessions

recommendations_db:
├── user_preferences
├── product_recommendations
├── user_interactions
├── recommendation_models
└── recommendation_feedback
```

### Elasticsearch Indices
```
products_index:
├── Product name and description
├── Category and brand information
├── Price and availability
├── Product attributes
└── Search relevance scoring

users_index:
├── User profiles
├── User preferences
├── Location data
└── Social connections

orders_index:
├── Order information
├── Order status
├── Product details
└── Customer information
```

### Redis Data Structure
```
Cache Layer:
├── user:{id} (Hash) - User profile cache
├── product:{id} (Hash) - Product cache
├── inventory:{product_id} (String) - Inventory count
├── cart:{user_id} (Hash) - Shopping cart
├── session:{session_id} (Hash) - User session
└── search:{query_hash} (String) - Search results cache

Real-time Data:
├── online_users (Set) - Online user IDs
├── product_views:{product_id} (Sorted Set) - Real-time views
├── trending_products (Sorted Set) - Trending products
└── live_orders (Stream) - Live order updates
```

## Real-time Features Implementation

### WebSocket Connections
```
WebSocket Endpoints:
├── /ws/notifications - Real-time notifications
├── /ws/orders - Order status updates
├── /ws/inventory - Live inventory updates
├── /ws/analytics - Real-time analytics
└── /ws/chat - Customer support chat
```

### Server-Sent Events (SSE)
```
SSE Endpoints:
├── /sse/product-updates - Product updates
├── /sse/price-changes - Price change notifications
├── /sse/stock-alerts - Stock level alerts
└── /sse/promotions - Live promotions
```

## Technology Stack

### Backend Services
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Search**: Elasticsearch 8
- **Message Queue**: Redis Streams
- **Real-time**: WebSockets, SSE
- **Analytics**: InfluxDB
- **ML**: Python/Scikit-learn

### Frontend
- **Framework**: Next.js 14
- **Real-time**: Socket.io, SSE
- **State Management**: SWR, React Query
- **UI**: Tailwind CSS, shadcn/ui

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Kubernetes
- **API Gateway**: Traefik/Nginx
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack
- **Service Mesh**: Istio

## Data Flow Examples

### Order Creation Flow
```
1. User places order → Order Service
2. Order Service publishes order.created event
3. Payment Service processes payment
4. Inventory Service updates stock
5. Notification Service sends confirmation
6. Analytics Service records sale
7. Search Service updates order index
8. Recommendation Service learns from purchase
```

### Real-time Inventory Update
```
1. Product purchased → Inventory updated
2. Product Service publishes inventory.updated event
3. Cart Service updates cart availability
4. Frontend receives WebSocket update
5. Search Service updates availability
6. Analytics Service records sale
7. Recommendation Service adjusts suggestions
```

This architecture provides a scalable, real-time e-commerce platform with comprehensive search capabilities and robust data management across multiple services.
