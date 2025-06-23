# 🚀 Debian 12 服务器部署指南

专为您的Debian 12服务器（2GB RAM，纽约节点）定制的完整部署指南。

## 📋 服务器规格确认
- **操作系统**: Debian 12 64位
- **内存**: 2GB RAM（符合最低要求）
- **位置**: 纽约（Server IP: 198.23.164.200）
- **推荐配置**: 适合小到中等负载的生产环境

---

## 🔧 第一步：系统准备

### 1.1 连接服务器并更新系统
```bash
# SSH连接到服务器
ssh root@198.23.164.200

# 更新系统包
apt update && apt upgrade -y

# 安装基础工具
apt install -y curl wget git vim ufw fail2ban
```

### 1.2 创建应用用户（安全最佳实践）
```bash
# 创建专用用户
useradd -m -s /bin/bash flashcard
usermod -aG sudo flashcard

# 为用户设置密码
passwd flashcard

# 切换到新用户
su - flashcard
```

---

## 🐳 第二步：Docker安装

### 2.1 安装Docker Engine
```bash
# 添加Docker官方GPG密钥
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 添加Docker仓库
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 将用户添加到docker组
sudo usermod -aG docker flashcard

# 重新登录以使组权限生效
exit
su - flashcard

# 验证Docker安装
docker --version
docker compose version
```

### 2.2 配置Docker守护进程
```bash
# 创建Docker配置目录
sudo mkdir -p /etc/docker

# 配置Docker守护进程（针对2GB RAM优化）
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-runtime": "runc",
  "storage-driver": "overlay2",
  "default-address-pools": [
    {"base": "172.30.0.0/16", "size": 24}
  ]
}
EOF

# 重启Docker服务
sudo systemctl restart docker
sudo systemctl enable docker
```

---

## 🔥 第三步：防火墙配置

### 3.1 配置UFW防火墙
```bash
# 重置防火墙规则
sudo ufw --force reset

# 设置默认策略
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允许SSH（确保不被锁定）
sudo ufw allow ssh
sudo ufw allow 22/tcp

# 允许HTTP和HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 允许应用端口（可选，用于直接访问）
sudo ufw allow 8000/tcp

# 启用防火墙
sudo ufw enable

# 检查状态
sudo ufw status verbose
```

### 3.2 配置Fail2ban（防暴力破解）
```bash
# 安装Fail2ban
sudo apt install -y fail2ban

# 创建本地配置
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# 启用SSH保护
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 📦 第四步：项目部署

### 4.1 克隆项目代码
```bash
# 创建应用目录
mkdir -p ~/apps
cd ~/apps

# 克隆项目（请替换为您的实际仓库地址）
git clone https://github.com/your-username/flashcard_generator_mvp.git
cd flashcard_generator_mvp

# 检查项目结构
ls -la
```

### 4.2 创建生产环境配置
```bash
# 复制环境配置模板
cp .env.example .env

# 编辑环境配置（重要！）
vim .env
```

**关键配置项（请务必设置）：**
```bash
# === 必需配置 ===
ENVIRONMENT=production
OPENROUTER_API_KEY=your-openrouter-api-key-here

# === 安全配置 ===
SECRET_KEY=your-super-secret-key-here
CORS_ORIGINS=https://yourdomain.com

# === 服务器配置 ===
HOST=0.0.0.0
PORT=8000
WORKERS=2  # 针对2GB RAM优化

# === 日志配置 ===
LOG_LEVEL=info
LOG_FORMAT=json

# === 其他配置 ===
MAX_TEXT_LENGTH=10000
REQUEST_TIMEOUT=60
```

### 4.3 创建必要目录
```bash
# 创建日志目录
mkdir -p logs nginx/ssl

# 设置权限
chmod 755 logs
chmod 700 nginx/ssl
```

---

## 🚀 第五步：应用部署

### 5.1 构建和启动应用
```bash
# 构建Docker镜像
docker compose build

# 启动生产环境
docker compose up -d

# 查看容器状态
docker compose ps

# 查看日志
docker compose logs -f flashcard-app
```

### 5.2 验证部署
```bash
# 等待容器启动（约30秒）
sleep 30

# 测试API端点
curl http://localhost:8000/supported_models

# 测试健康检查
curl http://localhost:8000/health

# 检查前端页面
curl -I http://localhost:8000/
```

---

## 🛡️ 第六步：SSL证书配置（生产环境推荐）

### 6.1 安装Certbot（Let's Encrypt）
```bash
# 安装Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取SSL证书（请替换yourdomain.com）
sudo certbot certonly --standalone -d yourdomain.com

