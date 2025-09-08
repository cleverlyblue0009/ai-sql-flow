# DataFlow AI Enterprise Platform - Backend

A comprehensive, enterprise-grade backend API for AI-powered data quality analysis, cleaning, and SQL migration between different database platforms.

## 🚀 Features

### 🔐 Authentication & Authorization
- JWT token-based authentication with refresh tokens
- Role-based access control (Admin, Engineer, Analyst)
- OAuth2 integration support (Google, GitHub)
- Comprehensive audit logging
- Rate limiting and security middleware

### 📊 Data Quality Analysis
- **AI-Powered Analysis**: ML-based duplicate detection, outlier detection with isolation forests
- **Missing Value Analysis**: Neural network-based imputation suggestions
- **Pattern Recognition**: NLP-based data type inference and validation
- **Quality Metrics**: Completeness, accuracy, consistency, validity, uniqueness scores
- **File Support**: CSV, Excel, JSON, Parquet, TSV (up to 500MB)

### 🧹 Data Cleaning
- **Automated Cleaning**: AI-suggested cleaning operations
- **Custom Operations**: Remove duplicates, fill missing values, remove outliers
- **Format Standardization**: Consistent data formatting and type correction
- **Preview Mode**: Test cleaning operations before applying
- **Background Processing**: Celery-based async processing

### 🔄 SQL Migration
- **Neural Translation**: SQL dialect conversion using transformer models
- **Database Support**: PostgreSQL, MySQL, Snowflake, SQL Server, Oracle
- **Semantic Validation**: BERT-based similarity checking
- **Performance Optimization**: Query optimization using ML
- **Schema Mapping**: Intelligent schema mapping and conversion
- **Progress Tracking**: Real-time migration progress monitoring

### 📈 Dashboard & Analytics
- **Real-time Metrics**: Data quality scores, migration status, cost savings
- **Activity Feed**: Live updates on platform activities
- **Performance Analytics**: Query performance improvements, resource usage
- **Cost Analysis**: ROI calculations and savings tracking

### ⚡ Real-time Communication
- **WebSocket Support**: Live updates for long-running operations
- **Progress Broadcasting**: Real-time job progress updates
- **Activity Notifications**: Instant activity feed updates
- **System Alerts**: System-wide notifications

## 🛠️ Technology Stack

- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with Redis caching
- **AI/ML**: TensorFlow, PyTorch, scikit-learn, Transformers
- **Queue System**: Celery with Redis broker
- **Storage**: AWS S3 / MinIO support
- **Monitoring**: Prometheus metrics, structured logging
- **Security**: JWT tokens, encrypted credentials storage

## 📋 Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Docker & Docker Compose (recommended)

## 🚀 Quick Start

### Using Docker Compose (Recommended)

1. **Clone and setup environment**:
```bash
git clone <repository-url>
cd dataflow-ai-backend
cp .env.example .env
# Edit .env with your configuration
```

2. **Start all services**:
```bash
docker-compose up -d
```

3. **Generate mock data** (optional):
```bash
docker-compose exec api python scripts/generate_mock_data.py
```

4. **Access the API**:
- API Documentation: http://localhost:8000/docs
- Admin Interface: http://localhost:8000/admin
- Monitoring (Flower): http://localhost:5555
- Grafana: http://localhost:3000 (admin/admin)

### Manual Installation

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Setup databases**:
```bash
# PostgreSQL
createdb ai_data_platform

# Redis (start service)
redis-server
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. **Initialize database**:
```bash
python -c "from app.database import create_tables; create_tables()"
```

5. **Start services**:
```bash
# API Server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Celery Worker (separate terminal)
celery -A app.tasks.data_quality_tasks.celery_app worker --loglevel=info

