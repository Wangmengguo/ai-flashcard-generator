# AI Flashcard Generator - 部署检查清单

## 部署前检查清单 (Pre-Deployment Checklist)

### 环境准备 (Environment Setup)
- [ ] Docker Engine 20.10+ 已安装
- [ ] Docker Compose 2.0+ 已安装  
- [ ] 系统满足最低要求 (2GB RAM, 1 CPU核心, 10GB 磁盘空间)
- [ ] 网络端口 80, 443, 8000 可用
- [ ] Git 仓库已克隆到目标服务器

### 环境变量配置 (Environment Configuration)
- [ ] `.env` 文件已创建并配置
- [ ] **OPENROUTER_API_KEY** 已设置 (CRITICAL - 必须设置)
- [ ] **CORS_ORIGINS** 已配置为实际域名 (生产环境)
- [ ] **SECRET_KEY** 已设置为强密码 (生产环境)
- [ ] SSL证书路径已配置 (如启用HTTPS)
- [ ] 日志目录权限已设置

### 安全配置 (Security Configuration)
- [ ] 防火墙规则已配置
- [ ] SSL/TLS证书已安装 (生产环境)
- [ ] 非root用户运行权限已设置
- [ ] API密钥已安全存储
- [ ] CORS策略已严格配置 (生产环境)

### 网络配置 (Network Configuration)
- [ ] 域名DNS记录已配置
- [ ] 反向代理配置已验证 (如使用)
- [ ] 端口映射已正确设置
- [ ] 健康检查端点可访问

## 快速部署命令 (Quick Deployment Commands)

### 开发环境部署
```bash
# 1. 环境准备
cp .env.example .env
# 编辑 .env 文件，设置 OPENROUTER_API_KEY

# 2. 启动开发环境
docker-compose --profile dev up -d

# 3. 验证部署
curl http://localhost:8001/supported_models
```

### 生产环境部署
```bash
# 1. 环境准备
cp .env.production .env
# 编辑 .env 文件，设置所有必需变量

# 2. 构建和启动
docker-compose up -d

# 3. 验证部署
curl http://localhost:8000/supported_models
```

### 完整生产环境 (含监控)
```bash
# 启动完整生产环境
docker-compose --profile production --profile monitoring up -d

# 访问服务
# 应用: http://localhost:8000
# Prometheus: http://localhost:9090  
# Grafana: http://localhost:3000 (admin/admin)
```

## 部署后验证 (Post-Deployment Verification)

### 基础功能验证
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

### 功能测试
- [ ] 文本输入和卡片生成功能正常
- [ ] 不同AI模型切换正常
- [ ] 导出功能 (Anki, CSV, JSON) 正常
- [ ] 错误处理和用户反馈正常

### 性能验证
- [ ] 响应时间在可接受范围内 (<5秒)
- [ ] 内存使用正常 (<2GB for 4 workers)
- [ ] CPU使用率正常 (<80% under load)
- [ ] 日志文件正常写入

### 安全验证
- [ ] HTTPS正常工作 (生产环境)
- [ ] API密钥不在日志中泄露
- [ ] CORS策略生效
- [ ] 防火墙规则正确应用

## 故障排除快速指南 (Quick Troubleshooting)

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
```

#### 3. 前端无法访问后端
```bash
# 检查CORS设置
docker-compose exec flashcard-app env | grep CORS

# 检查端口映射
docker-compose ps
```

#### 4. 性能问题
```bash
# 查看资源使用
docker stats flashcard-app

# 检查慢查询日志
tail -f logs/app.log | grep "slow"
```

## 监控和维护 (Monitoring and Maintenance)

### 日常监控指标
- [ ] 应用可用性 (通过健康检查)
- [ ] 响应时间和错误率
- [ ] 资源使用情况 (CPU, 内存, 磁盘)
- [ ] 日志文件大小和轮换

### 定期维护任务
- [ ] 每周检查安全更新
- [ ] 每月备份配置和日志
- [ ] 每季度更新依赖包版本
- [ ] 每半年审查安全配置

### 紧急响应步骤
1. **服务不可用**
   ```bash
   # 快速重启
   docker-compose restart flashcard-app
   
   # 如果问题持续，回滚到上一个版本
   docker-compose down
   docker pull flashcard-generator:previous-version
   docker-compose up -d
   ```

2. **高负载**
   ```bash
   # 临时扩容
   docker-compose up -d --scale flashcard-app=6
   ```

3. **数据损坏** (未来如有数据库)
   ```bash
   # 从备份恢复
   docker-compose exec postgres psql -U user -d flashcard < backup.sql
   ```

## 成功部署标准 (Success Criteria)

部署被认为成功当:
- [ ] 所有健康检查通过
- [ ] API响应时间 < 3秒 (正常负载)
- [ ] 错误率 < 1% (24小时内)
- [ ] 内存使用稳定 (无内存泄漏)
- [ ] 日志记录正常 (无错误堆栈)
- [ ] 监控指标正常显示

## 支持联系信息

如果遇到部署问题:
1. 查看本检查清单和故障排除指南
2. 检查项目文档 (README.md, DEPLOYMENT_GUIDE.md)
3. 查看GitHub Issues
4. 提交新Issue时包含:
   - 部署环境信息
   - 错误日志完整内容
   - 已尝试的解决步骤
   - 环境变量配置 (隐藏敏感信息)

---

**注意**: 确保在生产环境部署前完成所有检查项，特别是安全相关配置项。