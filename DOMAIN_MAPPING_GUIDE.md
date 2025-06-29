# 域名映射部署指南

## 🎯 目标架构

将AI闪卡生成器从直接IP访问 `198.23.164.200:8000` 映射到域名访问：
- `www.explain1thing.top` → 个人主页
- `explain1thing.top/ai-flashcard-generator` → AI闪卡生成器
- 保护8000端口，禁止外部直接访问

## 📋 部署步骤

### 1. 准备工作

#### 1.1 检查服务器状态
```bash
# 检查nginx状态
nginx -v
systemctl status nginx

# 检查Docker容器
docker ps | grep 8000

# 检查防火墙
ufw status
```

#### 1.2 获取Cloudflare Origin Certificate
1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 选择域名 `explain1thing.top`
3. 进入 **SSL/TLS** → **Origin Server**
4. 点击 **Create Certificate**
5. 配置证书：
   - 选择 **Let Cloudflare generate a private key and a CSR**
   - Hostnames: `explain1thing.top, *.explain1thing.top`
   - Certificate validity: **15 years**
6. 保存证书内容备用

### 2. 安装和配置nginx

#### 2.1 安装nginx（如果未安装）
```bash
apt update && apt install -y nginx
systemctl start nginx
systemctl enable nginx
```

#### 2.2 复制AI闪卡文件
```bash
# 创建nginx服务目录
mkdir -p /var/www/ai-flashcard-generator

# 复制文件（使用最新版本）
cp -r /root/ai-flashcard-generator/src/* /var/www/ai-flashcard-generator/

# 设置权限
chown -R www-data:www-data /var/www/ai-flashcard-generator
```

#### 2.3 修复前端API配置
```bash
# 备份原文件
cp /var/www/ai-flashcard-generator/unified_index.html /var/www/ai-flashcard-generator/unified_index.html.backup

# 编辑文件修复API_BASE_URL
nano /var/www/ai-flashcard-generator/unified_index.html
```

找到并修改（约2115-2121行）：
```javascript
// 修改前
window.API_BASE_URL = '';

// 修改后
window.API_BASE_URL = '/ai-flashcard-generator/api';
```

### 3. 配置nginx反向代理

#### 3.1 创建nginx配置文件
```bash
cat > /etc/nginx/sites-available/explain1thing_final.conf << 'EOF'
server {
    listen 80;
    listen [::]:80;
    
    server_name www.explain1thing.top explain1thing.top _;
    
    # 个人主页
    location / {
        root /var/www/explain1thing_root;
        index index.html;
        try_files $uri $uri/ =404;
    }
    
    # AI闪卡生成器
    location /ai-flashcard-generator/ {
        alias /var/www/ai-flashcard-generator/;
        index unified_index.html;
        try_files $uri $uri/ =404;
    }
    
    # 无斜杠重定向
    location /ai-flashcard-generator {
        return 301 $scheme://$host$uri/;
    }
    
    # API代理
    location /ai-flashcard-generator/api/ {
        rewrite ^/ai-flashcard-generator/api/(.*)$ /$1 break;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置（LLM响应较慢）
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF
```

#### 3.2 启用nginx配置
```bash
# 删除默认配置
rm -f /etc/nginx/sites-enabled/default*
rm -f /etc/nginx/sites-enabled/ai_flashcard_generator*

# 启用新配置
ln -sf /etc/nginx/sites-available/explain1thing_final.conf /etc/nginx/sites-enabled/

# 测试配置
nginx -t

# 重新加载nginx
systemctl reload nginx
```

### 4. 保护8000端口

#### 4.1 修改Docker端口绑定
```bash
# 停止现有容器
docker stop flashcard-generator

# 重新创建容器，只绑定到本地
docker run -d --name flashcard-generator-new \
  --restart unless-stopped \
  -p 127.0.0.1:8000:8000 \
  --mount type=bind,source=/root/ai-flashcard-generator/src/config,target=/app/config,readonly \
  ai-flashcard-generator-flashcard-app

# 删除旧容器
docker rm flashcard-generator
```

#### 4.2 配置防火墙
```bash
# 删除现有8000端口规则
ufw delete allow 8000/tcp

# 只允许本机访问8000端口
ufw allow from 127.0.0.1 to any port 8000
ufw allow from ::1 to any port 8000

# 验证防火墙状态
ufw status | grep 8000
```

### 5. 配置Cloudflare

#### 5.1 设置SSL模式（临时）
1. 进入 **SSL/TLS** → **概述**
2. 将加密模式设置为 **"灵活"**（因为后端使用HTTP）

#### 5.2 验证DNS解析
确保域名DNS记录指向服务器IP：
- A记录：`explain1thing.top` → `198.23.164.200`
- A记录：`www.explain1thing.top` → `198.23.164.200`

