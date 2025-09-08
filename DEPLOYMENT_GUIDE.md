# DataFlow AI Enterprise Platform - Deployment Guide

This guide covers deployment options for the DataFlow AI Enterprise Platform backend, from local development to production environments.

## 🚀 Quick Start (Development)

### Option 1: Docker Compose (Recommended)

1. **Prerequisites**:
   - Docker 20.10+
   - Docker Compose 2.0+
   - 4GB+ available RAM

2. **Setup**:
   ```bash
   # Clone repository
   git clone <repository-url>
   cd dataflow-ai-backend
   
   # Configure environment
   cp .env.example .env
   # Edit .env file as needed
   
   # Start all services
   ./scripts/start.sh docker
   ```

3. **Generate test data**:
   ```bash
   docker-compose exec api python scripts/generate_mock_data.py
   ```

4. **Access services**:
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Task Monitor: http://localhost:5555
   - Grafana: http://localhost:3000 (admin/admin)

### Option 2: Manual Development Setup

1. **Prerequisites**:
   - Python 3.9+
   - PostgreSQL 12+
   - Redis 6+

2. **Setup**:
   ```bash
   # Install dependencies
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Configure environment
   cp .env.example .env
   # Edit .env with your database credentials
   
   # Start services
   ./scripts/start.sh dev
   ```

## 🏢 Production Deployment

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Web Server    │    │   Database      │
│   (nginx/ALB)   │────│   (FastAPI)     │────│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Cache/Queue   │    │   File Storage  │
                       │   (Redis)       │    │   (S3/MinIO)    │
                       └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   Workers       │
                       │   (Celery)      │
                       └─────────────────┘
```

### Production Environment Variables

Create a production `.env` file:

```bash
# Production Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# Security (Generate strong keys!)
SECRET_KEY=your-super-secure-production-secret-key-min-32-chars
ENCRYPTION_KEY=your-32-char-production-encryption-key!

# Database (Use managed service in production)
DATABASE_URL=postgresql://user:password@prod-db:5432/ai_data_platform
REDIS_URL=redis://prod-redis:6379/0

# File Storage (Use S3 in production)
AWS_ACCESS_KEY_ID=your-production-aws-key
AWS_SECRET_ACCESS_KEY=your-production-aws-secret
S3_BUCKET_NAME=prod-ai-data-platform-storage
AWS_REGION=us-east-1

# Monitoring
SENTRY_DSN=your-sentry-dsn-for-error-tracking

