# 🛡️ 服务器安全配置指南

针对您的Debian 12服务器的全面安全配置指南，确保AI Flashcard Generator的安全运行。

---

## 🔐 第一层：系统级安全

### 1.1 用户权限管理

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

### 1.2 SSH安全加固

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

### 1.3 防火墙配置详解

```bash
# 高级UFW配置
sudo ufw --force reset

# 默认策略
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH (如果更改了端口，请相应调整)
sudo ufw allow 22/tcp
# sudo ufw allow 2222/tcp  # 如果更改了SSH端口

# Web服务
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 应用端口
sudo ufw allow 8000/tcp

# 限制连接频率（防暴力破解）
sudo ufw limit ssh

# 启用防火墙
sudo ufw --force enable

# 检查状态
sudo ufw status verbose
```

### 1.4 Fail2ban配置增强

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

[nginx-noproxy]
enabled = true
port = http,https
filter = nginx-noproxy
logpath = /var/log/nginx/access.log
maxretry = 2

[nginx-badbots]
enabled = true
port = http,https
filter = nginx-badbots
logpath = /var/log/nginx/access.log
maxretry = 2
EOF

# 重启Fail2ban
sudo systemctl restart fail2ban
sudo systemctl enable fail2ban

# 检查状态
sudo fail2ban-client status
```

---

## 🔒 第二层：应用级安全

### 2.1 环境变量安全

```bash
# 设置环境文件权限
chmod 600 .env*
chown flashcard:flashcard .env*

# 生成强随机密钥
SECRET_KEY=$(openssl rand -hex 32)
echo "SECRET_KEY=$SECRET_KEY" >> .env

# 确保敏感信息不在git中
echo ".env*" >> .gitignore
echo "*.log" >> .gitignore
echo "secrets/" >> .gitignore
```

### 2.2 Docker容器安全

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

### 2.3 网络安全配置

```bash
# 创建专用Docker网络
docker network create \
  --driver bridge \
  --subnet=172.30.0.0/24 \
  --gateway=172.30.0.1 \
  --opt com.docker.network.bridge.name=flashcard-br \
  flashcard-secure-network

# 限制容器间通信
docker network create \
  --driver bridge \
  --internal \
  flashcard-internal
```

---

## 🌐 第三层：Web服务安全

### 3.1 Nginx安全配置

```bash
# 创建安全的Nginx配置
mkdir -p nginx
cat > nginx/nginx.conf << 'EOF'
user www-data;
worker_processes auto;
pid /run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    # 隐藏Nginx版本
    server_tokens off;
    
    # 安全头设置
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';" always;
    
    # 限制请求大小
    client_max_body_size 10m;
    client_body_buffer_size 16k;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 8k;
    
    # 超时设置
    client_body_timeout 12;
    client_header_timeout 12;
    keepalive_timeout 15;
    send_timeout 10;
    
    # 日志格式
    log_format security '$remote_addr - $remote_user [$time_local] '
                        '"$request" $status $bytes_sent '
                        '"$http_referer" "$http_user_agent" '
                        '"$http_x_forwarded_for" $request_time';
    
    # 速率限制
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
    
    server {
        listen 80;
        server_name _;
        
        # 重定向到HTTPS
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name yourdomain.com;
        
        # SSL配置
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        
        # 现代SSL配置
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;
        
        # HSTS
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
        
        # 日志
        access_log /var/log/nginx/access.log security;
        error_log /var/log/nginx/error.log warn;
        
        # 限制请求方法
        if ($request_method !~ ^(GET|POST|HEAD|OPTIONS)$) {
            return 405;
        }
        
        # 阻止敏感文件访问
        location ~ /\\.(?!well-known) {
            deny all;
        }
        
        # API限制
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://flashcard-app:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # 主应用
        location / {
            proxy_pass http://flashcard-app:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # 超时设置
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
    }
}
EOF
```

### 3.2 SSL/TLS证书配置

```bash
# 安装Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取免费SSL证书
sudo certbot certonly --standalone -d yourdomain.com

