# AI Flashcard Generator - 部署指南

## 概述

本指南详细说明了AI Flashcard Generator项目的容器化部署流程，包括本地开发、测试环境和生产环境的完整部署方案。

## 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [环境配置](#环境配置)
- [容器化部署](#容器化部署)
- [CI/CD流程](#cicd流程)
- [安全配置](#安全配置)
- [监控和日志](#监控和日志)
- [故障排除](#故障排除)
- [性能优化](#性能优化)

## 系统要求

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

## 快速开始

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
python validate-config.py

# 检查应用健康状态
make health
```

## 环境配置

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

## 容器化部署

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

### 服务配置

#### 主应用服务
- **端口**: 8000
- **健康检查**: `/supported_models`
- **日志**: `/app/logs/`
- **重启策略**: unless-stopped

#### 反向代理 (Nginx)
- **HTTP端口**: 80
- **HTTPS端口**: 443
- **配置**: `nginx/nginx.conf`
- **SSL证书**: `nginx/ssl/`

#### 监控服务
- **Prometheus**: 端口9090
- **Grafana**: 端口3000
- **数据持久化**: Docker volumes

## CI/CD流程

### GitHub Actions工作流

CI/CD流程包含以下阶段：

1. **安全扫描** - Trivy漏洞扫描
2. **代码质量** - Black、Flake8、Bandit检查
3. **单元测试** - pytest测试套件
4. **镜像构建** - 多平台Docker镜像
5. **部署** - 自动部署到staging/production

### 触发条件
- **Push到main分支** → 部署到生产环境
- **Push到develop分支** → 部署到测试环境
- **Pull Request** → 运行测试和检查
- **Release发布** → 创建版本化镜像

### 环境变量设置

在GitHub仓库设置中配置以下密钥：

```bash
# 容器仓库
GITHUB_TOKEN  # 自动提供

# 部署密钥（如果使用SSH部署）
DEPLOY_SSH_KEY
STAGING_HOST
PRODUCTION_HOST

# 通知设置
SLACK_WEBHOOK_URL
```

### 部署脚本示例

```bash
#!/bin/bash
# deploy.sh

set -e

echo "开始部署到生产环境..."

# 拉取最新镜像
docker-compose pull

# 优雅重启服务
docker-compose up -d --no-deps --force-recreate flashcard-app

# 等待健康检查
echo "等待应用启动..."
sleep 30

# 验证部署
if curl -f http://localhost:8000/supported_models; then
    echo "部署成功！"
else
    echo "部署失败，回滚..."
    docker-compose rollback
    exit 1
fi
```

## 安全配置

### 容器安全

1. **非root用户运行**
   ```dockerfile
   RUN groupadd -r appuser && useradd -r -g appuser appuser
   USER appuser
   ```

2. **最小化镜像**
   - 使用slim基础镜像
   - 多阶段构建
   - 删除不必要的包

3. **安全扫描**
   - Trivy漏洞扫描
   - 定期更新基础镜像

### 网络安全

1. **HTTPS配置**
   ```bash
   # 生成自签名证书（仅用于测试）
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout nginx/ssl/key.pem \
     -out nginx/ssl/cert.pem
   ```

2. **防火墙设置**
   ```bash
   # UFW配置示例
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 80/tcp   # HTTP
   sudo ufw allow 443/tcp  # HTTPS
   sudo ufw enable
   ```

### API安全

1. **输入验证**
   - 文本长度限制
   - 字符过滤
   - API密钥验证

2. **速率限制**
   ```bash
   RATE_LIMIT_REQUESTS=100
   RATE_LIMIT_WINDOW=60
   ```

3. **CORS策略**
   ```bash
   # 生产环境严格设置
   CORS_ORIGINS=https://yourdomain.com
   ```

## 监控和日志

### 健康检查

应用提供多个健康检查端点：

- `/health` - 基础健康状态
- `/ready` - 就绪状态检查
- `/metrics` - Prometheus指标

### 日志配置

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

### 日志轮换

```yaml
# docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 故障排除

### 常见问题

#### 1. 容器启动失败
```bash
# 查看详细日志
docker-compose logs flashcard-app

# 检查配置
docker-compose config

# 验证环境变量
docker-compose exec flashcard-app env
```

#### 2. API调用失败
```bash
# 检查OpenRouter连接
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://openrouter.ai/api/v1/models

# 测试本地API
curl http://localhost:8000/supported_models
```

#### 3. 内存不足
```bash
# 查看资源使用
docker stats

# 调整内存限制
docker-compose up -d --scale flashcard-app=1 --memory="2g"
```

#### 4. SSL证书问题
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

## 性能优化

### 容器优化

1. **镜像大小优化**
   - 使用Alpine Linux基础镜像
   - 清理pip缓存
   - 删除构建依赖

2. **运行时优化**
   ```bash
   # Gunicorn工作进程数
   WORKERS=4

   # 工作进程类型
   WORKER_CLASS=uvicorn.workers.UvicornWorker

   # 连接保持
   KEEPALIVE=2
   ```

### 缓存策略

1. **静态文件缓存**
   ```nginx
   location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
       expires 1y;
       add_header Cache-Control "public, immutable";
   }
   ```

2. **API响应缓存**
   - Redis缓存实现
   - 模型响应缓存
   - 频率限制缓存

### 数据库优化（未来扩展）

```bash
# PostgreSQL配置
DATABASE_URL=postgresql://user:pass@db:5432/flashcard
POSTGRES_MAX_CONNECTIONS=100
POSTGRES_SHARED_BUFFERS=256MB
```

## 扩展部署

### 水平扩展

```yaml
# docker-compose.yml
services:
  flashcard-app:
    deploy:
      replicas: 3
    scale: 3
```

### 负载均衡

```nginx
upstream flashcard_backend {
    server flashcard-app-1:8000;
    server flashcard-app-2:8000;
    server flashcard-app-3:8000;
}
```

### 数据持久化

```yaml
volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
```

## 备份和恢复

### 数据备份

```bash
# 备份脚本
#!/bin/bash
docker-compose exec postgres pg_dump -U user flashcard > backup_$(date +%Y%m%d).sql

# 日志备份
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

### 灾难恢复

```bash
# 恢复数据库
docker-compose exec postgres psql -U user flashcard < backup_20241201.sql

# 恢复配置
cp backup/config/* config/
```

## 新增部署工具 (2025年更新)

### 1. 配置验证工具
```bash
# 运行全面配置检查
python validate-config.py

# 检查特定配置文件
python validate-config.py /path/to/project
```

### 2. Makefile快捷命令
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

# 测试和质量保证
make test         # 运行测试
make lint         # 代码检查
make security     # 安全扫描

# 维护工具
make health       # 健康检查
make backup       # 创建备份
make clean        # 清理容器
```

### 3. 自动化部署脚本
```bash
# 快速开发环境搭建
make quick-dev

# 快速生产环境搭建
make quick-prod

# 远程部署
make deploy SERVER=your-server.com
```

## 升级说明

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
python validate-config.py

# 4. 重新构建镜像
make build

# 5. 重启服务
make prod

# 6. 验证升级
make health
```

## 联系和支持

如果在部署过程中遇到问题，请：

1. 运行配置验证: `python validate-config.py`
2. 查看[故障排除](#故障排除)部分
3. 查看[部署检查清单](DEPLOYMENT_CHECKLIST.md)
4. 查看[生产最佳实践](PRODUCTION_BEST_PRACTICES.md)
5. 检查GitHub Issues
6. 提交新的Issue并包含：
   - 配置验证结果
   - 错误信息和日志
   - 系统信息
   - 复现步骤

---

**注意**: 在生产环境部署前，请确保：
- 运行 `python validate-config.py` 验证配置
- 设置强密码和密钥
- 配置正确的CORS域名
- 启用HTTPS
- 设置适当的防火墙规则
- 定期备份重要数据
- 查看[部署检查清单](DEPLOYMENT_CHECKLIST.md)