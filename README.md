# 🛒 Price Aggregator Microservices

A production-ready microservices architecture for aggregating and comparing product prices across multiple e-commerce platforms. Built with modern technologies and following industry best practices for scalability, security, and maintainability.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)](https://www.docker.com/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-Jenkins-red.svg)](https://www.jenkins.io/)

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Services](#services)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Environment Configuration](#environment-configuration)
- [API Documentation](#api-documentation)
- [CI/CD Pipeline](#cicd-pipeline)
- [Security](#security)
- [Monitoring](#monitoring)
- [Contributing](#contributing)
- [License](#license)

---

## 🏗️ Architecture Overview

This project implements a microservices architecture with three main services communicating over a secure internal network:

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│   Frontend  │─────▶│ Node Gateway │─────▶│ Python Collector│
│   (React)   │      │  (Express)   │      │   (FastAPI)     │
│   Port 3000 │      │  Port 5000   │      │ Port 8000       │
└─────────────┘      └──────────────┘      │ (Internal Only) │
                            │               └─────────────────┘
                            │
                     ┌──────┴──────┐
                     │             │
                ┌────▼───┐    ┌────▼────┐
                │ MongoDB│    │  Redis  │
                │        │    │         │
                └────────┘    └─────────┘
```

For detailed architecture documentation, see [ARCHITECTURE.md](infrastructure/ARCHITECTURE.md).

---

## 🎯 Services

### 1. **Frontend** (React)
- **Port:** 3000
- **Description:** User-facing web interface for product search and price comparison
- **Key Features:**
  - Modern, responsive UI
  - Real-time product search
  - Price comparison visualization
  - Integration with API Gateway

### 2. **Node Gateway** (Express.js)
- **Port:** 5000
- **Description:** API Gateway with JWT authentication and request routing
- **Key Features:**
  - JWT-based authentication
  - Rate limiting
  - Request validation
  - Service orchestration
  - Helmet security headers
  - CORS configuration

### 3. **Python Collector** (FastAPI)
- **Port:** 8000 (Internal only)
- **Description:** Product data collection and scraping service
- **Key Features:**
  - Multi-source product scraping
  - Data normalization
  - Internal-only access (not exposed publicly)
  - Async processing
  - Redis caching

### 4. **MongoDB**
- **Port:** 27017 (Internal only)
- **Description:** Primary database for user data and product cache
- **Features:**
  - Persistent storage
  - Authenticated access
  - Named volume for data persistence

### 5. **Redis**
- **Port:** 6379 (Internal only)
- **Description:** In-memory cache for session management and query caching
- **Features:**
  - Password-protected
  - Data persistence
  - Fast cache lookups

---

## 🛠️ Technology Stack

| Service | Technology | Version |
|---------|-----------|---------|
| **Frontend** | React | 18.x |
| **Node Gateway** | Express.js | 4.x |
| **Python Collector** | FastAPI | 0.108+ |
| **Database** | MongoDB | 7.0 |
| **Cache** | Redis | 7.x |
| **Containerization** | Docker | 24.x |
| **Orchestration** | Docker Compose | 3.8 |
| **CI/CD** | Jenkins | Latest |
| **Web Server** | Nginx (for React) | Alpine |
| **Runtime (Node)** | Node.js | 18 Alpine |
| **Runtime (Python)** | Python | 3.11 Slim |

---

## ✅ Prerequisites

Before running this project, ensure you have:

- **Docker:** Version 20.10 or higher
- **Docker Compose:** Version 2.0 or higher
- **Git:** For cloning the repository
- **(Optional) Jenkins:** For CI/CD pipeline

### Verify Installation

```bash
docker --version
docker compose version
```

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/price-aggregator-microservices.git
cd price-aggregator-microservices
```

### 2. Configure Environment

```bash
cd infrastructure
cp .env.example .env
```

Edit `.env` and set your values:

```bash
# Example values
MONGO_ROOT_PASSWORD=your_secure_password
REDIS_PASSWORD=your_redis_password
JWT_SECRET=$(openssl rand -base64 32)
```

### 3. Build and Run Services

```bash
docker compose up -d --build
```

### 4. Verify Services

```bash
# Check all containers are running
docker compose ps

# Check logs
docker compose logs -f

# Test health endpoints
curl http://localhost:5000/health
curl http://localhost:3000
```

### 5. Access the Application

- **Frontend:** http://localhost:3000
- **API Gateway:** http://localhost:5000
- **API Docs (Gateway):** http://localhost:5000
- **Python API Docs:** http://python-collector:8000/docs (internal only, access via Gateway)

---

## 💻 Development Setup

### Running Individual Services

#### Frontend
```bash
cd frontend
npm install
npm start
```

#### Node Gateway
```bash
cd node-gateway
npm install
npm run dev
```

#### Python Collector
```bash
cd python-collector
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## ⚙️ Environment Configuration

### Required Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_ROOT_PASSWORD` | MongoDB root password | - |
| `REDIS_PASSWORD` | Redis authentication password | - |
| `JWT_SECRET` | Secret key for JWT signing | - |
| `ENVIRONMENT` | Application environment | production |
| `NODE_ENV` | Node.js environment | production |
| `FRONTEND_PORT` | Frontend exposed port | 3000 |
| `NODE_GATEWAY_PORT` | Gateway exposed port | 5000 |

### Generate Secure Secrets

```bash
# Generate JWT secret
openssl rand -base64 32

# Generate random password
openssl rand -hex 16
```

---

## 📚 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123"
}

Response:
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "message": "Login successful"
}
```

### Search Endpoints

#### Search Products
```http
GET /search?query=laptop
Authorization: Bearer <token>

Response:
{
  "success": true,
  "query": "laptop",
  "results": [
    {
      "name": "Laptop - Amazon Edition",
      "price": 299.99,
      "source": "Amazon",
      "url": "https://amazon.com/...",
      "currency": "USD",
      "in_stock": true
    }
  ],
  "total_results": 3
}
```

### Health Check
```http
GET /health

Response:
{
  "status": "healthy",
  "service": "node-gateway",
  "uptime": 12345.67
}
```

---

## 🔄 CI/CD Pipeline

### Jenkins Pipeline

The project includes a complete Jenkins pipeline for automated builds and deployments.

**Location:** `infrastructure/jenkins/Jenkinsfile`

### Pipeline Stages

1. **Checkout:** Clone repository and get commit info
2. **Environment Check:** Verify Docker and dependencies
3. **Build Services:** Build all Docker images in parallel
4. **Docker Compose Build:** Build with Compose configuration
5. **Security Scan:** Run security vulnerability scans
6. **Test:** Execute unit and integration tests
7. **Push Images:** Push to Docker registry (main branch only)
8. **Deploy:** Deploy to production environment (main branch only)

### Running the Pipeline

```bash
# Configure Jenkins with this repository
# The Jenkinsfile will be automatically detected

# Or run locally
cd infrastructure
docker compose build
```

### Pipeline Features

- ✅ Parallel builds for faster execution
- ✅ Security scanning integration points
- ✅ Automated testing
- ✅ Docker image tagging with build number and commit hash
- ✅ Post-build cleanup
- ✅ Notification hooks (configurable)

---

## 🔒 Security

### Security Measures Implemented

1. **Container Security**
   - Non-root user execution in all containers
   - Minimal base images (Alpine, Slim)
   - Multi-stage builds to reduce attack surface
   - Security scanning integration points

2. **Network Security**
   - Internal bridge network for service communication
   - Python collector not exposed publicly
   - MongoDB and Redis not exposed externally
   - Proper CORS configuration

3. **Application Security**
   - JWT authentication
   - Password hashing with bcrypt
   - Rate limiting on API endpoints
   - Helmet.js security headers
   - Input validation and sanitization
   - No hardcoded secrets

4. **Data Security**
   - Environment variables for all secrets
   - .env files excluded from git
   - Persistent encrypted volumes

### Security Best Practices

```bash
# Scan Docker images for vulnerabilities
docker scan price-aggregator-frontend:latest

# Use strong passwords
openssl rand -base64 32 > .secrets/jwt_secret

# Keep dependencies updated
npm audit fix
pip list --outdated
```

---

## 📊 Monitoring

### Health Checks

All services include health check endpoints:

```bash
# Node Gateway
curl http://localhost:5000/health

# Frontend
curl http://localhost:3000

# Check Docker health status
docker compose ps
```

### Logging

```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f node-gateway
docker compose logs -f python-collector

# View last 100 lines
docker compose logs --tail=100
```

### Metrics (Future Enhancement)

Consider integrating:
- Prometheus for metrics collection
- Grafana for visualization
- ELK Stack for log aggregation
- Jaeger for distributed tracing

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines

- Follow existing code style
- Add tests for new features
- Update documentation
- Ensure all tests pass
- Keep commits atomic and descriptive

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Your Name** - *Initial work*

---

## 🙏 Acknowledgments

- Built as an academic project for microservices architecture learning
- Inspired by modern e-commerce platforms
- Community contributions and feedback

---

## 📞 Support

For questions and support:

- Open an issue on GitHub
- Email: support@example.com
- Documentation: [Wiki](https://github.com/yourusername/price-aggregator-microservices/wiki)

---

## 🗺️ Roadmap

- [ ] Implement real web scraping for major e-commerce sites
- [ ] Add user authentication with MongoDB
- [ ] Implement caching layer with Redis
- [ ] Add API rate limiting per user
- [ ] Integrate payment processing
- [ ] Add email notifications for price drops
- [ ] Implement GraphQL API layer
- [ ] Add Kubernetes deployment manifests
- [ ] Integrate monitoring and alerting
- [ ] Add end-to-end tests
- [ ] Implement service mesh (Istio/Linkerd)

---

**Built with ❤️ using modern microservices architecture**