# 复制证书到项目目录
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
sudo chown flashcard:flashcard nginx/ssl/*.pem
```

### 6.2 启用HTTPS（可选）
```bash
# 更新环境变量
echo "SSL_ENABLED=true" >> .env
echo "SSL_CERT_PATH=/app/nginx/ssl/cert.pem" >> .env
echo "SSL_KEY_PATH=/app/nginx/ssl/key.pem" >> .env

# 启动带Nginx的生产环境
docker compose --profile production up -d

# 测试HTTPS
curl -k https://localhost/health
```

---

## 📊 第七步：监控配置

### 7.1 启用基础监控
```bash
# 启动带监控的完整环境
docker compose --profile monitoring up -d

# 检查监控服务
docker compose ps

# 访问监控面板
echo "Prometheus: http://198.23.164.200:9090"
echo "Grafana: http://198.23.164.200:3000 (admin/admin)"
```

### 7.2 设置系统监控
```bash
# 安装htop和iostat
sudo apt install -y htop sysstat

# 创建简单的系统监控脚本
cat > ~/monitor.sh << 'EOF'
#!/bin/bash
echo "=== System Status $(date) ==="
echo "Memory Usage:"
free -h
echo ""
echo "Disk Usage:"
df -h
echo ""
echo "Docker Status:"
docker stats --no-stream
echo ""
EOF

chmod +x ~/monitor.sh
```

---

## 🔄 第八步：备份和维护

### 8.1 设置自动备份
```bash
# 创建备份脚本
cat > ~/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/flashcard/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# 备份配置文件
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
    /home/flashcard/apps/flashcard_generator_mvp/.env \
    /home/flashcard/apps/flashcard_generator_mvp/docker-compose.yml

# 备份日志
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" \
    /home/flashcard/apps/flashcard_generator_mvp/logs/

# 清理旧备份（保留7天）
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x ~/backup.sh

# 设置定时备份（每天凌晨2点）
(crontab -l 2>/dev/null; echo "0 2 * * * /home/flashcard/backup.sh >> /home/flashcard/backup.log 2>&1") | crontab -
```

### 8.2 设置自动重启（可选）
```bash
# 创建应用健康检查脚本
cat > ~/health_check.sh << 'EOF'
#!/bin/bash
cd /home/flashcard/apps/flashcard_generator_mvp

# 检查容器状态
if ! docker compose ps | grep -q "Up"; then
    echo "$(date): Containers down, restarting..." >> ~/health_check.log
    docker compose up -d
fi

# 检查API响应
if ! curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "$(date): API not responding, restarting..." >> ~/health_check.log
    docker compose restart flashcard-app
fi
EOF

chmod +x ~/health_check.sh

# 每5分钟检查一次（可选）
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/flashcard/health_check.sh") | crontab -
```

---

## ✅ 第九步：最终验证

### 9.1 完整功能测试
```bash
cd ~/apps/flashcard_generator_mvp

# 运行配置验证
python3 validate-config.py

# 运行部署检查
python3 deployment-check.py

# 测试所有API端点
echo "Testing API endpoints..."
curl http://localhost:8000/supported_models
curl http://localhost:8000/health
curl -X POST http://localhost:8000/generate_flashcards \
  -H "Content-Type: application/json" \
  -d '{"text": "测试文本", "model": "google/gemini-2.5-flash-preview"}'
```

### 9.2 性能基准测试
```bash
# 创建简单的压力测试脚本
cat > ~/load_test.sh << 'EOF'
#!/bin/bash
echo "Running load test..."
for i in {1..10}; do
  time curl -s http://localhost:8000/supported_models > /dev/null
done
echo "Load test completed"
EOF

chmod +x ~/load_test.sh
./load_test.sh
```

---

## 🎯 部署成功标准

部署被认为成功当：
- [ ] 容器健康状态：`docker compose ps` 显示所有容器为 "Up"
- [ ] API响应正常：`curl http://localhost:8000/supported_models` 返回模型列表
- [ ] 健康检查通过：`curl http://localhost:8000/health` 返回 "OK"
- [ ] 前端可访问：浏览器能打开 `http://198.23.164.200:8000`
- [ ] 资源使用合理：内存使用 < 1.5GB，CPU < 50%
- [ ] 日志正常：`docker compose logs` 无错误信息

---

## 🆘 故障排除

### 常见问题解决方案

**1. 容器启动失败**
```bash
# 查看详细日志
docker compose logs flashcard-app

# 检查环境变量
docker compose exec flashcard-app env | grep OPENROUTER

# 重新构建镜像
docker compose build --no-cache
```

**2. API调用失败**
```bash
# 检查OpenRouter API密钥
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://openrouter.ai/api/v1/models

# 检查网络连接
docker compose exec flashcard-app ping openrouter.ai
```

**3. 内存不足**
```bash
# 查看内存使用
free -h
docker stats

# 减少worker数量
sed -i 's/WORKERS=4/WORKERS=2/' .env
docker compose restart flashcard-app
```

**4. 端口冲突**
```bash
# 检查端口使用
sudo netstat -tlnp | grep :8000

# 更改端口
echo "PORT=8080" >> .env
docker compose up -d
```

---

## 📞 获取支持

如遇到问题，请：
1. 运行诊断：`python3 deployment-check.py`
2. 查看日志：`docker compose logs`
3. 检查系统资源：`~/monitor.sh`
4. 收集错误信息并寻求技术支持

---

## 📋 快速命令参考

```bash
# 查看应用状态
docker compose ps

# 查看实时日志
docker compose logs -f flashcard-app

# 重启应用
docker compose restart flashcard-app

# 更新应用
git pull && docker compose build && docker compose up -d

# 备份数据
~/backup.sh

# 监控系统
~/monitor.sh

# 运行健康检查
~/health_check.sh
```

---

**部署完成！** 🎉

您的AI Flashcard Generator现在应该在 `http://198.23.164.200:8000` 运行。

记住定期更新系统和应用，监控资源使用，并保持备份。