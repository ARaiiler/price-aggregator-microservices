# Price Aggregator Microservices

A production-ready microservices platform for aggregating and comparing product prices across multiple e-commerce platforms. This system demonstrates modern software architecture patterns including service isolation, API gateway pattern, JWT authentication, and containerized deployment with CI/CD automation.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)](https://www.docker.com/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-Jenkins-red.svg)](https://www.jenkins.io/)

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Team Development Workflow](#team-development-workflow)
- [CI/CD Pipeline](#cicd-pipeline)
- [Docker Architecture](#docker-architecture)
- [Environment Configuration](#environment-configuration)
- [API Documentation](#api-documentation)
  - [Base URL](#base-url)
  - [Authentication Header](#authentication-header)
  - [Endpoint Summary](#endpoint-summary)
  - [Service Info — GET /](#service-info)
  - [Health Check — GET /health](#health-check)
  - [Register — POST /auth/register](#post-authregister)
  - [Login — POST /auth/login](#post-authlogin)
  - [Search — GET /search](#get-search)
  - [Global Error Format](#global-error-format)
- [Production Notes](#production-notes)
- [Future Enhancements](#future-enhancements)
- [License](#license)

---

## Architecture Overview

This system implements a microservices architecture with five services communicating over a secure internal Docker bridge network. External traffic flows through the React frontend and Node.js API gateway only, while backend services (Python collector, MongoDB, Redis) remain isolated on the internal network for security.

### System Architecture

```
                    ┌──────────────────────────────────────────┐
                    │         External Network                 │
                    └─────────────┬────────────────────────────┘
                                  │
                    ┌─────────────┴────────────┐
                    │         User             │
                    └─────────────┬────────────┘
                                  │
            ┌─────────────────────┴──────────────────────┐
            │                                            │
       ┌────▼─────┐                               ┌─────▼────┐
       │ Frontend │                               │   API    │
       │  React   │──────────HTTP/REST───────────▶│ Gateway  │
       │ :3000    │                               │  Node.js │
       └──────────┘                               │  :5000   │
                                                  └─────┬────┘
                                                        │
                    ┌───────────────────────────────────┼───────────────┐
                    │     Internal Docker Network       │               │
                    │     (172.28.0.0/16)               │               │
                    │                                   │               │
                    │                          ┌────────▼────────┐      │
                    │                          │     Python      │      │
                    │                          │   Collector     │      │
                    │                          │    FastAPI      │      │
                    │                          │  :8000 (INT)    │      │
                    │                          └────────┬────────┘      │
                    │                                   │               │
                    │            ┌──────────────────────┴──────┐        │
                    │            │                             │        │
                    │       ┌────▼─────┐                 ┌─────▼────┐   │
                    │       │ MongoDB  │                 │  Redis   │   │
                    │       │ :27017   │                 │  :6379   │   │
                    │       │  (INT)   │                 │  (INT)   │   │
                    │       └──────────┘                 └──────────┘   │
                    │                                                   │
                    └───────────────────────────────────────────────────┘

Legend: (INT) = Internal Only - Not Exposed to Host Network
```

### Service Communication Flow

1. **User Request**: Client sends HTTP request to Frontend (port 3000)
2. **API Call**: Frontend makes authenticated API call to Gateway (port 5000)
3. **Authentication**: Gateway validates JWT token
4. **Service Orchestration**: Gateway routes request to Python Collector (internal port 8000)
5. **Data Collection**: Collector scrapes product data, checks Redis cache
6. **Data Storage**: Results cached in Redis, user data stored in MongoDB
7. **Response**: Aggregated data returned through Gateway to Frontend

For comprehensive architecture documentation, see [ARCHITECTURE.md](infrastructure/ARCHITECTURE.md).

---

## Technology Stack

| Service              | Technology        | Version   |
| -------------------- | ----------------- | --------- |
| **Frontend**         | React             | 18.x      |
| **Node Gateway**     | Express.js        | 4.x       |
| **Python Collector** | FastAPI           | 0.108+    |
| **Database**         | MongoDB           | 7.0       |
| **Cache**            | Redis             | 7.x       |
| **Containerization** | Docker            | 24.x      |
| **Orchestration**    | Docker Compose    | 3.8       |
| **CI/CD**            | Jenkins           | Latest    |
| **Web Server**       | Nginx (for React) | Alpine    |
| **Runtime (Node)**   | Node.js           | 18 Alpine |
| **Runtime (Python)** | Python            | 3.11 Slim |

## Technology Stack

### Application Services

| Component         | Technology | Version | Purpose                                   |
| ----------------- | ---------- | ------- | ----------------------------------------- |
| Frontend          | React      | 18.x    | User interface and client-side logic      |
| API Gateway       | Express.js | 4.x     | Authentication, routing, rate limiting    |
| Collector Service | FastAPI    | 0.108+  | Product data aggregation and web scraping |
| Database          | MongoDB    | 7.0     | Persistent data storage                   |
| Cache             | Redis      | 7.x     | Session management and query caching      |

### Infrastructure

| Component        | Technology     | Version | Purpose                                 |
| ---------------- | -------------- | ------- | --------------------------------------- |
| Containerization | Docker         | 24.x    | Service isolation and deployment        |
| Orchestration    | Docker Compose | 2.x     | Multi-container management              |
| CI/CD            | Jenkins        | Latest  | Automated build and deployment pipeline |
| Web Server       | Nginx          | Alpine  | Static asset serving for React          |

### Runtime Environments

- **Node.js**: 18 (Alpine)
- **Python**: 3.11 (Slim)

---

## Prerequisites

### Required Software

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Git**: Latest stable version

### Optional

- **Jenkins**: For running CI/CD pipeline locally
- **OpenSSL**: For generating secure secrets

### Verify Installation

```bash
docker --version
docker compose version
git --version
```

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/ARaiiler/price-aggregator-microservices.git
cd price-aggregator-microservices
```

### 2. Environment Configuration

Copy the environment template and configure secrets:

```bash
cd infrastructure
cp .env.example .env
```

Edit `.env` file with your configuration. **Required variables**:

```bash
# Database
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=your_secure_mongodb_password
MONGO_DATABASE=priceaggregator

# Cache
REDIS_PASSWORD=your_secure_redis_password

# Authentication
JWT_SECRET=your_jwt_secret_key

# Service URLs (internal - no changes needed)
PYTHON_SERVICE_URL=http://python-collector:8000
FRONTEND_URL=http://localhost:3000
```

**Generate secure secrets**:

```bash
# JWT Secret
openssl rand -base64 32

# Passwords
openssl rand -hex 16
```

### 3. Build and Start Services

From the `infrastructure` directory:

```bash
docker compose up -d --build
```

This command:

- Builds Docker images for all services
- Creates internal network (172.28.0.0/16)
- Starts containers in detached mode
- Creates persistent volumes for MongoDB and Redis

### 4. Verify Deployment

```bash
# Check container status
docker compose ps

# View logs
docker compose logs -f

# Test health endpoints
curl http://localhost:5000/health
```

Expected output:

```json
{
  "uptime": 123.45,
  "message": "OK",
  "timestamp": 1708274400000,
  "service": "node-gateway",
  "environment": "development"
}
```

### 5. Access Services

- **Frontend**: <http://localhost:3000>
- **API Gateway**: <http://localhost:5000>
- **API Documentation**: <http://localhost:5000> (interactive)

**Note**: Python Collector (port 8000), MongoDB (port 27017), and Redis (port 6379) are not exposed to the host network for security reasons.

### 6. Stop Services

```bash
# Stop containers (data persists in volumes)
docker compose down

# Stop and remove volumes (deletes all data)
docker compose down -v
```

---

## Team Development Workflow

### Branch Protection Rules

This project enforces strict branch protection on the `main` branch:

- **No direct commits to main**: All changes must go through Pull Requests
- **CI must pass**: Jenkins pipeline must complete successfully before merge
- **Code review required**: At least one approval required for merge
- **Linear history**: Merge commits or squash merging only

### Development Process

#### 1. Create Feature Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

Branch naming conventions:

- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Production hotfixes
- `refactor/` - Code refactoring
- `docs/` - Documentation updates

#### 2. Develop Locally

Make your changes following these guidelines:

**Before writing code**:

- Review [ARCHITECTURE.md](infrastructure/ARCHITECTURE.md)
- Understand service boundaries
- Check existing patterns

**While coding**:

- Follow existing code style
- Add comments for complex logic
- Update documentation if needed

#### 3. Test Locally

**CRITICAL**: Always test changes locally before pushing.

```bash
# Navigate to infrastructure directory
cd infrastructure

# Rebuild affected services
docker compose up -d --build

# Run health checks
docker compose ps
curl http://localhost:5000/health

# Check logs for errors
docker compose logs -f node-gateway
docker compose logs -f python-collector

# Test your feature manually
# (Use Postman, curl, or browser as appropriate)
```

**For Node.js changes**:

```bash
cd node-gateway
npm test  # Run unit tests
npm run lint  # Check code style
```

**For Python changes**:

```bash
cd python-collector
pip install -r requirements.txt
pytest  # Run tests when implemented
```

#### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add product filtering endpoint

- Implemented /search/filter endpoint
- Added query parameter validation
- Updated API documentation
- Added unit tests"
```

Commit message format:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

#### 5. Push and Create Pull Request

```bash
# Push branch to remote
git push origin feature/your-feature-name
```

On GitHub:

1. Navigate to repository
2. Click "New Pull Request"
3. Select your feature branch
4. Fill in PR template:
   - Title: Brief description
   - Description: What changed and why
   - Testing: How you tested
   - Screenshots: If UI changes
5. Request reviewers
6. Link related issues

#### 6. CI/CD Pipeline Execution

Once PR is opened, Jenkins automatically:

1. Checks out your branch
2. Builds all Docker images
3. Runs security scans
4. Executes tests
5. Reports results in PR

**If pipeline fails**:

- Review Jenkins logs
- Fix issues locally
- Commit and push fixes
- Pipeline re-runs automatically

**If pipeline passes**:

- Request code review
- Address review comments
- Wait for approval

#### 7. Merge to Main

After approval and successful CI:

1. Squash commits (if multiple small commits)
2. Merge Pull Request
3. Delete feature branch
4. Pipeline deploys to staging/production (if configured)

### Working with Docker During Development

#### Clean Up Docker Resources

```bash
# Remove stopped containers
docker compose down

# Remove all containers and volumes (fresh start)
docker compose down -v

# Remove dangling images
docker image prune -f

# Remove all unused resources
docker system prune -a --volumes
```

#### View Service Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f node-gateway

# Last 100 lines
docker compose logs --tail=100 python-collector
```

#### Rebuild Single Service

```bash
# Rebuild only node-gateway
docker compose up -d --build node-gateway

# Rebuild without cache
docker compose build --no-cache python-collector
docker compose up -d python-collector
```

---

## CI/CD Pipeline

### Overview

The project uses Jenkins for continuous integration and continuous deployment. The pipeline is defined in [infrastructure/jenkins/Jenkinsfile](infrastructure/jenkins/Jenkinsfile) and automatically triggers on code changes.

### Pipeline Stages

```
┌─────────────────────────────────────────────────────────────┐
│                  Jenkins Pipeline Flow                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Checkout          │  Clone repository and get commit    │
│                       │  information for tagging            │
│                       │                                     │
│  2. Environment Check │  Verify Docker and dependencies     │
│                       │  are available                      │
│                       │                                     │
│  3. Build Services    │  Parallel build of all Docker       │
│     (Parallel)        │  images:                            │
│                       │  ├─ Frontend (React + Nginx)        │
│                       │  ├─ Node Gateway                    │
│                       │  └─ Python Collector                │
│                       │                                     │
│  4. Compose Build     │  Build using docker-compose.yml     │
│                       │  to verify service integration      │
│                       │                                     │
│  5. Security Scan     │  (Placeholder) Vulnerability scan   │
│                       │  Integration point for Trivy/Snyk   │
│                       │                                     │
│  6. Test              │  (Placeholder) Run test suites      │
│                       │  Integration point for pytest/jest  │
│                       │                                     │
│  7. Push Images       │  Push to Docker registry            │
│     (main only)       │  Only on main branch                │
│                       │                                     │
│  8. Deploy            │  Deploy to staging/production       │
│     (main only)       │  Only on main branch                │
│                       │                                     │
└─────────────────────────────────────────────────────────────┘
```

### Trigger Behavior

#### On Pull Request

When a Pull Request is created or updated:

1. **Webhook Trigger**: GitHub sends webhook to Jenkins
2. **Pipeline Execution**: Jenkins runs full pipeline up to (but not including) push/deploy stages
3. **Status Report**: Build status reported back to GitHub PR
4. **PR Checks**:
   - Green check: Pipeline passed, merge allowed
   - Red X: Pipeline failed, must fix before merge

#### On Main Branch Update

When code is merged to `main`:

1. **Full Pipeline**: All stages execute including push and deploy
2. **Image Tagging**: Docker images tagged with build number and commit hash
3. **Registry Push**: Images pushed to Docker registry (if configured)
4. **Deployment**: Services deployed to staging/production environment (if configured)

### Build Artifacts

Each successful build produces:

- **Docker Images**: Tagged with `{BUILD_NUMBER}-{COMMIT_HASH}` and `latest`
- **Build Logs**: Stored in Jenkins for debugging
- **Test Reports**: (When implemented) Test results and coverage reports

### Manual Pipeline Execution

To run the pipeline manually:

```bash
# Local build (without Jenkins)
cd infrastructure
docker compose build --no-cache

# Single service build
docker compose build node-gateway
```

### Pipeline Configuration

Key environment variables in Jenkinsfile:

- `DOCKER_IMAGE_PREFIX`: Prefix for Docker image names
- `COMPOSE_FILE`: Path to docker-compose.yml
- `COMPOSE_PROJECT_NAME`: Project name for Docker Compose

---

## Docker Architecture

### Network Isolation Strategy

The system uses a custom Docker bridge network (`internal-network`) with subnet `172.28.0.0/16` to isolate services from the host and external networks.

**Security Model**:

```
External Network (Internet)
        │
        │ Port exposures: 3000, 5000 only
        │
        ▼
┌───────────────────────────────────────────┐
│    Host Network (Docker Host)             │
│                                           │
│    Exposed Services:                      │
│    ├─ Frontend:3000                       │
│    └─ Node Gateway:5000                   │
│                                           │
└───────────────────────────────────────────┘
        │
        │ Bridge
        │
        ▼
┌───────────────────────────────────────────┐
│  Internal Docker Network                  │
│  (172.28.0.0/16)                          │
│                                           │
│  All Services (DNS Resolution):           │
│  ├─ frontend:3000                         │
│  ├─ node-gateway:5000                     │
│  ├─ python-collector:8000  (NOT EXPOSED)  │
│  ├─ mongodb:27017          (NOT EXPOSED)  │
│  └─ redis:6379             (NOT EXPOSED)  │
│                                           │
└───────────────────────────────────────────┘
```

### Service-to-Service Communication

Services communicate using **container names as hostnames**:

**Example from Node Gateway**:

```javascript
// Connect to Python Collector
const PYTHON_URL = process.env.PYTHON_SERVICE_URL;
// Value: "http://python-collector:8000"

// Connect to MongoDB
const MONGO_URI = process.env.MONGO_URI;
// Value: "mongodb://admin:password@mongodb:27017/priceaggregator"

// Connect to Redis
const REDIS_URL = process.env.REDIS_URL;
// Value: "redis://:password@redis:6379/0"
```

**Why DNS instead of IP addresses**:

- Container IPs can change on restart
- DNS resolution handles service discovery
- Easy to scale and replace containers
- Works with orchestration platforms (Kubernetes, Swarm)

### Why MongoDB and Redis Are Not Exposed

**Security Benefits**:

1. **Reduced Attack Surface**: Database ports not accessible from internet
2. **Defense in Depth**: Even if gateway is compromised, databases remain isolated
3. **Compliance**: Aligns with security best practices (CIS benchmarks)
4. **Principle of Least Privilege**: Only services that need database access can reach it

**Access Pattern**:

- Application logic in Node Gateway queries MongoDB
- Python Collector caches data in Redis
- External clients cannot directly connect to databases
- Administration done via `docker exec` into containers

### Health Checks

All custom services implement Docker health checks:

```yaml
healthcheck:
  test: [health check command]
  interval: 30s # Run check every 30 seconds
  timeout: 5s # Fail if no response in 5 seconds
  retries: 3 # Mark unhealthy after 3 failures
  start_period: 10s # Grace period after container start
```

**Purpose**:

- **Dependency Management**: Containers wait for dependencies to be healthy
- **Auto-Recovery**: Orchestrator can restart unhealthy containers
- **Load Balancing**: Remove unhealthy instances from load balancer pool
- **Monitoring**: Health status visible in `docker compose ps`

**Dependency Chain**:

```
Frontend  →  depends_on  →  Node Gateway  →  depends_on  →  Python Collector
                              ↓                               ↓
                         depends_on                      depends_on
                              ↓                               ↓
                          MongoDB                         Redis
                          (healthy)                       (healthy)
```

### Data Persistence

Persistent data stored in Docker named volumes:

- `mongodb_data`: MongoDB database files
- `mongodb_config`: MongoDB configuration
- `redis_data`: Redis RDB snapshots and AOF logs

**Volume Management**:

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect infrastructure_mongodb_data

# Backup volume
docker run --rm -v infrastructure_mongodb_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/mongodb-backup.tar.gz /data

# Restore volume
docker run --rm -v infrastructure_mongodb_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/mongodb-backup.tar.gz -C /
```

---

## Environment Configuration

### Environment Variables Reference

#### Required Variables

| Variable              | Description                   | Example               | Security Level |
| --------------------- | ----------------------------- | --------------------- | -------------- |
| `MONGO_ROOT_USERNAME` | MongoDB admin username        | `admin`               | Low            |
| `MONGO_ROOT_PASSWORD` | MongoDB admin password        | `h8Kf2@mPq9`          | **CRITICAL**   |
| `MONGO_DATABASE`      | Database name                 | `priceaggregator`     | Low            |
| `REDIS_PASSWORD`      | Redis authentication password | `r9Xm#pL2kQ`          | **HIGH**       |
| `JWT_SECRET`          | Secret key for JWT signing    | `base64encodedkey...` | **CRITICAL**   |

#### Optional Configuration

| Variable             | Description             | Default                        |
| -------------------- | ----------------------- | ------------------------------ |
| `ENVIRONMENT`        | Application environment | `production`                   |
| `NODE_ENV`           | Node.js environment     | `production`                   |
| `FRONTEND_PORT`      | Frontend exposed port   | `3000`                         |
| `NODE_GATEWAY_PORT`  | Gateway exposed port    | `5000`                         |
| `PYTHON_SERVICE_URL` | Python collector URL    | `http://python-collector:8000` |

### Security Best Practices

#### Secret Generation

```bash
# Strong JWT secret (256-bit)
openssl rand -base64 32

# Strong password (128-bit)
openssl rand -hex 16

# Alternative: Use UUIDs
uuidgen
```

#### Secret Storage

**NEVER**:

- Commit `.env` file to version control
- Share secrets via email or chat
- Hardcode secrets in application code
- Use default or example passwords in production

**ALWAYS**:

- Add `.env` to `.gitignore` (already done)
- Use unique secrets per environment
- Rotate secrets regularly
- Use secret management tools (Vault, AWS Secrets Manager) in production
- Grant secrets access on need-to-know basis

#### Environment File Security

```bash
# Restrict .env file permissions (Linux/macOS)
chmod 600 infrastructure/.env

# Verify .env is ignored
git check-ignore infrastructure/.env
# Should output: infrastructure/.env
```

### Environment Template

Copy `infrastructure/.env.example` to `infrastructure/.env`:

```bash
# ============================================
# Database Configuration
# ============================================
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=CHANGE_ME_TO_SECURE_PASSWORD
MONGO_DATABASE=priceaggregator
MONGO_URI=mongodb://admin:CHANGE_ME@mongodb:27017/priceaggregator?authSource=admin

# ============================================
# Redis Configuration
# ============================================
REDIS_PASSWORD=CHANGE_ME_TO_SECURE_PASSWORD
REDIS_URL=redis://:CHANGE_ME@redis:6379/0

# ============================================
# JWT Authentication
# ============================================
JWT_SECRET=CHANGE_ME_TO_SECURE_SECRET_MINIMUM_256_BITS

# ============================================
# Service Configuration
# ============================================
ENVIRONMENT=production
NODE_ENV=production
FRONTEND_PORT=3000
NODE_GATEWAY_PORT=5000
PYTHON_SERVICE_URL=http://python-collector:8000
FRONTEND_URL=http://localhost:3000
```

---

## API Documentation

> **Contract Notice** — This section is the official REST API contract between the **React Frontend** (`http://localhost:3000`) and the **Node.js API Gateway** (`http://localhost:5000`). Both sides **must** honour the request/response shapes defined here. Any change to an endpoint path, field name, type, or HTTP status code is a **breaking change** and requires a coordinated update on both sides before merging.

---

### Base URL

| Environment | URL |
|-------------|-----|
| Local development | `http://localhost:5000` |
| Inside Docker network | `http://node-gateway:5000` |

The frontend resolves the base URL from the `REACT_APP_API_URL` environment variable (defaults to `http://localhost:5000`).

```javascript
// frontend/src/App.js
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
```

---

### Authentication Header

Protected endpoints require the JWT obtained from `POST /auth/login` sent as a Bearer token:

```
Authorization: Bearer <jwt_token>
```

| Scenario | Status | Response body |
|----------|--------|---------------|
| Header missing or not `Bearer …` | `401` | `{ "error": { "message": "No token provided", "status": 401 } }` |
| Token invalid or expired | `403` | `{ "error": { "message": "Invalid or expired token", "status": 403 } }` |

---

### Endpoint Summary

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/` | No | Service info / liveness ping |
| `GET` | `/health` | No | Gateway health check |
| `POST` | `/auth/register` | No | Create a new user account |
| `POST` | `/auth/login` | No | Log in and receive a JWT |
| `GET` | `/search?query=` | No* | Search products by keyword |

> \* `/search` does not currently enforce the auth middleware, but the middleware is wired and ready. The frontend **should always send the token** for forward compatibility.

---

### `GET /`

Returns basic service metadata. No authentication required.

**Response** `200 OK`

```json
{
  "service": "Node Gateway",
  "version": "1.0.0",
  "status": "running"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `service` | `string` | Always `"Node Gateway"` |
| `version` | `string` | Semantic version of the gateway |
| `status` | `string` | Always `"running"` when reachable |

---

### `GET /health`

Live health status of the Node.js Gateway. Used by Docker Compose health checks and the Jenkins pipeline. No authentication required.

**Request**

```http
GET /health HTTP/1.1
Host: localhost:5000
```

**Response** `200 OK`

```json
{
  "status": "healthy",
  "service": "node-gateway",
  "timestamp": "2026-02-20T10:00:00.000Z",
  "uptime": 12345.67,
  "environment": "development"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | Always `"healthy"` while the process is running |
| `service` | `string` | Always `"node-gateway"` |
| `timestamp` | `string` | ISO 8601 UTC time of the response |
| `uptime` | `number` | Process uptime in seconds (`process.uptime()`) |
| `environment` | `string` | Value of `NODE_ENV` (e.g. `"development"`) |

---

### `POST /auth/register`

Create a new user account. A JWT is **not** issued on registration — call `POST /auth/login` afterwards.

**Request**

```http
POST /auth/register HTTP/1.1
Host: localhost:5000
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecureP@ssw0rd"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `email` | `string` | ✓ | Valid e-mail address |
| `password` | `string` | ✓ | Non-empty; hashed with bcrypt (cost 10) before storage |

**Response** `201 Created`

```json
{
  "message": "User registered successfully",
  "user": {
    "email": "user@example.com"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `message` | `string` | Human-readable confirmation |
| `user.email` | `string` | Echo of the registered e-mail |

**Error responses**

| Status | Condition | Body |
|--------|-----------|------|
| `400` | `email` or `password` missing | `{ "error": { "message": "Email and password are required", "status": 400 } }` |
| `500` | Unexpected server error | `{ "error": { "message": "Registration failed", "status": 500 } }` |

---

### `POST /auth/login`

Authenticate with email and password. Returns a signed JWT valid for **24 hours**.

**Request**

```http
POST /auth/login HTTP/1.1
Host: localhost:5000
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecureP@ssw0rd"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `email` | `string` | ✓ | Must match a registered account |
| `password` | `string` | ✓ | Plain-text; compared against stored bcrypt hash |

**Response** `200 OK`

```json
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": "24h"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `message` | `string` | Human-readable confirmation |
| `token` | `string` | Signed JWT — store in memory or `sessionStorage`; attach to all subsequent requests |
| `expiresIn` | `string` | Token lifetime. Always `"24h"` |

**Decoded JWT payload**

```json
{
  "email": "user@example.com",
  "userId": "placeholder-id",
  "iat": 1708258200,
  "exp": 1708344600
}
```

**Frontend usage** (`App.js`)

```javascript
const response = await axios.post(`${API_URL}/auth/login`, { email, password });
const { token } = response.data;
// Attach to protected requests:
// axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
```

**Error responses**

| Status | Condition | Body |
|--------|-----------|------|
| `400` | `email` or `password` missing | `{ "error": { "message": "Email and password are required", "status": 400 } }` |
| `500` | Unexpected server error | `{ "error": { "message": "Login failed", "status": 500 } }` |

---

### `GET /search`

Search for products by keyword. The gateway forwards the query to the internal Python Collector (`POST http://python-collector:8000/internal/search`) and returns the aggregated, normalised results.

**Request**

```http
GET /search?query=laptop HTTP/1.1
Host: localhost:5000
Authorization: Bearer <jwt_token>
```

| Query parameter | Type | Required | Notes |
|-----------------|------|----------|-------|
| `query` | `string` | ✓ | Non-empty; HTML-escaped by the gateway before forwarding |

**Frontend usage** (`App.js`)

```javascript
const response = await axios.get(`${API_URL}/search`, {
  params: { query: searchQuery }
});
const products = response.data.results; // rendered as result cards
```

**Response** `200 OK`

```json
{
  "success": true,
  "query": "laptop",
  "results": [
    {
      "name": "Laptop - Source A Edition",
      "price": 299.99,
      "source": "Source A",
      "url": "https://source-a.example.com/products/laptop-123",
      "currency": "USD",
      "in_stock": true,
      "timestamp": "2026-02-20T10:30:00.000Z"
    },
    {
      "name": "Laptop - Source B Edition",
      "price": 319.99,
      "source": "Source B",
      "url": "https://source-b.example.com/products/laptop-456",
      "currency": "USD",
      "in_stock": false,
      "timestamp": "2026-02-20T10:30:01.000Z"
    }
  ],
  "cached": false,
  "sources_queried": 2,
  "timestamp": "2026-02-20T10:30:05.000Z"
}
```

**Top-level fields**

| Field | Type | Description |
|-------|------|-------------|
| `success` | `boolean` | `true` when the collector returned a valid response |
| `query` | `string` | Echo of the `query` parameter sent by the frontend |
| `results` | `array` | List of product objects (see schema below) |
| `cached` | `boolean` | `true` if the response came from the Redis cache |
| `sources_queried` | `number` | Number of price sources the collector queried |
| `timestamp` | `string` | ISO 8601 UTC time the gateway assembled the response |

**Product object schema** (each item in `results`)

| Field | Type | Description | Frontend renders |
|-------|------|-------------|-----------------|
| `name` | `string` | Product title | `<h3>{item.name}</h3>` |
| `price` | `number` | Price as a decimal number | `<p>${item.price}</p>` |
| `source` | `string` | Store / scrape-source name | `<p>Source: {item.source}</p>` |
| `url` | `string` | Direct link to the product listing | — |
| `currency` | `string` | ISO 4217 code (e.g. `"USD"`) | — |
| `in_stock` | `boolean` | Stock availability at scrape time | — |
| `timestamp` | `string` | ISO 8601 UTC time the price was scraped | — |

**Error responses**

| Status | Condition | Body |
|--------|-----------|------|
| `400` | `query` param missing or empty | `{ "errors": [{ "msg": "Invalid value", "param": "query", "location": "query" }] }` |
| `503` | Python Collector is unreachable (`ECONNREFUSED`) | `{ "success": false, "message": "Product collector service unavailable", "error": "Service temporarily down" }` |
| `500` | Any other gateway error | `{ "success": false, "message": "Failed to fetch products", "error": "<error details>" }` |

---

### Global Error Envelope

All non-validation errors from the gateway use this shape:

```json
{
  "error": {
    "message": "Human-readable description",
    "status": 400
  }
}
```

**404 — Route not found**

```json
{
  "error": {
    "message": "Route not found",
    "status": 404
  }
}
```

---

## Production Notes

### Pre-Production Checklist

Before deploying to production:

- [ ] **Secrets**: All environment variables use strong, unique values
- [ ] **Branch Protection**: Main branch protected with required reviews
- [ ] **CI/CD**: Pipeline configured and tested
- [ ] **Monitoring**: Health checks verified for all services
- [ ] **Backups**: Database backup strategy implemented
- [ ] **Logging**: Centralized logging configured (if applicable)
- [ ] **Security**: Docker images scanned for vulnerabilities
- [ ] **Documentation**: API documentation up to date
- [ ] **Testing**: All tests passing in CI
- [ ] **Resources**: Container resource limits configured

### Security Hardening

#### Never Commit Secrets

```bash
# Verify .gitignore is working
git status

# .env should NOT appear in untracked files
# If it does, add to .gitignore immediately
```

#### Use Strong Credentials

- **Passwords**: Minimum 16 characters, mix of alphanumeric and symbols
- **JWT Secrets**: Minimum 256 bits (32 bytes base64 encoded)
- **Unique per environment**: Dev, staging, and production use different secrets

#### Branch Protection Configuration

On GitHub, configure main branch protection:

1. Go to repository settings → Branches
2. Add rule for `main` branch:
   - ✓ Require pull request before merging
   - ✓ Require approvals: 1+
   - ✓ Require status checks to pass
   - ✓ Require branches to be up to date
   - ✓ Include administrators
   - ✓ Restrict who can push to matching branches

### Keep CI Green

**Team Responsibility**: Maintain passing CI at all times.

If CI fails on main:

1. **Immediate action**: Create hotfix branch
2. **Fix forward**: Push fix to restore green status
3. **Post-mortem**: Understand why CI passed on PR but failed on main
4. **Prevent recurrence**: Improve testing or CI configuration

### Docker Resource Management

#### Clean Up Regularly

```bash
# Remove unused containers
docker container prune -f

# Remove unused images
docker image prune -a -f

# Remove unused volumes (WARNING: deletes data)
docker volume prune -f

# Complete cleanup
docker system prune -a --volumes -f
```

#### Monitor Disk Usage

```bash
# Check Docker disk usage
docker system df

# Detailed usage per type
docker system df -v
```

---

## Future Enhancements

### Immediate Improvements

- [ ] **Unit & Integration Tests**: Jest for Node.js, Pytest for Python
- [ ] **Code Coverage**: Minimum 80% coverage requirement
- [ ] **API Documentation**: OpenAPI/Swagger integration
- [ ] **Input Validation**: Enhanced request validation with Joi/Pydantic
- [ ] **Error Handling**: Standardized error response format

### Infrastructure

- [ ] **Staging Environment**: Dedicated staging deployment for pre-production testing
- [ ] **Kubernetes Migration**: Helm charts for Kubernetes deployment
- [ ] **Service Mesh**: Istio or Linkerd for advanced traffic management
- [ ] **Container Registry**: Private Docker registry (Harbor, ECR, or GCR)
- [ ] **SSL/TLS**: HTTPS support with Let's Encrypt certificates

### Observability

- [ ] **Monitoring**: Prometheus for metrics collection
- [ ] **Visualization**: Grafana dashboards for service health
- [ ] **Centralized Logging**: ELK stack (Elasticsearch, Logstash, Kibana) or Loki
- [ ] **Distributed Tracing**: Jaeger or Zipkin for request tracing
- [ ] **Alerting**: PagerDuty or Opsgenie integration for critical alerts

### Automation

- [ ] **Automated Versioning**: Semantic versioning with git tags
- [ ] **Changelog Generation**: Automated CHANGELOG.md from commits
- [ ] **Dependency Updates**: Renovate or Dependabot for dependency management
- [ ] **Security Scanning**: Trivy, Snyk, or Clair for vulnerability scanning
- [ ] **Performance Testing**: k6 or Artillery for load testing

### Features

- [ ] **Real Web Scraping**: Integration with actual e-commerce platforms
- [ ] **User Preferences**: Saved searches and price alerts
- [ ] **Price History**: Track price changes over time
- [ ] **Email Notifications**: Alerts for price drops
- [ ] **Admin Dashboard**: Service management and analytics
- [ ] **Rate Limiting**: Per-user API quotas
- [ ] **GraphQL API**: Optional GraphQL layer for flexible queries

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions are welcome. Please read the [Team Development Workflow](#team-development-workflow) section before contributing.

For major changes, please open an issue first to discuss proposed changes.

---

## Support

For questions and issues:

- **Issues**: <https://github.com/yourusername/price-aggregator-microservices/issues>
- **Discussions**: <https://github.com/yourusername/price-aggregator-microservices/discussions>
- **Documentation**: [ARCHITECTURE.md](infrastructure/ARCHITECTURE.md)

---

**Built for educational purposes demonstrating microservices architecture, containerization, and CI/CD automation.**