# 创建证书更新脚本
cat > ~/renew-ssl.sh << 'EOF'
#!/bin/bash
sudo certbot renew --quiet
if [ $? -eq 0 ]; then
    sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ~/apps/flashcard_generator_mvp/nginx/ssl/cert.pem
    sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ~/apps/flashcard_generator_mvp/nginx/ssl/key.pem
    sudo chown flashcard:flashcard ~/apps/flashcard_generator_mvp/nginx/ssl/*.pem
    docker compose restart nginx
fi
EOF

chmod +x ~/renew-ssl.sh

# 设置自动更新证书
(crontab -l 2>/dev/null; echo "0 3 * * 0 $HOME/renew-ssl.sh") | crontab -
```

---

## 🔍 第四层：监控和审计

### 4.1 安全监控脚本

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

# 检查磁盘使用
echo "Disk usage:" >> $LOG_FILE
df -h >> $LOG_FILE

# 检查内存使用
echo "Memory usage:" >> $LOG_FILE
free -h >> $LOG_FILE

# 检查Docker容器状态
echo "Docker containers:" >> $LOG_FILE
docker ps >> $LOG_FILE

echo "----------------------------------------" >> $LOG_FILE
EOF

chmod +x ~/security-monitor.sh

# 设置定期安全检查
(crontab -l 2>/dev/null; echo "0 */6 * * * $HOME/security-monitor.sh") | crontab -
```

### 4.2 入侵检测

```bash
# 安装AIDE (高级入侵检测环境)
sudo apt install -y aide

# 初始化AIDE数据库
sudo aideinit

# 创建检查脚本
cat > ~/aide-check.sh << 'EOF'
#!/bin/bash
sudo aide --check
if [ $? -ne 0 ]; then
    echo "AIDE detected file system changes!" | mail -s "Security Alert" admin@yourdomain.com
fi
EOF

chmod +x ~/aide-check.sh

# 设置每日检查
(crontab -l 2>/dev/null; echo "0 4 * * * $HOME/aide-check.sh") | crontab -
```

---

## 🚨 第五层：应急响应

### 5.1 安全事件响应脚本

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

### 5.2 自动威胁响应

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

---

## 📋 安全检查清单

### 每日检查
- [ ] 查看fail2ban日志：`sudo fail2ban-client status sshd`
- [ ] 检查系统更新：`sudo apt list --upgradable`
- [ ] 查看应用日志：`docker compose logs --tail=100`
- [ ] 监控资源使用：`~/monitor.sh`

### 每周检查
- [ ] 更新系统包：`sudo apt update && sudo apt upgrade`
- [ ] 检查SSL证书状态：`sudo certbot certificates`
- [ ] 审查安全日志：`cat ~/security-monitor.log`
- [ ] 验证备份完整性：`ls -la ~/backups/`

### 每月检查
- [ ] 更新Docker镜像：`docker compose pull && docker compose up -d`
- [ ] 审查防火墙规则：`sudo ufw status numbered`
- [ ] 检查用户账户：`sudo cat /etc/passwd`
- [ ] 更新安全配置

---

## 🔧 安全加固命令

```bash
# 一键安全加固脚本
cat > ~/security-hardening.sh << 'EOF'
#!/bin/bash

echo "Starting security hardening..."

# 内核参数优化
sudo tee -a /etc/sysctl.conf > /dev/null <<EOL
# IP Spoofing protection
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Ignore ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0

# Ignore send redirects
net.ipv4.conf.all.send_redirects = 0

# Disable source packet routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0

# Log Martians
net.ipv4.conf.all.log_martians = 1

# Ignore ping requests
net.ipv4.icmp_echo_ignore_all = 0

# TCP SYN flood protection
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 5
EOL

# 应用内核参数
sudo sysctl -p

# 删除不必要的包
sudo apt autoremove -y
sudo apt autoclean

# 设置自动安全更新
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

echo "Security hardening completed!"
EOF

chmod +x ~/security-hardening.sh
```

---

## 🎯 安全最佳实践总结

1. **定期更新**：保持系统和应用的最新版本
2. **最小权限原则**：只开放必要的端口和服务
3. **强密码策略**：使用复杂密码和双因素认证
4. **监控和日志**：持续监控系统活动
5. **备份策略**：定期备份重要数据和配置
6. **安全训练**：了解最新的安全威胁和防护措施

按照此配置指南，您的服务器将具有企业级的安全防护能力。记住安全是一个持续的过程，需要定期审查和更新。