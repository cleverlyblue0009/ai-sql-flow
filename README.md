# AI-Powered Data Cleaning and SQL Migration Platform - Backend API

A comprehensive, enterprise-grade backend API for AI-powered data quality analysis, cleaning, and SQL migration.

## 🚀 Features

### 🔐 Authentication & Authorization
- JWT token-based authentication with refresh tokens
- Role-based access control (Admin, Engineer, Analyst)
- OAuth2 integration (Google, GitHub)
- Comprehensive audit logging
- Session management and security

### 📊 Data Quality Analysis
- **AI-Powered Analysis**: Duplicate detection using ML clustering, outlier detection with isolation forests
- **Missing Value Analysis**: Neural network-based imputation suggestions
- **Pattern Recognition**: NLP-based data type inference and validation
- **Quality Metrics**: Completeness, accuracy, consistency, validity, uniqueness scores
- **Real-time Reporting**: Interactive dashboards and comprehensive reports

### 🧹 Data Cleaning
- **Automated Cleaning**: AI-suggested cleaning operations
- **Custom Operations**: Remove duplicates, fill missing values, remove outliers
- **Format Standardization**: Consistent data formatting and type correction
- **Preview Mode**: Test cleaning operations before applying
- **Batch Processing**: Handle large datasets efficiently

### 🔄 SQL Migration (Coming Soon)
- **Neural Translation**: SQL dialect conversion using transformer models
- **Semantic Validation**: BERT-based similarity checking
- **Performance Optimization**: Query optimization using reinforcement learning
- **Schema Mapping**: Intelligent schema mapping and conversion

### 🗄️ Database Management
- **Multi-Database Support**: PostgreSQL, MySQL, Oracle, SQL Server
- **Secure Connections**: Encrypted credential storage
- **Health Monitoring**: Connection status and performance tracking
- **Connection Pooling**: Efficient resource management

### ⚡ Background Processing
- **Distributed Tasks**: Celery-based background job processing
- **Real-time Progress**: WebSocket updates for long-running operations
- **Resource Management**: CPU and memory usage tracking
- **Error Handling**: Comprehensive error recovery and retry logic

## 🏗️ Technology Stack

- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with Redis caching
- **AI/ML**: TensorFlow, PyTorch, scikit-learn, Transformers
- **Queue System**: Celery with Redis broker
- **Storage**: AWS S3 / MinIO support
- **Monitoring**: Prometheus metrics, structured logging
- **Security**: JWT tokens, OAuth2, encryption, rate limiting

## 📋 Requirements

- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (recommended)

## 🚀 Quick Start

### Using Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-data-platform-backend
   ```

2. **Start the services**
   ```bash
   docker-compose up -d
   ```

3. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Celery Flower: http://localhost:5555
   - MinIO Console: http://localhost:9001
   - Grafana: http://localhost:3000 (admin/admin)

### Manual Installation

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start PostgreSQL and Redis**
   ```bash
   # Using Docker
   docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15
   docker run -d --name redis -p 6379:6379 redis:7-alpine
   ```

4. **Start the application**
   ```bash
   python -m app.main
   ```

5. **Start Celery worker** (in another terminal)
   ```bash
   celery -A app.tasks.data_quality_tasks.celery_app worker --loglevel=info
   ```

## 📁 Project Structure

```
app/
├── main.py                 # FastAPI application entry point
├── auth/                   # Authentication module
│   ├── routes.py          # Auth endpoints
│   ├── security.py        # JWT and encryption utilities
│   ├── dependencies.py    # Auth dependencies
│   └── schemas.py         # Auth Pydantic models
├── data_quality/          # Data quality module
│   ├── routes.py          # Data quality endpoints
│   ├── analyzer.py        # AI-powered data analysis
│   ├── cleaner.py         # Data cleaning operations
│   └── schemas.py         # Data quality Pydantic models
├── database/              # Database configuration
│   ├── config.py          # Database setup and settings
│   ├── models.py          # SQLAlchemy models
│   └── __init__.py
├── tasks/                 # Background tasks
│   ├── data_quality_tasks.py  # Celery tasks
│   └── __init__.py
├── utils/                 # Utility modules
│   ├── email.py           # Email utilities
│   ├── audit.py           # Audit logging
│   ├── file_storage.py    # File storage manager
│   └── logging_config.py  # Logging configuration
└── tests/                 # Test suites
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/ai_data_platform
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Storage
S3_BUCKET_NAME=ai-data-platform-storage
MINIO_ENDPOINT=localhost:9000

