# 🚀 AI Flashcard Generator - 完整部署指南

本指南提供 AI Flashcard Generator 项目的完整部署解决方案，包括本地开发、测试环境和生产环境的部署流程，以及最佳实践和运维指南。

---

## 📋 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [环境配置](#环境配置)
- [容器化部署](#容器化部署)
- [部署检查清单](#部署检查清单)
- [生产最佳实践](#生产最佳实践)
- [监控和日志](#监控和日志)
- [故障排除](#故障排除)
- [扩展部署](#扩展部署)

---

## 🖥️ 系统要求

### 最低要求
- Docker Engine 20.10+
- Docker Compose 2.0+
- 2GB RAM
- 1 CPU核心
- 10GB 磁盘空间

### 推荐配置
- Docker Engine 24.0+
- Docker Compose 2.20+
- 4GB RAM
- 2 CPU核心
- 20GB SSD磁盘空间

### 2025年更新优化
- 使用最新FastAPI 0.115.13+
- 使用Uvicorn 0.34.3+内置多进程支持（推荐替代Gunicorn）
- 支持HTTP/2和现代异步架构
- 优化的容器镜像和多阶段构建

### 支持的操作系统
- Linux (Ubuntu 20.04+, CentOS 8+, RHEL 8+)
- macOS 12+
- Windows 10/11 (WSL2)

---

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd flashcard_generator_mvp
```

### 2. 环境配置
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量（必须设置OPENROUTER_API_KEY）
vim .env
```

### 3. 启动开发环境
```bash
# 使用Makefile快速启动（推荐）
make dev

# 或手动启动开发环境（带热重载）
docker-compose --profile dev up -d

# 查看日志
make dev-logs
# 或
docker-compose logs -f flashcard-dev

# 应用将在 http://localhost:8001 运行
```

### 4. 启动生产环境
```bash
# 使用Makefile快速启动（推荐）
make prod

# 或启动完整生产环境（含监控）
make prod-full

# 或手动构建并启动生产环境
docker-compose up -d

# 应用将在 http://localhost:8000 运行
```

### 5. 配置验证
```bash
# 验证部署配置
make validate
# 或
python validate-config.py

# 检查应用健康状态
make health
```

---

## ⚙️ 环境配置

### 环境变量文件

项目提供了三个环境配置文件：

1. **`.env.example`** - 模板文件，包含所有可配置选项
2. **`.env.development`** - 开发环境配置
3. **`.env.production`** - 生产环境配置

### 关键配置项

#### 必需配置
```bash
# OpenRouter API密钥（必需）
OPENROUTER_API_KEY=your-openrouter-api-key

# 应用环境
ENVIRONMENT=production
```

#### CORS配置
```bash
# 开发环境
CORS_ORIGINS=*

# 生产环境（必须指定具体域名）
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

#### 安全配置
```bash
# 生产环境必须设置
SECRET_KEY=your-super-secret-key-here
SSL_ENABLED=true
SSL_CERT_PATH=/etc/ssl/certs/cert.pem
SSL_KEY_PATH=/etc/ssl/private/key.pem
```

#### 性能配置
```bash
# 工作进程配置
WORKERS=4
MAX_TEXT_LENGTH=10000
REQUEST_TIMEOUT=60

# 日志配置
LOG_LEVEL=info
LOG_FORMAT=json  # 生产环境
ACCESS_LOG=/app/logs/access.log
ERROR_LOG=/app/logs/error.log
```

#### 完整环境变量配置 (69个配置选项)
```bash
# === 核心应用配置 ===
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secret-key-here
HOST=0.0.0.0
PORT=8000

# === API配置 ===
OPENROUTER_API_KEY=your-openrouter-api-key
API_BASE_URL=https://openrouter.ai/api/v1
DEFAULT_MODEL=google/gemini-2.5-flash-preview
MAX_TEXT_LENGTH=10000
REQUEST_TIMEOUT=60

# === 安全配置 ===
CORS_ORIGINS=https://yourdomain.com
CORS_CREDENTIALS=true
CORS_METHODS=GET,POST,OPTIONS
CORS_HEADERS=*
SSL_ENABLED=true
SSL_CERT_PATH=/etc/ssl/certs/cert.pem
SSL_KEY_PATH=/etc/ssl/private/key.pem

# === 性能配置 ===
WORKERS=4
WORKER_CLASS=uvicorn.workers.UvicornWorker
KEEPALIVE=2
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=100
TIMEOUT=30
GRACEFUL_TIMEOUT=30

# === 日志配置 ===
LOG_LEVEL=info
LOG_FORMAT=json
LOG_FILE=/app/logs/app.log
ACCESS_LOG=/app/logs/access.log
ERROR_LOG=/app/logs/error.log
LOG_ROTATION=daily
LOG_RETENTION=30

# === 监控配置 ===
METRICS_ENABLED=true
HEALTH_CHECK_PATH=/health
METRICS_PATH=/metrics
PROMETHEUS_ENABLED=true

# === 缓存配置 ===
REDIS_URL=redis://redis:6379
CACHE_TTL=3600
CACHE_ENABLED=true

# === 数据库配置 (未来扩展) ===
DATABASE_URL=postgresql://user:pass@db:5432/flashcard
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# === 文件存储配置 ===
UPLOAD_MAX_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=txt,md
STORAGE_PATH=/app/storage

# === 速率限制配置 ===
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
RATE_LIMIT_STORAGE=redis

# === 邮件配置 (通知) ===
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TLS=true

# === 外部服务配置 ===
SENTRY_DSN=https://your-sentry-dsn
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url

# === Docker配置 ===
COMPOSE_PROJECT_NAME=flashcard-generator
DOCKER_REGISTRY=ghcr.io/your-username
IMAGE_TAG=latest

# === Nginx配置 ===
NGINX_CLIENT_MAX_BODY_SIZE=10m
NGINX_PROXY_TIMEOUT=60s
NGINX_PROXY_CONNECT_TIMEOUT=60s
NGINX_PROXY_SEND_TIMEOUT=60s

# === 监控服务配置 ===
PROMETHEUS_RETENTION=15d
GRAFANA_ADMIN_PASSWORD=admin
GRAFANA_SECRET_KEY=your-grafana-secret

# === 备份配置 ===
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION=30
BACKUP_S3_BUCKET=your-backup-bucket

# === 开发配置 ===
HOT_RELOAD=true
AUTO_RELOAD=true
RELOAD_DIRS=/app
RELOAD_INCLUDES=*.py

# === 安全扫描配置 ===
SECURITY_SCAN_ENABLED=true
TRIVY_ENABLED=true
BANDIT_ENABLED=true
```

---

## 🐳 容器化部署

### 2025年优化特性

本项目已升级至2025年最新标准：

1. **Uvicorn多进程支持**: 使用Uvicorn 0.34.3+的内置多进程管理，替代Gunicorn
2. **现代FastAPI**: 升级至FastAPI 0.115.13+，支持最新特性
3. **优化的容器构建**: 多阶段构建，最小化镜像大小
4. **结构化日志**: JSON格式日志，便于监控和分析

### Docker镜像构建

```bash
# 使用Makefile构建（推荐）
make build

# 或手动构建生产镜像
docker build -t flashcard-generator:latest .

# 构建并标记版本
docker build -t flashcard-generator:v1.0.0 .

# 多平台构建
docker buildx build --platform linux/amd64,linux/arm64 -t flashcard-generator:latest .
```

### Docker Compose配置

项目支持多种部署配置：

#### 1. 基础部署
```bash
# 启动应用
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 2. 开发环境
```bash
# 启动开发环境（带热重载）
docker-compose --profile dev up -d
```

#### 3. 生产环境（带反向代理）
```bash
# 启动完整生产环境
docker-compose --profile production up -d
```

#### 4. 监控环境
```bash
# 启动带监控的环境
docker-compose --profile monitoring up -d

# 访问监控面板
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

### 自动化工具完善 (Makefile)

```bash
# 查看所有可用命令
make help

# 开发环境管理
make dev          # 启动开发环境
make dev-logs     # 查看开发日志
make dev-stop     # 停止开发环境

# 生产环境管理
make prod         # 启动生产环境
make prod-full    # 启动完整生产环境（含监控）
make prod-logs    # 查看生产日志

# 构建和部署
make build        # 构建Docker镜像
make push         # 推送镜像到仓库
make deploy       # 部署到远程服务器

# 测试和质量保证
make test         # 运行测试
make lint         # 代码检查
make security     # 安全扫描

# 维护工具
make health       # 健康检查
make verify       # 综合部署验证
make validate     # 配置验证
make backup       # 创建备份
make clean        # 清理容器

# 快速部署
make quick-dev    # 快速开发环境搭建
make quick-prod   # 快速生产环境搭建

# 监控
make monitor      # 打开监控面板
```

---

## ✅ 部署检查清单

### 部署前检查 (Pre-Deployment)

#### 环境准备
- [ ] Docker Engine 20.10+ 已安装
- [ ] Docker Compose 2.0+ 已安装  
- [ ] 系统满足最低要求 (2GB RAM, 1 CPU核心, 10GB 磁盘空间)
- [ ] 网络端口 80, 443, 8000 可用
- [ ] Git 仓库已克隆到目标服务器

#### 环境变量配置
- [ ] `.env` 文件已创建并配置
- [ ] **OPENROUTER_API_KEY** 已设置 (CRITICAL - 必须设置)
- [ ] **CORS_ORIGINS** 已配置为实际域名 (生产环境)
- [ ] **SECRET_KEY** 已设置为强密码 (生产环境)
- [ ] SSL证书路径已配置 (如启用HTTPS)
- [ ] 日志目录权限已设置

#### 安全配置
- [ ] 防火墙规则已配置
- [ ] SSL/TLS证书已安装 (生产环境)
- [ ] 非root用户运行权限已设置
- [ ] API密钥已安全存储
- [ ] CORS策略已严格配置 (生产环境)

#### 网络配置
- [ ] 域名DNS记录已配置
- [ ] 反向代理配置已验证 (如使用)
- [ ] 端口映射已正确设置
- [ ] 健康检查端点可访问

### 快速部署命令

#### 开发环境部署
```bash
# 1. 环境准备
cp .env.example .env
# 编辑 .env 文件，设置 OPENROUTER_API_KEY

# 2. 启动开发环境
make dev

# 3. 验证部署
curl http://localhost:8001/supported_models
```

#### 生产环境部署
```bash
# 1. 环境准备
cp .env.production .env
# 编辑 .env 文件，设置所有必需变量

# 2. 构建和启动
make build
make prod

# 3. 验证部署
make verify
```

#### 完整生产环境 (含监控)
```bash
# 启动完整生产环境
make prod-full

# 访问服务
# 应用: http://localhost:8000
# Prometheus: http://localhost:9090  
# Grafana: http://localhost:3000 (admin/admin)
```

### 部署后验证 (Post-Deployment)

#### 基础功能验证
- [ ] API端点响应正常
  ```bash
  curl http://localhost:8000/supported_models
  ```
- [ ] 健康检查通过
  ```bash
  curl http://localhost:8000/health
  ```
- [ ] 前端页面可访问
  ```bash
  curl http://localhost:8000/
  ```

#### 功能测试
- [ ] 文本输入和卡片生成功能正常
- [ ] 不同AI模型切换正常
- [ ] 导出功能 (Anki, CSV, JSON) 正常
- [ ] 错误处理和用户反馈正常

#### 性能验证
- [ ] 响应时间在可接受范围内 (<5秒)
- [ ] 内存使用正常 (<2GB for 4 workers)
- [ ] CPU使用率正常 (<80% under load)
- [ ] 日志文件正常写入

#### 安全验证
- [ ] HTTPS正常工作 (生产环境)
- [ ] API密钥不在日志中泄露
- [ ] CORS策略生效
- [ ] 防火墙规则正确应用

### 成功部署标准

部署被认为成功当:
- [ ] 所有健康检查通过
- [ ] API响应时间 < 3秒 (正常负载)
- [ ] 错误率 < 1% (24小时内)
- [ ] 内存使用稳定 (无内存泄漏)
- [ ] 日志记录正常 (无错误堆栈)
- [ ] 监控指标正常显示

---

## 🛡️ 生产最佳实践

### 安全最佳实践

#### 1. 系统级安全加固

**用户权限管理**
```bash
# 创建专用应用用户
sudo useradd -m -s /bin/bash flashcard
sudo usermod -aG sudo flashcard

# 禁用root SSH登录（可选）
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# 设置强密码策略
sudo apt install -y libpam-pwquality
sudo sed -i 's/# minlen = 8/minlen = 12/' /etc/security/pwquality.conf
```

**SSH安全加固**
```bash
# 更改SSH默认端口（可选）
sudo sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config

# 禁用密码认证，仅使用密钥认证（推荐）
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# 限制SSH访问尝试
echo "MaxAuthTries 3" | sudo tee -a /etc/ssh/sshd_config
echo "MaxSessions 2" | sudo tee -a /etc/ssh/sshd_config

# 重启SSH服务
sudo systemctl restart ssh
```

**Fail2ban配置增强**
```bash
# 创建自定义jail配置
sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[DEFAULT]
# 禁止时间（秒）
bantime = 3600
# 查找时间窗口（秒）
findtime = 600
# 最大尝试次数
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
EOF

# 重启Fail2ban
sudo systemctl restart fail2ban
sudo systemctl enable fail2ban
```

#### 2. 容器安全

**非root用户运行**
```dockerfile
# 确保应用以非root用户运行
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
```

**增强Docker配置**
```bash
# 创建增强的Docker配置
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-runtime": "runc",
  "storage-driver": "overlay2",
  "live-restore": true,
  "userland-proxy": false,
  "no-new-privileges": true,
  "seccomp-profile": "/etc/docker/seccomp.json",
  "default-address-pools": [
    {"base": "172.30.0.0/16", "size": 24}
  ]
}
EOF

# 重启Docker
sudo systemctl restart docker
```

**最小化镜像**
- 使用官方slim基础镜像
- 删除不必要的包和文件
- 使用多阶段构建减少攻击面

**安全扫描**
```bash
# 使用Trivy扫描镜像漏洞
trivy image flashcard-generator:latest

# 集成到CI/CD流程
make security
```

#### 2. 网络安全

**HTTPS强制启用**
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

**防火墙配置**
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

#### 3. API安全

**速率限制**
```bash
# 环境变量配置
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

**输入验证和净化**
- 严格的文本长度限制 (最大10000字符)
- 字符过滤和净化
- API密钥格式验证

**CORS策略**
```bash
# 生产环境严格设置
CORS_ORIGINS=https://yourdomain.com
```

#### 4. 安全监控和事件响应

**安全监控脚本**
```bash
# 创建安全监控脚本
cat > ~/security-monitor.sh << 'EOF'
#!/bin/bash

LOG_FILE="$HOME/security-monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] Security Monitor Report" >> $LOG_FILE

# 检查失败的SSH登录
echo "Recent failed SSH attempts:" >> $LOG_FILE
sudo grep "Failed password" /var/log/auth.log | tail -10 >> $LOG_FILE

# 检查Fail2ban状态
echo "Fail2ban status:" >> $LOG_FILE
sudo fail2ban-client status >> $LOG_FILE

# 检查端口监听
echo "Listening ports:" >> $LOG_FILE
sudo netstat -tlnp >> $LOG_FILE

# 检查异常进程
echo "High CPU processes:" >> $LOG_FILE
ps aux --sort=-%cpu | head -10 >> $LOG_FILE

# 检查Docker容器状态
echo "Docker containers:" >> $LOG_FILE
docker ps >> $LOG_FILE

echo "----------------------------------------" >> $LOG_FILE
EOF

chmod +x ~/security-monitor.sh

# 设置定期安全检查
(crontab -l 2>/dev/null; echo "0 */6 * * * $HOME/security-monitor.sh") | crontab -
```

**自动威胁检测**
```bash
# 创建自动威胁检测脚本
cat > ~/threat-detection.sh << 'EOF'
#!/bin/bash

# 检查异常连接
CONNECTIONS=$(netstat -an | grep :8000 | wc -l)
if [ $CONNECTIONS -gt 100 ]; then
    echo "$(date): High connection count detected: $CONNECTIONS" >> ~/security-events.log
    # 自动限制连接
    sudo iptables -A INPUT -p tcp --dport 8000 -m connlimit --connlimit-above 20 -j DROP
fi

# 检查CPU使用率
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
if (( $(echo "$CPU_USAGE > 90" | bc -l) )); then
    echo "$(date): High CPU usage detected: $CPU_USAGE%" >> ~/security-events.log
fi

# 检查内存使用
MEM_USAGE=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100)}')
if (( $(echo "$MEM_USAGE > 90" | bc -l) )); then
    echo "$(date): High memory usage detected: $MEM_USAGE%" >> ~/security-events.log
fi

# 检查异常日志
if grep -q "error\|failed\|denied" ~/apps/flashcard_generator_mvp/logs/app.log; then
    echo "$(date): Error patterns detected in application logs" >> ~/security-events.log
fi
EOF

chmod +x ~/threat-detection.sh

# 每分钟运行威胁检测
(crontab -l 2>/dev/null; echo "* * * * * $HOME/threat-detection.sh") | crontab -
```

**紧急安全响应**
```bash
# 创建紧急安全响应脚本
cat > ~/emergency-response.sh << 'EOF'
#!/bin/bash

# 紧急安全响应脚本
# 用法: ./emergency-response.sh [lockdown|isolate|restore]

case "$1" in
    "lockdown")
        echo "Initiating security lockdown..."
        
        # 停止所有Web服务
        docker compose stop
        
        # 阻止所有入站连接
        sudo ufw deny in
        
        # 记录事件
        echo "$(date): Emergency lockdown initiated" >> ~/security-events.log
        
        echo "Lockdown complete. Only SSH access allowed."
        ;;
        
    "isolate")
        echo "Isolating compromised services..."
        
        # 停止主应用
        docker compose stop flashcard-app
        
        # 保持监控运行
        echo "$(date): Services isolated" >> ~/security-events.log
        ;;
        
    "restore")
        echo "Restoring normal operations..."
        
        # 恢复防火墙规则
        sudo ufw --force reset
        sudo ufw default deny incoming
        sudo ufw default allow outgoing
        sudo ufw allow ssh
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        sudo ufw allow 8000/tcp
        sudo ufw enable
        
        # 重启服务
        docker compose up -d
        
        echo "$(date): Normal operations restored" >> ~/security-events.log
        ;;
        
    *)
        echo "Usage: $0 [lockdown|isolate|restore]"
        exit 1
        ;;
esac
EOF

chmod +x ~/emergency-response.sh
```

### 性能优化最佳实践

#### 1. 容器配置优化

**资源限制**
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

**工作进程优化**
```bash
# 2025年推荐配置
# 使用Uvicorn内置多进程支持
WORKERS=4  # CPU核心数
WORKER_CLASS=uvicorn.workers.UvicornWorker
KEEPALIVE=2
```

#### 2. 缓存策略

**静态文件缓存**
```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

**API响应缓存**
- Redis缓存实现
- 模型响应缓存
- 频率限制缓存

#### 3. 性能目标指标
- 响应时间: P95 < 3秒, P99 < 5秒
- 吞吐量: > 100 requests/second
- 错误率: < 0.1%
- 可用性: > 99.9%
- 内存使用: < 2GB (4 workers)

---

## 📊 监控和日志

### 健康检查

应用提供多个健康检查端点：

- `/health` - 基础健康状态
- `/ready` - 就绪状态检查
- `/metrics` - Prometheus指标

### 实时监控仪表板

```bash
# 创建综合监控脚本
cat > ~/dashboard.sh << 'EOF'
#!/bin/bash

# 清屏并显示标题
clear
echo "=== AI Flashcard Generator - 实时监控仪表板 ==="
echo "服务器：Debian 12 | RAM：2GB | 时间：$(date)"
echo "==============================================="

# 系统负载
echo "📊 系统负载："
uptime

# 内存使用
echo "💾 内存使用："
free -h | awk 'NR==2{printf "内存使用: %s/%s (%.2f%%)\n", $3,$2,$3*100/$2}'

# Docker容器状态
echo "🐳 Docker容器状态："
if command -v docker &> /dev/null; then
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo "Docker未安装或未运行"
fi

# 应用健康检查
echo "🏥 应用健康状态："
if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ 应用健康状态：正常"
else
    echo "❌ 应用健康状态：异常"
fi

if curl -sf http://localhost:8000/supported_models >/dev/null 2>&1; then
    echo "✅ API端点：可访问"
else
    echo "❌ API端点：无法访问"
fi

echo ""
echo "==============================================="
echo "刷新：watch -n 30 ~/dashboard.sh"
echo "退出：Ctrl+C"
EOF

chmod +x ~/dashboard.sh
```

### 性能监控和告警

```bash
# 创建性能监控脚本
cat > ~/performance-monitor.sh << 'EOF'
#!/bin/bash

LOG_FILE="$HOME/performance-monitor.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 获取系统指标
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
MEM_USAGE=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100)}')
DISK_USAGE=$(df / | awk 'NR==2{print $5}' | cut -d'%' -f1)
LOAD_AVG=$(uptime | awk '{print $10 $11 $12}')

# 获取Docker指标
if command -v docker &> /dev/null; then
    CONTAINER_COUNT=$(docker ps -q | wc -l)
    CONTAINER_MEM=$(docker stats --no-stream --format "{{.MemUsage}}" | head -1)
else
    CONTAINER_COUNT=0
    CONTAINER_MEM="N/A"
fi

# 获取网络指标
CONNECTIONS=$(ss -tu | wc -l)
API_RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8000/health || echo "N/A")

# 记录到日志文件
echo "$TIMESTAMP,CPU:$CPU_USAGE%,MEM:$MEM_USAGE%,DISK:$DISK_USAGE%,LOAD:$LOAD_AVG,CONTAINERS:$CONTAINER_COUNT,CONNECTIONS:$CONNECTIONS,API_TIME:${API_RESPONSE_TIME}s" >> $LOG_FILE

# 性能警告检查
if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    echo "$TIMESTAMP: HIGH CPU USAGE: $CPU_USAGE%" >> $HOME/alerts.log
fi

if (( $(echo "$MEM_USAGE > 85" | bc -l) )); then
    echo "$TIMESTAMP: HIGH MEMORY USAGE: $MEM_USAGE%" >> $HOME/alerts.log
fi

if [ "$DISK_USAGE" -gt 85 ]; then
    echo "$TIMESTAMP: HIGH DISK USAGE: $DISK_USAGE%" >> $HOME/alerts.log
fi

# 保留最近30天的数据
find $HOME -name "performance-monitor.log" -mtime +30 -delete
EOF

chmod +x ~/performance-monitor.sh

# 设置每5分钟收集一次性能数据
(crontab -l 2>/dev/null; echo "*/5 * * * * $HOME/performance-monitor.sh") | crontab -
```

### 应用监控和自动恢复

```bash
# 创建应用专用监控脚本
cat > ~/app-monitor.sh << 'EOF'
#!/bin/bash

APP_LOG="$HOME/app-monitor.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
APP_DIR="$HOME/apps/flashcard_generator_mvp"

cd $APP_DIR

# 检查Docker容器状态
CONTAINER_STATUS=$(docker compose ps --services --filter "status=running" | wc -l)
TOTAL_CONTAINERS=$(docker compose ps --services | wc -l)

# API健康检查
API_HEALTH="FAILED"
API_RESPONSE_CODE=$(curl -o /dev/null -s -w "%{http_code}" http://localhost:8000/health)
if [ "$API_RESPONSE_CODE" = "200" ]; then
    API_HEALTH="OK"
fi

# 检查支持的模型端点
MODELS_HEALTH="FAILED"
MODELS_RESPONSE=$(curl -s http://localhost:8000/supported_models | wc -l)
if [ "$MODELS_RESPONSE" -gt 0 ]; then
    MODELS_HEALTH="OK"
fi

# 记录监控数据
echo "$TIMESTAMP,CONTAINERS:$CONTAINER_STATUS/$TOTAL_CONTAINERS,API:$API_HEALTH,MODELS:$MODELS_HEALTH" >> $APP_LOG

# 自动恢复逻辑
if [ "$API_HEALTH" = "FAILED" ] && [ "$CONTAINER_STATUS" -gt 0 ]; then
    echo "$TIMESTAMP: API健康检查失败，重启应用容器" >> $HOME/auto-recovery.log
    docker compose restart flashcard-app
    sleep 10
    
    # 再次检查
    API_RESPONSE_CODE=$(curl -o /dev/null -s -w "%{http_code}" http://localhost:8000/health)
    if [ "$API_RESPONSE_CODE" = "200" ]; then
        echo "$TIMESTAMP: 应用重启成功" >> $HOME/auto-recovery.log
    else
        echo "$TIMESTAMP: 应用重启失败，需要人工介入" >> $HOME/alerts.log
    fi
fi

if [ "$CONTAINER_STATUS" -eq 0 ]; then
    echo "$TIMESTAMP: 容器全部停止，尝试重启" >> $HOME/auto-recovery.log
    docker compose up -d
    echo "$TIMESTAMP: 容器重启命令已执行" >> $HOME/auto-recovery.log
fi
EOF

chmod +x ~/app-monitor.sh

# 设置每2分钟检查一次应用状态
(crontab -l 2>/dev/null; echo "*/2 * * * * $HOME/app-monitor.sh") | crontab -
```

### 结构化日志配置

```bash
# 日志级别
LOG_LEVEL=info

# 日志格式
LOG_FORMAT=json  # 生产环境
LOG_FORMAT=pretty  # 开发环境

# 日志文件
LOG_FILE=/app/logs/app.log
ACCESS_LOG=/app/logs/access.log
ERROR_LOG=/app/logs/error.log
```

### Prometheus指标

监控以下关键指标：

- 请求总数和成功率
- 响应时间分布
- 生成的卡片数量
- API错误统计
- 模型使用情况
- 系统资源使用 (CPU, 内存, 磁盘)

### 日志轮换

```yaml
# docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 告警配置

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

---

## 🔧 故障排除

### 常见问题及解决方案

#### 1. 容器启动失败
```bash
# 查看详细日志
docker-compose logs flashcard-app

# 检查配置语法
docker-compose config

# 验证环境变量
docker-compose exec flashcard-app env | grep OPENROUTER
```

#### 2. API调用失败 (OpenRouter)
```bash
# 测试API密钥
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://openrouter.ai/api/v1/models

# 检查网络连接
docker-compose exec flashcard-app ping openrouter.ai

# 测试本地API
curl http://localhost:8000/supported_models
```

#### 3. 前端无法访问后端
```bash
# 检查CORS设置
docker-compose exec flashcard-app env | grep CORS

# 检查端口映射
docker-compose ps
```

#### 4. 内存不足
```bash
# 查看资源使用
docker stats

# 调整内存限制
docker-compose up -d --scale flashcard-app=1 --memory="2g"
```

#### 5. SSL证书问题
```bash
# 验证证书
openssl x509 -in nginx/ssl/cert.pem -text -noout

# 检查Nginx配置
docker-compose exec nginx nginx -t
```

### 调试模式

```bash
# 启用调试模式
export DEBUG=true
export LOG_LEVEL=debug

# 重启服务
docker-compose restart flashcard-app
```

### 性能分析

```bash
# 查看容器资源使用
docker stats flashcard-app

# 分析慢查询
grep "slow" /path/to/logs/app.log

# 内存分析
docker exec flashcard-app python -m memory_profiler main.py
```

### 自动化诊断工具

```bash
# 运行综合验证
make verify

# 运行健康检查
make health

# 查看系统状态
make status

# 生成诊断报告
python deployment-check.py
```

---

## 📈 扩展部署

### 水平扩展

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

### 数据持久化

```yaml
volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local
```

### 跨区域部署

```bash
# 区域A部署
docker-compose -f docker-compose.yml -f docker-compose.region-a.yml up -d

# 区域B部署  
docker-compose -f docker-compose.yml -f docker-compose.region-b.yml up -d
```

---

## 💾 备份和恢复

### 数据备份策略

#### 自动备份脚本
```bash
#!/bin/bash
# backup.sh - 由 make backup 调用

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

### 灾难恢复计划

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

---

## 🔒 安全审计和合规

### 定期安全检查

#### 自动化安全扫描
```bash
#!/bin/bash
# security-audit.sh - 由 make security 调用

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

### 合规性检查

#### GDPR合规
- 确保用户数据不被持久化存储
- 实现数据处理透明度
- 提供数据删除机制

#### SOC2合规
- 实现访问控制和审计日志
- 确保数据传输加密
- 建立事件响应流程

---

## 🔄 升级和维护

### 从旧版本升级

如果从旧版本升级，请注意以下变更：

1. **Uvicorn替代Gunicorn**: 新版本使用Uvicorn内置多进程支持
2. **依赖包更新**: 所有核心依赖已升级至最新版本
3. **日志格式**: 新增JSON格式结构化日志
4. **环境变量**: 新增了一些可选的环境变量配置

### 升级步骤
```bash
# 1. 备份当前配置
make backup

# 2. 拉取最新代码
git pull origin main

# 3. 验证新配置
make validate

# 4. 重新构建镜像
make build

# 5. 重启服务
make prod

# 6. 验证升级
make verify
```

### 定期维护任务

- [ ] 每周检查安全更新
- [ ] 每月备份配置和日志
- [ ] 每季度更新依赖包版本
- [ ] 每半年审查安全配置

---

## 📞 联系和支持

如果在部署过程中遇到问题，请：

1. 运行配置验证: `make validate`
2. 查看[故障排除](#故障排除)部分
3. 检查GitHub Issues
4. 提交新的Issue并包含：
   - 配置验证结果
   - 错误信息和日志
   - 系统信息
   - 复现步骤

### 支持资源

- **配置验证工具**: `make validate` 或 `python validate-config.py`
- **健康检查**: `make health`
- **综合验证**: `make verify`
- **诊断报告**: `python deployment-check.py`

---

## 📝 总结

遵循这个完整部署指南将确保AI Flashcard Generator在生产环境中的:

1. **安全性**: 通过多层安全措施保护应用和数据
2. **性能**: 通过优化配置和监控确保最佳性能
3. **可靠性**: 通过健康检查和故障恢复机制确保高可用
4. **可维护性**: 通过结构化日志和监控简化运维工作
5. **可扩展性**: 通过水平扩展支持增长需求

**注意**: 在生产环境部署前，请确保：
- 运行 `make validate` 验证配置
- 设置强密码和密钥
- 配置正确的CORS域名
- 启用HTTPS
- 设置适当的防火墙规则
- 定期备份重要数据

定期审查和更新这些实践，确保它们与最新的安全和性能标准保持一致。

---

**文档维护者**: AI Flashcard Generator 部署团队  
**最后更新**: 2025-06-21  
**文档版本**: 2.0 (整合版)  
**涵盖内容**: 完整部署流程 + 检查清单 + 最佳实践