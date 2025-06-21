# AI Flashcard Generator - 生产部署最佳实践

## 概述

本文档提供AI Flashcard Generator在生产环境中部署和运维的最佳实践指南，确保应用的安全性、性能和可靠性。

## 安全最佳实践

### 1. 容器安全

#### 非root用户运行
```dockerfile
# 确保应用以非root用户运行
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
```

#### 最小化镜像
- 使用官方slim基础镜像
- 删除不必要的包和文件
- 使用多阶段构建减少攻击面

#### 安全扫描
```bash
# 使用Trivy扫描镜像漏洞
trivy image flashcard-generator:latest

# 集成到CI/CD流程
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  -v $PWD:/tmp/.cache/ aquasec/trivy:latest image flashcard-generator:latest
```

### 2. 网络安全

#### HTTPS强制启用
```nginx
# nginx配置示例
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    
    # 现代SSL配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # 安全头
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
```

#### 防火墙配置
```bash
# UFW配置示例
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 仅允许特定IP访问管理端口
sudo ufw allow from 192.168.1.0/24 to any port 9090  # Prometheus
sudo ufw allow from 192.168.1.0/24 to any port 3000  # Grafana
```

### 3. API安全

#### 速率限制
```python
# 在应用中实现速率限制
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/generate")
@limiter.limit("10/minute")
async def generate_flashcards(request: Request, ...):
    pass
```

#### 输入验证和净化
```python
# 严格的输入验证
from pydantic import BaseModel, Field, validator

class TextInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    
    @validator('text')
    def sanitize_text(cls, v):
        # 移除潜在危险字符
        import re
        return re.sub(r'[<>"\']', '', v)
```

## 性能优化最佳实践

### 1. 容器配置优化

#### 资源限制
```yaml
# docker-compose.yml
services:
  flashcard-app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

#### 工作进程优化
```bash
# 计算最佳工作进程数
# CPU密集型: 进程数 = CPU核心数
# I/O密集型: 进程数 = CPU核心数 * 2

# 对于AI推理应用 (I/O密集型)
WORKERS = $(nproc) * 2
```

### 2. 应用性能优化

#### 异步处理
```python
# 使用异步HTTP客户端
import httpx