# AI Models
HUGGINGFACE_API_KEY=your-huggingface-key

# Application
DEBUG=True
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=100
```

## 📊 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user info
- `POST /auth/logout` - User logout

### Data Quality
- `POST /data-quality/upload` - Upload data file
- `POST /data-quality/analyze` - Start data analysis
- `GET /data-quality/report/{job_id}` - Get analysis report
- `POST /data-quality/clean` - Start data cleaning
- `GET /data-quality/status/{job_id}` - Get job status
- `GET /data-quality/download/{job_id}` - Download cleaned data

### System
- `GET /health` - Health check
- `GET /info` - System information
- `GET /metrics` - Prometheus metrics

## 🔍 AI Models

### Data Quality Models

1. **Duplicate Detection Model**: Siamese network for similarity matching
2. **Outlier Detection**: Ensemble of isolation forest and autoencoders
3. **Data Type Classifier**: BERT-based model for semantic type detection
4. **Quality Scorer**: Multi-output regression model for quality metrics

### SQL Translation Models (Coming Soon)

1. **Dialect Translator**: Transformer model trained on SQL corpus
2. **Semantic Validator**: BERT for semantic similarity checking
3. **Performance Predictor**: Tree-based model for query performance

## 🧪 Testing

Run tests with pytest:

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

## 📈 Performance Specifications

- **Response Time**: <200ms for simple queries, <2s for complex operations
- **Throughput**: Handle 1000+ concurrent users
- **File Processing**: Support files up to 10GB, process 1M+ records
- **Reliability**: 99.9% uptime with comprehensive error recovery

## 🔒 Security Features

- **Input Validation**: Pydantic models for all API inputs
- **SQL Injection Prevention**: Parameterized queries only
- **Rate Limiting**: API throttling by user and endpoint
- **Encryption**: AES-256 for sensitive data at rest
- **Audit Logging**: Comprehensive activity tracking
- **CORS Configuration**: Proper cross-origin handling

## 🐳 Deployment

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# Scale workers
docker-compose up -d --scale celery-worker=3

# View logs
docker-compose logs -f api
```

### Production Deployment

1. **Configure environment variables** for production
2. **Set up SSL/TLS** certificates
3. **Configure load balancer** (nginx, HAProxy)
4. **Set up monitoring** (Prometheus + Grafana)
5. **Configure backup** for PostgreSQL
6. **Set up log aggregation** (ELK stack)

## 🔧 Development

### Setting up Development Environment

1. **Install development dependencies**
   ```bash
   pip install -r requirements.txt
   pip install black isort flake8 mypy
   ```

2. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

3. **Run code formatting**
   ```bash
   black app/
   isort app/
   ```

4. **Run linting**
   ```bash
   flake8 app/
   mypy app/
   ```

## 📊 Monitoring

### Metrics

The application exposes metrics for monitoring:

- HTTP request metrics
- Database connection pool metrics
- Celery task metrics
- Custom business metrics

### Logging

Structured logging with JSON format:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "logger": "app.auth.routes",
  "message": "User login successful",
  "user_id": 123,
  "ip_address": "192.168.1.1"
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run linting and tests
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

- Create an issue on GitHub
- Email: support@aidataplatform.com
- Documentation: [API Docs](http://localhost:8000/docs)

## 🗺️ Roadmap

- [ ] SQL Migration module implementation
- [ ] Advanced AI model fine-tuning
- [ ] Real-time data streaming support
- [ ] Multi-tenant architecture
- [ ] Advanced visualization dashboards
- [ ] Mobile API support
- [ ] Integration with popular BI tools

---

**Built with ❤️ for enterprise data teams**
