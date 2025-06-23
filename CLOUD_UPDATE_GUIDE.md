# 🚀 云端部署更新指南

## 📋 **快速更新步骤**

### 1️⃣ **SSH连接到云端服务器**
```bash
ssh user@198.23.164.200
```

### 2️⃣ **进入项目目录**
```bash
cd ~/apps/flashcard_generator_mvp
```

### 3️⃣ **拉取最新代码**
```bash
git pull origin main
```

### 4️⃣ **查看更新内容**
```bash
git log --oneline -3
```

### 5️⃣ **执行快速部署**
```bash
./quick-deploy.sh
```

### 6️⃣ **验证部署状态**
```bash
docker compose ps
curl http://localhost:8000/health
```

---

## 🔄 **替代方案：手动更新**

如果快速部署脚本有问题，可以手动执行：

```bash
# 重新构建镜像
docker compose build --no-cache

# 重启服务
docker compose down
docker compose up -d

# 等待启动
sleep 30

# 检查状态
docker compose ps
```

---

## ✅ **验证新功能**

### 🌙 **夜间模式测试**
1. 访问: http://198.23.164.200:8000
2. 查看右上角圆形主题切换按钮
3. 点击按钮，应该循环切换：太阳→月亮→星星→太阳
4. 进入"设置"标签页，检查主题选择下拉菜单
5. 刷新页面，主题设置应该保持

### 📱 **功能检查清单**
- [ ] 应用可正常访问
- [ ] 夜间模式切换按钮显示
- [ ] 主题切换功能正常
- [ ] 设置面板主题选项可用
- [ ] 卡片生成功能正常
- [ ] 导出功能正常
- [ ] 所有现有功能保持正常

---

## 🚨 **故障排除**

### 如果服务启动失败：
```bash
# 查看容器日志
docker compose logs flashcard-app

# 查看系统资源
free -h
df -h

# 重启Docker服务
sudo systemctl restart docker
```

### 如果API无响应：
```bash
# 检查端口占用
sudo netstat -tlnp | grep 8000

# 检查防火墙
sudo ufw status

# 重启应用容器
docker compose restart flashcard-app
```

### 如果需要回滚：
```bash
# 查看git历史
git log --oneline -5

# 回滚到上一个版本
git reset --hard HEAD~1

# 重新部署
./quick-deploy.sh
```

---

## 📞 **获取帮助**

如果遇到问题：
1. 查看容器日志：`docker compose logs -f flashcard-app`
2. 运行部署检查：`python3 deployment-check.py`
3. 检查系统状态：`./monitor.sh`（如果存在）

---

## 🎉 **更新内容**

本次更新包含：
- ✨ **夜间模式功能**：三种主题模式（浅色/深色/跟随系统）
- 🎨 **主题切换**：右上角快速切换按钮
- ⚙️ **设置面板**：主题选择下拉菜单
- 💾 **状态保存**：主题选择自动保存到本地
- 📝 **文档更新**：README反映云端部署状态

---

*更新时间：2025-06-23*
*版本：v2.1 - 夜间模式更新*