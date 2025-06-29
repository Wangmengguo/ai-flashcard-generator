# 🚀 部署自动化指南

适配新的HTTPS架构的完整部署自动化方案。

## 📋 概述

针对新的nginx HTTPS + Docker + SSL证书架构，提供三套部署脚本：

- **完整部署** (`deploy.sh`) - 全面的生产部署，包含备份、验证、安全检查
- **快速更新** (`quick-deploy.sh`) - 日常代码更新，不涉及nginx/SSL配置  
- **紧急回滚** (`rollback.sh`) - 故障时快速恢复到上一个工作版本

## 🎯 新架构特点

```
本地开发 → 一键部署 → 云端生产环境
    ↓           ↓            ↓
代码更新    自动化脚本    HTTPS安全服务
```

**架构优势**：
- 🔐 端到端HTTPS加密 (Let's Encrypt)
- 🛡️ 多层安全防护 (Cloudflare + nginx + 防火墙)
- ⚡ 零停机更新部署
- 🔄 自动备份和回滚机制

## 🚀 使用指南

### 1. 完整部署 (首次或重大更新)

```bash
# 使用完整部署脚本
./deploy.sh

# 功能特性：
# ✅ 环境检查和SSH连接验证
# ✅ 自动备份当前配置
# ✅ 部署应用文件和Docker容器
# ✅ 更新前端配置 (API_BASE_URL)
# ✅ nginx配置验证和重载
# ✅ 完整的功能验证测试
# ✅ 部署结果摘要报告
```

**适用场景**：
- 首次部署到新服务器
- 架构性变更 (nginx配置、SSL证书等)
- 重要版本发布
- 生产环境故障恢复

### 2. 快速更新 (日常开发)

```bash
# 快速更新代码
./quick-deploy.sh

# 功能特性：
# ⚡ 仅同步核心应用文件
# ⚡ 重启Docker容器
# ⚡ 基础功能验证
# ⚡ 2-3分钟完成部署
```

**适用场景**：
- 日常代码修改
- Bug修复
- 功能优化
- 前端界面更新

### 3. 紧急回滚 (故障恢复)

```bash
# 交互式回滚菜单
./rollback.sh

# 快速回滚模式
./rollback.sh --quick

# 功能特性：
# 🔄 查看可用备份
# 🔄 快速回滚到上一版本
# 🔄 指定备份回滚
# 🔄 服务状态检查
# 🔄 自动验证恢复结果
```

**适用场景**：
- 新部署出现问题
- 服务异常需要快速恢复
- 配置错误修复
- 紧急故障处理

## 📝 脚本详细功能

### deploy.sh - 完整部署脚本

**执行流程**：
1. **环境检查** - SSH连接、必要文件验证
2. **配置备份** - nginx配置、应用文件、Docker状态
3. **文件部署** - 同步所有应用文件到服务器
4. **前端配置** - 更新API_BASE_URL，设置权限
5. **容器更新** - 重建Docker镜像，重启容器
6. **nginx重载** - 验证配置，重载服务
7. **功能验证** - 本地API、nginx代理、外部访问测试
8. **结果报告** - 显示访问信息和管理命令

**安全特性**：
- 执行前确认提示
- 完整的备份机制
- 逐步验证，失败即停
- 详细的状态检查

### quick-deploy.sh - 快速更新脚本

**执行流程**：
1. **代码同步** - 仅同步核心文件 (main_refactored.py, unified_index.html等)
2. **前端更新** - 复制到nginx目录，修正API配置
3. **容器重启** - 重建镜像，重启容器
4. **快速验证** - 基础API测试

**优化特性**：
- 最小化文件传输
- 静默构建过程
- 快速启动验证
- 适合频繁更新

### rollback.sh - 回滚脚本

**功能模块**：
1. **状态检查** - Docker、nginx、端口、API状态
2. **备份查看** - 列出可用配置备份
3. **快速回滚** - 恢复到上一个工作版本
4. **指定回滚** - 回滚到特定备份时间点

**回滚策略**：
- 优先恢复前端文件备份
- 使用上一个Docker镜像
- 重载nginx配置
- 完整服务验证

## ⚙️ 配置说明

### 服务器配置

脚本中的关键配置变量：

```bash
SERVER_IP="198.23.164.200"      # 服务器IP
SERVER_USER="root"              # 登录用户
PROJECT_NAME="ai-flashcard-generator"
DOMAIN="explain1thing.top"      # 域名
CONTAINER_NAME="flashcard-generator-new"
```

### 目录结构

```
服务器端目录：
├── /root/ai-flashcard-generator/     # 项目源码目录
├── /var/www/ai-flashcard-generator/  # nginx静态文件目录
├── /etc/nginx/sites-enabled/         # nginx配置目录
├── /etc/letsencrypt/live/            # SSL证书目录
└── /root/backup-*/                   # 自动备份目录
```

### SSL证书路径

```bash
# Let's Encrypt证书路径
ssl_certificate /etc/letsencrypt/live/explain1thing.top/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/explain1thing.top/privkey.pem;
```

## 🔍 验证和监控

### 部署后验证清单

```bash
# 1. 服务状态检查
systemctl status nginx
docker ps | grep flashcard-generator-new

# 2. 端口监听验证
ss -tlnp | grep :443    # HTTPS
ss -tlnp | grep :8000   # Docker API

# 3. SSL证书验证
openssl s_client -connect explain1thing.top:443 -servername explain1thing.top

# 4. 功能测试
curl -I https://explain1thing.top/ai-flashcard-generator/
curl https://explain1thing.top/ai-flashcard-generator/api/health

# 5. 安全配置验证
ufw status | grep 8000  # 防火墙规则
docker ps | grep 127.0.0.1:8000  # 端口绑定
```

### 常用管理命令

```bash
# 查看应用日志
ssh root@198.23.164.200 'docker logs flashcard-generator-new'

# 重启应用容器
ssh root@198.23.164.200 'docker restart flashcard-generator-new'

# 重载nginx配置
ssh root@198.23.164.200 'systemctl reload nginx'

# 查看备份目录
ssh root@198.23.164.200 'ls -la /root/backup-*'
```

## 🚨 故障排除

### 常见问题和解决方案

#### 1. 部署失败 - SSH连接问题

```bash
# 检查SSH连接
ssh -v root@198.23.164.200

# 如果需要重新配置SSH密钥
ssh-copy-id root@198.23.164.200
```

#### 2. Docker容器启动失败

```bash
# 查看容器日志
ssh root@198.23.164.200 'docker logs flashcard-generator-new'

# 手动重启容器
ssh root@198.23.164.200 'docker restart flashcard-generator-new'

# 如果需要重建镜像
ssh root@198.23.164.200 'cd /root/ai-flashcard-generator && docker build -t ai-flashcard-generator-flashcard-app .'
```

#### 3. nginx配置错误

```bash
# 测试nginx配置
ssh root@198.23.164.200 'nginx -t'

# 查看nginx错误日志
ssh root@198.23.164.200 'tail -f /var/log/nginx/error.log'

# 恢复备份配置
./rollback.sh
```

#### 4. SSL证书问题

```bash
# 检查证书有效期
ssh root@198.23.164.200 'openssl x509 -in /etc/letsencrypt/live/explain1thing.top/cert.pem -text -noout | grep -A 2 Validity'

# 手动续期证书
ssh root@198.23.164.200 'certbot renew --dry-run'
```

#### 5. API访问异常

```bash
# 测试本地API
ssh root@198.23.164.200 'curl -v http://127.0.0.1:8000/health'

# 测试nginx代理
ssh root@198.23.164.200 'curl -v http://127.0.0.1/ai-flashcard-generator/api/health'

# 检查防火墙规则
ssh root@198.23.164.200 'ufw status numbered'
```

## 📊 性能优化建议

### 部署优化

1. **并行化部署** - 多个文件同时传输
2. **增量更新** - 仅传输变更文件
3. **缓存利用** - Docker镜像层缓存
4. **压缩传输** - 启用scp压缩选项

### 监控集成

```bash
# 集成到现有监控系统
# 添加部署通知到Slack/钉钉
# 设置部署成功/失败的邮件通知
# 集成Prometheus监控指标
```

## 🔄 CI/CD 集成

### GitHub Actions 示例

```yaml
name: Deploy to Production
on:
  push:
    branches: [ main ]
    
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Deploy to server
      run: |
        chmod +x ./quick-deploy.sh
        ./quick-deploy.sh
```

### 部署策略

- **开发环境** → 自动部署 (quick-deploy.sh)
- **预发布环境** → 手动审批 + 完整部署 (deploy.sh)  
- **生产环境** → 手动部署 + 回滚准备 (deploy.sh + rollback.sh)

## 📈 未来优化方向

1. **蓝绿部署** - 零停机更新策略
2. **健康检查** - 更完善的服务监控
3. **自动扩缩容** - 基于负载的容器管理
4. **多环境支持** - 开发/测试/生产环境隔离
5. **配置管理** - 环境变量和密钥管理

---

## 🎯 快速参考

```bash
# 日常更新 (最常用)
./quick-deploy.sh

# 重要发布
./deploy.sh

# 紧急回滚
./rollback.sh --quick

# 检查服务状态
./rollback.sh  # 选择选项1
```

**记住**：新的HTTPS架构需要特别注意SSL证书和nginx配置的一致性！