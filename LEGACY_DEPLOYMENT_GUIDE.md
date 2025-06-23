# 🔍 传统部署排查和管理指南

根据您提供的命令信息，您的服务器上使用的是传统的systemd + Gunicorn + Nginx部署方式。本指南将帮助您重新掌控现有部署。

---

## 🚀 快速开始

### 1. 上传管理脚本到服务器
```bash
# 将 legacy-server-manager.sh 上传到服务器
scp legacy-server-manager.sh user@your-server:~/
```

### 2. 在服务器上运行管理工具
```bash
# SSH到服务器
ssh user@your-server

# 运行管理脚本
chmod +x legacy-server-manager.sh
./legacy-server-manager.sh
```

---

## 📋 现有部署架构分析

根据您的备份命令，推测您的部署架构如下：

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     用户请求    │───▶│      Nginx      │───▶│   ai_flashcard  │
│                 │    │   (反向代理)    │    │   (systemd)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                               ┌─────────────────┐
                                               │    Gunicorn     │
                                               │  (WSGI服务器)   │
                                               └─────────────────┘
                                                       │
                                                       ▼
                                               ┌─────────────────┐
                                               │  Flask/FastAPI  │
                                               │   应用代码      │
                                               └─────────────────┘
```

---

## 🔧 手动管理命令

基于您提供的备份命令，以下是完整的管理命令集：

### 服务管理命令
```bash
# 查看服务状态
sudo systemctl status ai_flashcard

# 启动服务
sudo systemctl start ai_flashcard

# 停止服务
sudo systemctl stop ai_flashcard

# 重启服务
sudo systemctl restart ai_flashcard

# 查看服务是否开机自启
sudo systemctl is-enabled ai_flashcard

# 启用开机自启
sudo systemctl enable ai_flashcard

# 禁用开机自启
sudo systemctl disable ai_flashcard
```

### 日志查看命令
```bash
# 查看错误日志（实时）
sudo tail -f /var/log/gunicorn/ai_flashcard-error.log

# 查看错误日志（最后50行）
sudo tail -50 /var/log/gunicorn/ai_flashcard-error.log

# 查看访问日志
sudo tail -f /var/log/gunicorn/ai_flashcard-access.log

# 查看systemd服务日志
sudo journalctl -u ai_flashcard -f

# 查看systemd服务日志（最近100行）
sudo journalctl -u ai_flashcard -n 100
```

### Nginx管理命令
```bash
# 检查nginx配置
sudo nginx -t

# 重启nginx
sudo systemctl restart nginx

# 重新加载nginx配置（无需停止服务）
sudo systemctl reload nginx

# 查看nginx状态
sudo systemctl status nginx

# 查看nginx错误日志
sudo tail -f /var/log/nginx/error.log

# 查看nginx访问日志
sudo tail -f /var/log/nginx/access.log
```

---

## 🔍 排查步骤指南

### 第1步：发现服务
```bash
# 查找flashcard相关服务
systemctl list-units --type=service | grep -i flashcard

# 查找运行中的gunicorn进程
ps aux | grep gunicorn | grep -v grep

# 查看端口占用
sudo netstat -tlnp | grep -E ':80|:443|:8000|:8080|:5000'
```

### 第2步：定位应用目录
```bash
# 查找应用代码目录
find /home -name "*flashcard*" -type d 2>/dev/null
find /opt -name "*flashcard*" -type d 2>/dev/null
find /var/www -name "*flashcard*" -type d 2>/dev/null

# 查看systemd服务文件内容（包含应用路径）
sudo systemctl cat ai_flashcard
```

### 第3步：检查配置文件
```bash
# 查找systemd服务文件
find /etc/systemd/system -name "*flashcard*"

# 查找nginx配置文件
find /etc/nginx -name "*flashcard*"
sudo nginx -T | grep -i flashcard