async def call_openrouter_api(prompt: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(...)
        return response.json()
```

#### 缓存策略
```python
# Redis缓存示例
import redis
import json
from functools import wraps

redis_client = redis.Redis(host='redis', port=6379, db=0)

def cache_result(expiration=3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # 尝试从缓存获取
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            redis_client.setex(
                cache_key, 
                expiration, 
                json.dumps(result, ensure_ascii=False)
            )
            return result
        return wrapper
    return decorator
```

### 3. 数据库优化 (未来扩展)

#### 连接池配置
```python
# PostgreSQL连接池配置
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,
    poolclass=NullPool if testing else None
)
```

## 监控和日志最佳实践

### 1. 结构化日志

#### 日志配置
```python
# 使用structlog进行结构化日志
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

#### 关键指标记录
```python
import time
from prometheus_client import Counter, Histogram, Gauge

# 定义指标
REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active connections')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    REQUEST_COUNT.labels(
        method=request.method, 
        endpoint=request.url.path
    ).inc()
    
    REQUEST_DURATION.observe(time.time() - start_time)
    
    return response
```

### 2. 健康检查

#### 深度健康检查
```python
@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # 检查OpenRouter API连接
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                timeout=5.0
            )
            health_status["checks"]["openrouter"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception as e:
        health_status["checks"]["openrouter"] = f"unhealthy: {str(e)}"
    
    # 检查磁盘空间
    import shutil
    disk_usage = shutil.disk_usage("/app/logs")
    free_space_gb = disk_usage.free / (1024**3)
    health_status["checks"]["disk_space"] = "healthy" if free_space_gb > 1 else "unhealthy"
    
    # 检查内存使用
    import psutil
    memory_percent = psutil.virtual_memory().percent
    health_status["checks"]["memory"] = "healthy" if memory_percent < 90 else "unhealthy"
    
    # 整体状态
    unhealthy_checks = [k for k, v in health_status["checks"].items() if "unhealthy" in v]
    if unhealthy_checks:
        health_status["status"] = "unhealthy"
    
    return health_status
```

### 3. 告警配置

#### Prometheus告警规则
```yaml
# prometheus-alerts.yml
groups:
- name: flashcard-generator
  rules:
  - alert: HighErrorRate
    expr: rate(requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      
  - alert: HighMemoryUsage
    expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage detected"
      
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(request_duration_seconds_bucket[5m])) > 5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response time detected"
```

## 备份和灾难恢复

### 1. 数据备份策略

#### 自动备份脚本
```bash
#!/bin/bash
# backup.sh

set -e

BACKUP_DIR="/backup/flashcard-generator"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# 备份配置文件
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
    .env* \
    docker-compose.yml \
    nginx/ \
    monitoring/

# 备份日志文件
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" logs/

# 备份数据库 (如果有)
# docker-compose exec postgres pg_dump -U user flashcard > "$BACKUP_DIR/db_$DATE.sql"

# 清理旧备份 (保留30天)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.sql" -mtime +30 -delete

echo "Backup completed: $DATE"
```

#### 定时备份
```bash
# 添加到crontab
0 2 * * * /opt/flashcard-generator/backup.sh >> /var/log/backup.log 2>&1
```

### 2. 灾难恢复计划

#### 恢复步骤
```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1
RESTORE_DATE=$(date +%Y%m%d_%H%M%S)

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "Starting disaster recovery: $RESTORE_DATE"

# 停止服务
docker-compose down

# 备份当前状态
mv .env .env.backup_$RESTORE_DATE
mv docker-compose.yml docker-compose.yml.backup_$RESTORE_DATE

# 恢复配置
tar -xzf "$BACKUP_FILE" -C .

# 重启服务
docker-compose up -d

# 验证恢复
sleep 30
curl -f http://localhost:8000/health || {
    echo "Recovery failed, rolling back..."
    docker-compose down
    mv .env.backup_$RESTORE_DATE .env
    mv docker-compose.yml.backup_$RESTORE_DATE docker-compose.yml
    docker-compose up -d
    exit 1
}

echo "Disaster recovery completed successfully"
```

## 扩展和高可用部署

### 1. 水平扩展

#### 负载均衡配置
```nginx
# nginx负载均衡
upstream flashcard_backend {
    least_conn;
    server flashcard-app-1:8000 max_fails=3 fail_timeout=30s;
    server flashcard-app-2:8000 max_fails=3 fail_timeout=30s;
    server flashcard-app-3:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://flashcard_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 健康检查
        proxy_next_upstream error timeout http_500 http_502 http_503 http_504;
    }
}
```

#### Docker Swarm部署
```yaml
# docker-compose.swarm.yml
version: '3.8'

services:
  flashcard-app:
    image: flashcard-generator:latest
    deploy:
      mode: replicated
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      placement:
        constraints:
          - node.role == worker
    networks:
      - flashcard-network

networks:
  flashcard-network:
    driver: overlay
    attachable: true
```

### 2. 跨区域部署

#### 多区域容器编排
```bash
# 区域A部署
docker-compose -f docker-compose.yml -f docker-compose.region-a.yml up -d

# 区域B部署  
docker-compose -f docker-compose.yml -f docker-compose.region-b.yml up -d
```

## 安全审计和合规

### 1. 定期安全检查

#### 自动化安全扫描
```bash
#!/bin/bash
# security-audit.sh

echo "Starting security audit..."

# 镜像漏洞扫描
trivy image flashcard-generator:latest --format json > security-report.json

# 代码安全扫描
bandit -r . -f json -o bandit-report.json

# 依赖安全检查
safety check --json > safety-report.json

# 生成汇总报告
python generate-security-report.py

echo "Security audit completed"
```

### 2. 合规性检查

#### GDPR合规
- 确保用户数据不被持久化存储
- 实现数据处理透明度
- 提供数据删除机制

#### SOC2合规
- 实现访问控制和审计日志
- 确保数据传输加密
- 建立事件响应流程

## 性能基准和优化

### 1. 性能基准测试

#### 负载测试脚本
```python
# load_test.py
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor

async def test_endpoint(session, url, data):
    async with session.post(url, json=data) as response:
        return await response.json()

async def run_load_test():
    concurrent_users = 50
    test_duration = 60  # seconds
    
    connector = aiohttp.TCPConnector(limit=100)
    async with aiohttp.ClientSession(connector=connector) as session:
        start_time = time.time()
        tasks = []
        
        while time.time() - start_time < test_duration:
            for _ in range(concurrent_users):
                task = test_endpoint(
                    session, 
                    "http://localhost:8000/generate",
                    {"text": "测试文本内容"}
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            tasks.clear()
            
            # 统计结果
            successful = sum(1 for r in results if not isinstance(r, Exception))
            print(f"Successful requests: {successful}/{len(results)}")

if __name__ == "__main__":
    asyncio.run(run_load_test())
```

### 2. 性能优化指标

#### 目标性能指标
- 响应时间: P95 < 3秒, P99 < 5秒
- 吞吐量: > 100 requests/second
- 错误率: < 0.1%
- 可用性: > 99.9%

## 总结

遵循这些最佳实践将确保AI Flashcard Generator在生产环境中的:

1. **安全性**: 通过多层安全措施保护应用和数据
2. **性能**: 通过优化配置和监控确保最佳性能
3. **可靠性**: 通过健康检查和故障恢复机制确保高可用
4. **可维护性**: 通过结构化日志和监控简化运维工作
5. **可扩展性**: 通过水平扩展支持增长需求

定期审查和更新这些实践，确保它们与最新的安全和性能标准保持一致。