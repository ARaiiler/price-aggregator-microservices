# 🏛️ System Architecture Documentation

## Price Aggregator Microservices Architecture

**Version:** 1.0.0  
**Last Updated:** 2026-02-17  
**Status:** Production-Ready

---

## 📐 Architecture Overview

This document describes the architecture, design decisions, and data flow for the Price Aggregator Microservices system. The system follows a **microservices architecture pattern** with clear service boundaries, internal communication, and a layered security model.

---

## 🎯 Design Principles

1. **Separation of Concerns:** Each service has a single, well-defined responsibility
2. **Security by Default:** Services not exposed unless necessary
3. **Fault Tolerance:** Services can fail independently without bringing down the system
4. **Scalability:** Each service can be scaled independently based on load
5. **Observability:** Health checks and logging for all services
6. **Infrastructure as Code:** Everything defined in version-controlled Docker configurations

---

## 🏗️ System Components

### High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         External Layer                           │
│  ┌────────────┐                                                  │
│  │  Internet  │                                                  │
│  └─────┬──────┘                                                  │
│        │                                                         │
└────────┼─────────────────────────────────────────────────────────┘
         │
    ┌────▼─────┐
    │  User    │
    └────┬─────┘
         │
         │ HTTP
┌────────▼─────────────────────────────────────────────────────────┐
│                      Presentation Layer                          │
│  ┌───────────────────────────────────────────────────┐          │
│  │          Frontend (React + Nginx)                  │          │
│  │          Port: 3000 (Exposed)                      │          │
│  │  - User Interface                                  │          │
│  │  - Product Search                                  │          │
│  │  - Results Display                                 │          │
│  └──────────────────────┬─────────────────────────────┘          │
└─────────────────────────┼────────────────────────────────────────┘
                          │
                          │ HTTP REST
┌─────────────────────────▼────────────────────────────────────────┐
│                      Application Layer                           │
│  ┌───────────────────────────────────────────────────┐          │
│  │       Node.js API Gateway (Express)                │          │
│  │       Port: 5000 (Exposed)                         │          │
│  │  - Authentication (JWT)                            │          │
│  │  - Rate Limiting                                   │          │
│  │  - Request Routing                                 │          │
│  │  - Input Validation                                │          │
│  │  - Service Orchestration                           │          │
│  └──────┬────────────────────────────┬─────────────────┘          │
│         │                            │                           │
└─────────┼────────────────────────────┼───────────────────────────┘
          │                            │
          │ Internal HTTP              │ MongoDB Protocol
          │                            │
┌─────────▼────────────────────────────▼───────────────────────────┐
│                      Service Layer                               │
│  ┌────────────────────────────┐    ┌───────────────────────┐   │
│  │  Python Collector (FastAPI)│    │    MongoDB            │   │
│  │  Port: 8000 (Internal)     │    │    Port: 27017        │   │
│  │  - Web Scraping            │    │    (Internal)         │   │
│  │  - Data Collection         │    │    - User Data        │   │
│  │  - Price Aggregation       │    │    - Product Cache    │   │
│  │  - Data Normalization      │    │    - Auth Storage     │   │
│  └────────────┬───────────────┘    └───────────────────────┘   │
│               │                                                  │
│               │ Redis Protocol                                   │
│               │                                                  │
│  ┌────────────▼───────────────┐                                 │
│  │       Redis Cache          │                                 │
│  │       Port: 6379 (Internal)│                                 │
│  │  - Session Storage         │                                 │
│  │  - Query Cache             │                                 │
│  │  - Rate Limit Store        │                                 │
│  └────────────────────────────┘                                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow

### 1. Product Search Flow

```
┌────┐     ┌──────────┐     ┌──────────┐     ┌──────────────┐
│User├────▶│ Frontend ├────▶│ Gateway  ├────▶│   Python     │
└────┘     └──────────┘     └──────────┘     │  Collector   │
                                              └──────┬───────┘
                                                     │
                                                     ▼
                                              ┌──────────────┐
                                              │    Redis     │
                                              │    Cache     │
                                              └──────────────┘

1. User enters search query in Frontend
2. Frontend sends HTTP GET to Gateway (/search?query=laptop)
3. Gateway validates request and checks authentication
4. Gateway forwards request to Python Collector (internal)
5. Python Collector checks Redis cache for existing results
6. If cache miss, scrapes product data from sources
7. Python Collector normalizes and returns data
8. Gateway adds metadata and returns to Frontend
9. Frontend displays results to user
```

### 2. Authentication Flow

```
┌────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│User├────▶│ Frontend ├────▶│ Gateway  ├────▶│ MongoDB  │
└────┘     └──────────┘     └──────────┘     └──────────┘
                                │
                                ▼
                            ┌─────────┐
                            │  Redis  │
                            │ Session │
                            └─────────┘

Login Flow:
1. User submits credentials via Frontend
2. Frontend POSTs to /auth/login
3. Gateway validates credentials against MongoDB
4. Gateway generates JWT token
5. Gateway stores session in Redis
6. Gateway returns token to Frontend
7. Frontend stores token for subsequent requests
```

### 3. Data Collection Flow (Internal)