# 查看nginx sites配置
ls -la /etc/nginx/sites-enabled/
ls -la /etc/nginx/sites-available/
```

### 第4步：测试访问
```bash
# 获取服务器IP
curl ifconfig.me

# 测试本地访问
curl http://localhost
curl http://localhost:8000
curl http://localhost:5000

# 测试外部访问
curl http://YOUR_SERVER_IP
```

---

## 🚨 常见问题排查

### 问题1：服务无法启动
```bash
# 查看详细错误信息
sudo systemctl status ai_flashcard -l
sudo journalctl -u ai_flashcard --no-pager -l

# 检查配置文件权限
sudo systemctl cat ai_flashcard

# 手动测试gunicorn命令
# (从systemd服务文件中复制ExecStart命令)
```

### 问题2：Nginx配置错误
```bash
# 测试nginx配置
sudo nginx -t

# 查看nginx错误日志
sudo tail -20 /var/log/nginx/error.log

# 检查nginx配置语法
sudo nginx -T | grep -C 5 error
```

### 问题3：端口冲突
```bash
# 查看端口占用
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :8000

# 杀死占用端口的进程
sudo fuser -k 80/tcp
sudo fuser -k 8000/tcp
```

### 问题4：权限问题
```bash
# 检查应用目录权限
ls -la /path/to/your/app

# 检查日志目录权限
ls -la /var/log/gunicorn/

# 修复权限（根据需要调整）
sudo chown -R www-data:www-data /path/to/your/app
sudo chmod -R 755 /path/to/your/app
```

---

## 📦 备份现有部署

在进行任何更改之前，建议先备份现有部署：

```bash
# 创建备份目录
mkdir -p ~/deployment-backup-$(date +%Y%m%d)
cd ~/deployment-backup-$(date +%Y%m%d)

# 备份systemd服务文件
sudo cp /etc/systemd/system/ai_flashcard.service ./

# 备份nginx配置
sudo cp -r /etc/nginx/sites-available ./nginx-sites-available
sudo cp -r /etc/nginx/sites-enabled ./nginx-sites-enabled

# 备份应用代码（找到目录后替换路径）
cp -r /path/to/your/flashcard/app ./app-code

# 备份日志文件
sudo cp -r /var/log/gunicorn ./gunicorn-logs

# 记录当前进程状态
ps aux | grep -E 'gunicorn|nginx' > process-status.txt
systemctl status ai_flashcard > service-status.txt
sudo nginx -T > nginx-config-full.txt
```

---

## 🔄 迁移到Docker部署（可选）

如果您想迁移到Docker部署，可以：

### 1. 备份现有部署
```bash
./legacy-server-manager.sh  # 选择选项9创建备份
```

### 2. 停止现有服务
```bash
sudo systemctl stop ai_flashcard
sudo systemctl disable ai_flashcard
# 保留nginx或根据需要停止
```

### 3. 使用新的Docker部署
```bash
# 使用之前创建的部署脚本
./server-deploy.sh
```

---

## 📞 紧急恢复命令

如果服务出现问题，按以下顺序尝试恢复：

```bash
# 1. 重启应用服务
sudo systemctl restart ai_flashcard

# 2. 如果应用服务重启失败，查看错误
sudo systemctl status ai_flashcard -l
sudo journalctl -u ai_flashcard -n 50

# 3. 重启nginx
sudo nginx -t && sudo systemctl restart nginx

# 4. 如果仍有问题，重启所有相关服务
sudo systemctl restart ai_flashcard nginx

# 5. 最后手段：重启服务器
sudo reboot
```

---

## 💡 使用建议

1. **优先使用管理脚本**：运行 `./legacy-server-manager.sh` 来自动化管理
2. **创建别名**：在 `~/.bashrc` 中添加常用命令别名
3. **定期备份**：定期备份配置和应用代码
4. **监控日志**：设置日志轮转，避免磁盘空间耗尽
5. **文档记录**：记录所有配置更改和部署信息

现在您可以使用管理脚本或手动命令来重新掌控您的现有部署！