### 6. 测试验证

#### 6.1 本地测试
```bash
# 测试个人主页
curl -I http://127.0.0.1/

# 测试AI闪卡应用
curl -I http://127.0.0.1/ai-flashcard-generator/

# 测试API代理
curl http://127.0.0.1/ai-flashcard-generator/api/health

# 验证8000端口保护
curl --connect-timeout 5 http://198.23.164.200:8000/health || echo "外部访问已被阻止 ✓"
```

#### 6.2 域名测试
访问以下URL验证：
- `https://www.explain1thing.top` → 个人主页
- `https://explain1thing.top/ai-flashcard-generator` → AI闪卡应用
- `http://explain1thing.top` → 自动重定向到HTTPS

#### 6.3 SSL验证
```bash
# 验证SSL证书
openssl s_client -connect explain1thing.top:443 -servername explain1thing.top < /dev/null 2>/dev/null | openssl x509 -noout -issuer -subject -dates

# 预期输出：
# issuer=C = US, O = Let's Encrypt, CN = E6
# subject=CN = explain1thing.top
# 证书有效期到2025年8月

# 验证443端口监听
ss -tlnp | grep :443

# 验证HTTPS访问
curl -I https://explain1thing.top/ai-flashcard-generator/
```

## ✅ SSL证书配置（已完成）

已成功实现完整的端到端HTTPS加密，使用Let's Encrypt证书：

### 1. SSL证书状态
- ✅ **Let's Encrypt证书**: 已配置并正常工作
- ✅ **nginx HTTPS配置**: 443端口正常监听
- ✅ **Cloudflare完全(严格)模式**: 端到端加密已启用
- ✅ **自动续期机制**: Let's Encrypt自动续期已配置

### 2. 当前HTTPS配置
```bash
# 当前生产配置文件：/etc/nginx/sites-available/explain1thing_ssl.conf
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    
    server_name www.explain1thing.top explain1thing.top;
    
    # Let's Encrypt SSL证书
    ssl_certificate /etc/letsencrypt/live/explain1thing.top/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/explain1thing.top/privkey.pem;
    
    # SSL优化配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    
    # 应用配置（个人主页、AI应用、API代理）...
}

# HTTP重定向到HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name www.explain1thing.top explain1thing.top;
    return 301 https://$host$request_uri;
}
```

### 3. SSL验证命令
```bash
# 检查SSL证书信息
openssl s_client -connect explain1thing.top:443 -servername explain1thing.top < /dev/null 2>/dev/null | openssl x509 -noout -issuer -subject -dates

# 验证端到端HTTPS
curl -I https://explain1thing.top/ai-flashcard-generator/

# 检查443端口监听
ss -tlnp | grep :443
```

## 🎯 最终架构

```
用户 → Cloudflare (HTTPS) → nginx (HTTPS) → Docker容器 (HTTP, 仅本地)
     ↓
个人主页: www.explain1thing.top
AI应用: explain1thing.top/ai-flashcard-generator
API: explain1thing.top/ai-flashcard-generator/api/*
```

**架构特点**:
- 🔒 **端到端HTTPS加密**: 用户到Cloudflare，Cloudflare到nginx全程HTTPS
- 🛡️ **多层安全防护**: Cloudflare WAF + nginx SSL + 防火墙规则
- ⚡ **高性能**: HTTP/2支持，SSL会话缓存优化
- 🔄 **自动重定向**: HTTP自动301重定向到HTTPS

## 🔒 安全特性

- ✅ **8000端口保护**: 仅允许本机nginx访问
- ✅ **防火墙规则**: 保护Docker容器外部访问
- ✅ **Cloudflare防护**: DDoS和WAF完整保护
- ✅ **端到端SSL加密**: Let's Encrypt证书，完全(严格)模式
- ✅ **HTTP重定向**: 自动301重定向到HTTPS
- ✅ **SSL优化**: TLS 1.2/1.3，会话缓存，HTTP/2支持
- ✅ **证书自动续期**: Let's Encrypt自动续期机制

## 🐛 常见问题

### 问题1：404 Not Found
- 检查nginx配置语法：`nginx -t`
- 检查文件权限：`ls -la /var/www/ai-flashcard-generator/`
- 检查nginx日志：`tail -f /var/log/nginx/error.log`

### 问题2：API调用失败
- 检查前端API_BASE_URL配置
- 验证API代理：`curl http://127.0.0.1/ai-flashcard-generator/api/health`
- 检查Docker容器状态：`docker logs flashcard-generator-new`

### 问题3：8000端口仍可外部访问
- 验证Docker端口绑定：`docker ps | grep 8000`
- 检查防火墙规则：`ufw status | grep 8000`
- 确认没有其他程序占用8000端口：`ss -tlnp | grep 8000`