```
┌──────────────┐     ┌─────────────┐     ┌────────────┐
│   Gateway    ├────▶│   Python    ├────▶│  External  │
│              │     │  Collector  │     │  E-commerce│
└──────────────┘     └──────┬──────┘     │   Sites    │
                            │             └────────────┘
                            ▼
                     ┌──────────────┐
                     │    Redis     │
                     │   Cache      │
                     └──────────────┘

1. Gateway calls Python Collector endpoint
2. Collector initiates parallel scraping tasks
3. Collector fetches data from multiple sources
4. Data is normalized and deduplicated
5. Results cached in Redis with TTL
6. Aggregated data returned to Gateway
```

---

## 🌐 Network Architecture

### Network Topology

```
┌──────────────────────────────────────────────────────┐
│           Docker Bridge Network (internal-network)   │
│                 Subnet: 172.28.0.0/16                │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Frontend │  │ Gateway  │  │  Python  │          │
│  │          │  │          │  │Collector │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │             │             │                 │
│       └─────────────┼─────────────┘                 │
│                     │                               │
│            ┌────────┼────────┐                      │
│            │                 │                      │
│       ┌────▼────┐      ┌────▼────┐                 │
│       │ MongoDB │      │  Redis  │                 │
│       └─────────┘      └─────────┘                 │
│                                                      │
└──────────────────────────────────────────────────────┘
         │              │
    Port 3000       Port 5000
         │              │
    Exposed to Host Network
```

### Port Exposure Strategy

| Service | Internal Port | Exposed Port | Access Level |
|---------|--------------|--------------|--------------|
| Frontend | 3000 | 3000 | Public |
| Node Gateway | 5000 | 5000 | Public |
| Python Collector | 8000 | - | **Internal Only** |
| MongoDB | 27017 | - | **Internal Only** |
| Redis | 6379 | - | **Internal Only** |

**Security Rationale:**
- Only frontend and gateway are customer-facing
- Python collector is accessed exclusively by gateway via container name
- Database and cache are never exposed externally
- Reduces attack surface significantly

---

## 🔐 Security Architecture

### Defense in Depth Layers

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: Network Isolation                         │
│ - Internal Docker network                          │
│ - No external exposure for backend services        │
└─────────────────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────┐
│ Layer 2: Container Security                        │
│ - Non-root users in all containers                 │
│ - Minimal base images (Alpine, Slim)               │
│ - Read-only file systems where possible            │
└─────────────────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────┐
│ Layer 3: Application Security                      │
│ - JWT authentication                               │
│ - BCrypt password hashing                          │
│ - Rate limiting                                    │
│ - Input validation                                 │
│ - Helmet.js security headers                       │
└─────────────────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────┐
│ Layer 4: Data Security                             │
│ - Environment-based secrets                        │
│ - Encrypted connections                            │
│ - Database authentication                          │
│ - Password-protected Redis                         │
└─────────────────────────────────────────────────────┘
```

### Authentication & Authorization

```
Request Flow with JWT:

1. Client Request
   ├─▶ Authorization: Bearer <JWT_TOKEN>
   │
2. Gateway Middleware
   ├─▶ Extract token from header
   ├─▶ Verify signature with JWT_SECRET
   ├─▶ Check expiration
   ├─▶ Decode payload
   │
3. Decision
   ├─▶ Valid: Attach user context to request → Continue
   └─▶ Invalid: Return 401 Unauthorized → Reject
```

### Service-to-Service Communication

All internal communication uses **container name DNS resolution**:

```javascript
// Gateway → Python Collector
const PYTHON_URL = process.env.PYTHON_SERVICE_URL; 
// "http://python-collector:8000"

// Gateway → MongoDB
const MONGO_URI = process.env.MONGO_URI;
// "mongodb://admin:pass@mongodb:27017/db"

// Gateway → Redis
const REDIS_URL = process.env.REDIS_URL;
// "redis://:password@redis:6379/0"
```

**Benefits:**
- No hardcoded IPs
- DNS-based service discovery
- Easy to scale and replace containers
- Network-level isolation

---

## 📊 Service Communication Patterns

### Synchronous Communication (REST)

```
Frontend ━━━━━━HTTP━━━━▶ Gateway ━━━━━━HTTP━━━━▶ Python
                          │
                          ├━━━━━MongoDB━━━━▶ Database
                          │
                          └━━━━━Redis━━━━━▶ Cache