# CORS (Restrict to your domain)
ALLOWED_ORIGINS=["https://your-frontend-domain.com"]
```

### Deployment Options

#### Option 1: Docker Swarm

1. **Create production docker-compose**:
   ```yaml
   # docker-compose.prod.yml
   version: '3.8'
   services:
     api:
       image: dataflow-ai:latest
       deploy:
         replicas: 3
         resources:
           limits:
             memory: 2G
           reservations:
             memory: 1G
       environment:
         - DATABASE_URL=${DATABASE_URL}
         - REDIS_URL=${REDIS_URL}
         - SECRET_KEY=${SECRET_KEY}
         - ENCRYPTION_KEY=${ENCRYPTION_KEY}
       ports:
         - "8000:8000"
       depends_on:
         - postgres
         - redis
   
     celery-worker:
       image: dataflow-ai:latest
       command: celery -A app.tasks.data_quality_tasks.celery_app worker --loglevel=warning --concurrency=4
       deploy:
         replicas: 2
       environment:
         - DATABASE_URL=${DATABASE_URL}
         - REDIS_URL=${REDIS_URL}
         - SECRET_KEY=${SECRET_KEY}
         - ENCRYPTION_KEY=${ENCRYPTION_KEY}
   ```

2. **Deploy**:
   ```bash
   docker stack deploy -c docker-compose.prod.yml dataflow-ai
   ```

#### Option 2: Kubernetes

1. **Create Kubernetes manifests**:
   ```yaml
   # k8s/deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: dataflow-ai-api
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: dataflow-ai-api
     template:
       metadata:
         labels:
           app: dataflow-ai-api
       spec:
         containers:
         - name: api
           image: dataflow-ai:latest
           ports:
           - containerPort: 8000
           env:
           - name: DATABASE_URL
             valueFrom:
               secretKeyRef:
                 name: dataflow-secrets
                 key: database-url
           resources:
             limits:
               memory: "2Gi"
               cpu: "1000m"
             requests:
               memory: "1Gi"
               cpu: "500m"
   ```

2. **Deploy**:
   ```bash
   kubectl apply -f k8s/
   ```

#### Option 3: Cloud Platforms

##### AWS ECS/Fargate

1. **Create task definition**:
   ```json
   {
     "family": "dataflow-ai",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "1024",
     "memory": "2048",
     "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
     "containerDefinitions": [
       {
         "name": "api",
         "image": "your-account.dkr.ecr.region.amazonaws.com/dataflow-ai:latest",
         "portMappings": [
           {
             "containerPort": 8000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "DATABASE_URL",
             "value": "postgresql://..."
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/dataflow-ai",
             "awslogs-region": "us-east-1",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

##### Google Cloud Run

1. **Deploy**:
   ```bash
   gcloud run deploy dataflow-ai \
     --image gcr.io/PROJECT-ID/dataflow-ai \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 2Gi \
     --cpu 2 \
     --max-instances 10
   ```

##### Azure Container Instances

1. **Deploy**:
   ```bash
   az container create \
     --resource-group myResourceGroup \
     --name dataflow-ai \
     --image myregistry.azurecr.io/dataflow-ai:latest \
     --cpu 2 \
     --memory 4 \
     --ports 8000 \
     --environment-variables \
       DATABASE_URL="postgresql://..." \
       REDIS_URL="redis://..."
   ```

### Database Setup

#### PostgreSQL (Production)

1. **Managed Services** (Recommended):
   - AWS RDS PostgreSQL
   - Google Cloud SQL
   - Azure Database for PostgreSQL
   - DigitalOcean Managed Databases

2. **Configuration**:
   ```sql
   -- Create database
   CREATE DATABASE ai_data_platform;
   
   -- Create user
   CREATE USER dataflow_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE ai_data_platform TO dataflow_user;
   
   -- Performance tuning
   ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
   ALTER SYSTEM SET max_connections = '200';
   ALTER SYSTEM SET shared_buffers = '256MB';
   ALTER SYSTEM SET effective_cache_size = '1GB';
   ```

#### Redis (Production)

1. **Managed Services** (Recommended):
   - AWS ElastiCache
   - Google Cloud Memorystore
   - Azure Cache for Redis
   - DigitalOcean Managed Databases

2. **Configuration**:
   ```bash
   # Redis configuration for production
   maxmemory 1gb
   maxmemory-policy allkeys-lru
   save 900 1
   save 300 10
   save 60 10000
   ```

### Load Balancer & Reverse Proxy

#### Nginx Configuration

```nginx
# /etc/nginx/sites-available/dataflow-ai
upstream dataflow_api {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name api.dataflow.ai;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.dataflow.ai;
    
    # SSL Configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # File upload size
    client_max_body_size 500M;
    
    # API routes
    location / {
        proxy_pass http://dataflow_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check
    location /health {
        access_log off;
        proxy_pass http://dataflow_api/health;
    }
    
    # Static files (if any)
    location /static/ {
        alias /var/www/dataflow-ai/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Monitoring & Logging

#### Application Monitoring

1. **Sentry** (Error tracking):
   ```python
   # In production settings
   SENTRY_DSN = "https://your-sentry-dsn"
   ```

2. **Prometheus + Grafana**:
   ```yaml
   # docker-compose.monitoring.yml
   version: '3.8'
   services:
     prometheus:
       image: prom/prometheus:latest
       ports:
         - "9090:9090"
       volumes:
         - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
     
     grafana:
       image: grafana/grafana:latest
       ports:
         - "3000:3000"
       environment:
         - GF_SECURITY_ADMIN_PASSWORD=admin
       volumes:
         - grafana_data:/var/lib/grafana
   ```

#### Logging

1. **Centralized Logging**:
   ```yaml
   # ELK Stack
   version: '3.8'
   services:
     elasticsearch:
       image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
     
     logstash:
       image: docker.elastic.co/logstash/logstash:7.17.0
     
     kibana:
       image: docker.elastic.co/kibana/kibana:7.17.0
       ports:
         - "5601:5601"
   ```

2. **Application Logging**:
   ```python
   # Production logging configuration
   LOGGING = {
       'version': 1,
       'disable_existing_loggers': False,
       'formatters': {
           'json': {
               'format': '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
           },
       },
       'handlers': {
           'file': {
               'level': 'INFO',
               'class': 'logging.handlers.RotatingFileHandler',
               'filename': '/var/log/dataflow-ai/app.log',
               'maxBytes': 10485760,  # 10MB
               'backupCount': 5,
               'formatter': 'json',
           },
       },
       'loggers': {
           '': {
               'handlers': ['file'],
               'level': 'INFO',
               'propagate': True,
           },
       },
   }
   ```

### Security Checklist

- [ ] Use strong, unique SECRET_KEY and ENCRYPTION_KEY
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure CORS to restrict origins
- [ ] Use managed database services with encryption
- [ ] Enable database connection encryption (SSL)
- [ ] Set up proper firewall rules
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting
- [ ] Set up monitoring and alerting
- [ ] Regular security updates
- [ ] Backup strategy in place
- [ ] Access logging enabled

### Backup & Recovery

#### Database Backups

```bash
# Automated PostgreSQL backups
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="ai_data_platform"

# Create backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

#### File Storage Backups

```bash
# S3 backup script
#!/bin/bash
aws s3 sync s3://prod-ai-data-platform-storage s3://backup-ai-data-platform-storage --delete
```

### Performance Optimization

#### Application Level

1. **Connection Pooling**:
   ```python
   # Database connection pool
   engine = create_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=30,
       pool_pre_ping=True,
       pool_recycle=3600
   )
   ```

2. **Caching**:
   ```python
   # Redis caching
   @lru_cache(maxsize=1000)
   def get_cached_data(key: str):
       return redis_client.get(key)
   ```

#### Infrastructure Level

1. **Auto Scaling**:
   ```yaml
   # Kubernetes HPA
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: dataflow-ai-hpa
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: dataflow-ai-api
     minReplicas: 2
     maxReplicas: 10
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70
   ```

### Troubleshooting

#### Common Issues

1. **Database Connection Issues**:
   ```bash
   # Test database connection
   psql $DATABASE_URL -c "SELECT 1"
   ```

2. **Redis Connection Issues**:
   ```bash
   # Test Redis connection
   redis-cli -u $REDIS_URL ping
   ```

3. **High Memory Usage**:
   ```bash
   # Monitor memory usage
   docker stats
   
   # Check for memory leaks
   docker exec -it container_name ps aux --sort=-%mem
   ```

4. **Slow API Responses**:
   ```bash
   # Check API logs
   docker-compose logs -f api
   
   # Monitor database queries
   SELECT query, calls, total_time, mean_time 
   FROM pg_stat_statements 
   ORDER BY total_time DESC 
   LIMIT 10;
   ```

### Maintenance

#### Regular Tasks

1. **Database Maintenance**:
   ```sql
   -- Weekly maintenance
   VACUUM ANALYZE;
   REINDEX DATABASE ai_data_platform;
   ```

2. **Log Rotation**:
   ```bash
   # Setup logrotate
   /var/log/dataflow-ai/*.log {
       daily
       missingok
       rotate 30
       compress
       notifempty
       create 644 www-data www-data
   }
   ```

3. **Security Updates**:
   ```bash
   # Update dependencies
   pip install --upgrade -r requirements.txt
   
   # Update base images
   docker pull python:3.11-slim
   docker build -t dataflow-ai:latest .
   ```

This deployment guide provides comprehensive instructions for deploying the DataFlow AI Enterprise Platform in various environments, from development to production-scale deployments.