# Celery Flower (separate terminal)
celery -A app.tasks.data_quality_tasks.celery_app flower --port=5555
```

## 📚 API Documentation

### Authentication Endpoints
```
POST /auth/register       - Register new user
POST /auth/login          - User login
POST /auth/refresh        - Refresh access token
GET  /auth/me             - Get current user info
POST /auth/logout         - User logout
```

### Dashboard Endpoints
```
GET  /dashboard/metrics        - Get dashboard metrics
GET  /dashboard/activities     - Get recent activities
GET  /dashboard/quick-stats    - Get quick statistics
GET  /dashboard/system-status  - Get system health status
GET  /dashboard/overview       - Get complete dashboard data
```

### Data Quality Endpoints
```
POST /data-quality/upload      - Upload data files
POST /data-quality/analyze     - Start quality analysis
GET  /data-quality/report/{id} - Get analysis report
POST /data-quality/clean       - Start cleaning process
GET  /data-quality/status/{id} - Get job status
```

### SQL Migration Endpoints
```
GET  /migration/databases           - Get supported databases
POST /migration/test-connection     - Test database connection
POST /migration/setup               - Setup migration project
POST /migration/translate-sql       - Translate SQL queries
POST /migration/start               - Start migration process
GET  /migration/progress/{id}       - Get migration progress
GET  /migration/performance/{id}    - Get performance analysis
```

### WebSocket Endpoints
```
WS   /ws                   - User WebSocket connection
WS   /ws/admin            - Admin WebSocket connection
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/db_name
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-32-char-encryption-key

# File Storage
MAX_FILE_SIZE_MB=500
S3_BUCKET_NAME=your-bucket-name

# AI/ML APIs (optional)
OPENAI_API_KEY=your-openai-key
HUGGINGFACE_API_KEY=your-huggingface-key
```

### Database Schema

The application uses SQLAlchemy models with the following main entities:

- **Users**: User accounts with role-based access
- **Projects**: Data analysis and migration projects
- **DataProfiles**: File analysis results and quality metrics
- **Jobs**: Background task tracking
- **MigrationLogs**: SQL migration history and progress
- **Connections**: Database connection configurations
- **AuditLogs**: Comprehensive audit trail

## 📊 Monitoring & Logging

### Health Checks
```bash
curl http://localhost:8000/health
```

### Metrics
- Prometheus metrics: http://localhost:8000/metrics
- Grafana dashboards: http://localhost:3000
- Application logs: Structured JSON logging

### Background Jobs
- Celery Flower: http://localhost:5555
- Job monitoring via WebSocket or REST API

## 🧪 Testing

### Run Tests
```bash
# Unit tests
pytest

# Integration tests
pytest tests/integration/

# Coverage report
pytest --cov=app tests/
```

### Mock Data Generation
```bash
python scripts/generate_mock_data.py
```

This creates:
- 15 test users (admin/engineer/analyst roles)
- 25 sample projects
- 150 data profiles with quality issues
- 60 migration scenarios
- 300 background jobs
- Sample CSV files with realistic data quality issues

### Test Credentials
```
Admin: admin@dataflow.ai / secret
Engineer: engineer1@dataflow.ai / secret
Analyst: Use any generated user / secret
```

## 🔒 Security Features

- **Authentication**: JWT tokens with refresh mechanism
- **Authorization**: Role-based access control (RBAC)
- **Encryption**: Database credentials encrypted at rest
- **Rate Limiting**: API endpoint protection
- **Input Validation**: Comprehensive request validation
- **Audit Logging**: All actions logged for compliance
- **CORS**: Configurable cross-origin resource sharing

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**:
```bash
# Set production environment variables
export ENVIRONMENT=production
export DEBUG=false
export SECRET_KEY=your-production-secret-key
```

2. **Database Migration**:
```bash
# Run database migrations
python -c "from app.database import create_tables; create_tables()"
```

3. **SSL/TLS**:
- Configure reverse proxy (nginx/traefik)
- Use SSL certificates
- Set secure cookie flags

4. **Scaling**:
- Multiple API instances behind load balancer
- Separate Celery workers for background tasks
- Redis cluster for high availability
- PostgreSQL read replicas

### Docker Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 📈 Performance Specifications

- **Response Time**: <200ms for simple queries, <2s for complex operations
- **Throughput**: Handle 1000+ concurrent users
- **File Processing**: Support files up to 500MB, process 1M+ records
- **Reliability**: 99.9% uptime with comprehensive error recovery
- **Scalability**: Horizontal scaling with load balancers

## 🤝 Integration

### Frontend Integration
The backend is designed to work seamlessly with React/Vue/Angular frontends:

- RESTful APIs with OpenAPI documentation
- WebSocket support for real-time updates
- CORS configuration for cross-origin requests
- JWT token-based authentication

### Third-party Integrations
- **Databases**: Native connectors for major databases
- **Cloud Storage**: AWS S3, Google Cloud Storage, MinIO
- **AI/ML**: OpenAI, Hugging Face, custom models
- **Monitoring**: Prometheus, Grafana, Sentry

## 📞 Support

For technical support and questions:
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- System Info: http://localhost:8000/info

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.