```

**Protocol:** HTTP/HTTPS REST  
**Format:** JSON  
**Pattern:** Request-Response  

**Example:**
```http
GET /search?query=laptop HTTP/1.1
Host: node-gateway:5000
Authorization: Bearer eyJhbG...
```

### Asynchronous Communication (Future)

For scalability, consider adding:
- **Message Queue:** RabbitMQ or Apache Kafka
- **Event Bus:** For pub/sub patterns
- **Background Jobs:** Bull/Celery for long-running tasks

---

## 💾 Data Architecture

### Data Storage Strategy

```
┌────────────────────────────────────────────────────┐
│              MongoDB (Primary Database)            │
├────────────────────────────────────────────────────┤
│ Collections:                                       │
│  - users: User accounts and profiles              │
│  - products: Cached product data (optional)       │
│  - searches: Search history (analytics)           │
│  - sessions: Active user sessions                 │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│                Redis (Cache Layer)                 │
├────────────────────────────────────────────────────┤
│ Key Patterns:                                      │
│  - search:<query_hash>: Cached search results     │
│  - session:<user_id>: User session data           │
│  - rate_limit:<ip>: API rate limiting             │
│  - product:<id>: Individual product cache         │
│                                                    │
│ TTL Strategy:                                      │
│  - Search results: 1 hour                         │
│  - Sessions: 24 hours                             │
│  - Rate limits: 15 minutes                        │
└────────────────────────────────────────────────────┘
```

### Data Persistence

```
Docker Volumes:

mongodb_data/
  └── Persistent MongoDB data files

mongodb_config/
  └── MongoDB configuration

redis_data/
  └── Redis RDB/AOF persistence
```

**Backup Strategy:**
- Schedule regular MongoDB dumps
- Redis snapshots for cache recovery
- Volume backups to external storage

---

## 🔄 Deployment Architecture

### Container Orchestration

```yaml
Docker Compose Dependency Graph:

                  frontend
                      │
                      │ depends_on
                      ▼
                 node-gateway
                      │
            ┌─────────┼─────────┐
            │         │         │
       depends_on  depends_on  depends_on
            │         │         │
            ▼         ▼         ▼
      python-    mongodb    redis
      collector
            │
       depends_on
            │
            ▼
          redis
```

### Health Check Strategy

All services implement health checks:

```yaml
healthcheck:
  test: [health check command]
  interval: 30s      # Check every 30 seconds
  timeout: 3s        # Fail if no response in 3s
  retries: 3         # Try 3 times before marking unhealthy
  start_period: 10s  # Grace period after container start
```

**Benefits:**
- Automatic unhealthy container detection
- Prevents routing to failed services
- Enables automated recovery

---

## 📈 Scalability Considerations

### Horizontal Scaling

Each service can be scaled independently:

```bash
# Scale Python collectors for heavy scraping
docker compose up -d --scale python-collector=3

# Scale gateway for high traffic
docker compose up -d --scale node-gateway=2
```

### Load Balancing (Future)

```
                ┌─────────────┐
                │ Load Balancer│
                │  (Nginx)     │
                └──────┬───────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
   │Gateway 1│    │Gateway 2│    │Gateway 3│
   └─────────┘    └─────────┘    └─────────┘
```

### Database Scaling

```
MongoDB Replica Set (Future):

┌─────────┐       ┌─────────┐       ┌─────────┐
│ Primary │◀─────▶│Secondary│◀─────▶│Secondary│
└─────────┘       └─────────┘       └─────────┘
     │                │                  │
     └────────────────┼──────────────────┘
                      │
                   Clients
```

---

## 🛠️ Technology Decisions

### Why Microservices?

| Benefit | Implementation |
|---------|----------------|
| **Independent Deployment** | Each service has its own container |
| **Technology Diversity** | Node.js for API, Python for scraping |
| **Fault Isolation** | One service failure doesn't cascade |
| **Team Autonomy** | Teams can own individual services |
| **Scalability** | Scale services independently |

### Why Docker?

- Consistent environments across dev/staging/prod
- Easy dependency management
- Quick deployment and rollback
- Resource isolation
- Compatible with orchestration platforms (K8s, Swarm)

### Why This Tech Stack?

| Component | Reason |
|-----------|--------|
| **React** | Modern UI, component reusability, large ecosystem |
| **Express** | Mature, middleware-friendly, Node.js ecosystem |
| **FastAPI** | High performance, async support, auto-generated docs |
| **MongoDB** | Flexible schema, JSON-native, good for product data |
| **Redis** | Fast in-memory cache, pub/sub support, simple APIs |

---

## 🔮 Future Enhancements

### Phase 2: Production Hardening
- [ ] Implement Kubernetes manifests
- [ ] Add service mesh (Istio/Linkerd)
- [ ] Implement distributed tracing (Jaeger)
- [ ] Add metrics collection (Prometheus)
- [ ] Set up log aggregation (ELK stack)

### Phase 3: Feature Expansion
- [ ] Real-time price alerts
- [ ] User preferences and wishlists
- [ ] Price history tracking
- [ ] Advanced filtering and sorting
- [ ] Mobile app with shared backend

### Phase 4: Scale Optimization
- [ ] Implement caching strategies (CDN)
- [ ] Database sharding
- [ ] Read replicas for MongoDB
- [ ] Message queue for async jobs
- [ ] GraphQL API layer

---

## 📚 References

- [12-Factor App Methodology](https://12factor.net/)
- [Microservices Patterns](https://microservices.io/patterns/index.html)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [REST API Design](https://restfulapi.net/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

---

## 📞 Architecture Review

For questions about architecture decisions:

- Create an issue with the `architecture` label
- Tag the architecture team
- Schedule an architecture review session

---

**Document Maintained By:** DevOps Team  
**Review Cycle:** Quarterly  
**Last Architecture Review:** 2026-02-17
