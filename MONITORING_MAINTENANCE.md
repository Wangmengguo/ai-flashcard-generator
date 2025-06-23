# 📊 监控和维护指南

针对您的Debian 12服务器（2GB RAM）的AI Flashcard Generator的全面监控和维护策略。

---

## 🔍 第一部分：系统监控

### 1.1 实时监控仪表板

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

echo ""

# CPU使用率
echo "🖥️  CPU使用率："
top -bn1 | grep "Cpu(s)" | awk '{print "CPU Usage: " $2}'

echo ""

# 内存使用
echo "💾 内存使用："
free -h | awk 'NR==2{printf "内存使用: %s/%s (%.2f%%)\n", $3,$2,$3*100/$2}'

echo ""

# 磁盘使用
echo "💿 磁盘使用："
df -h | grep -vE '^Filesystem|tmpfs|cdrom' | awk '{print $5 " " $1 " (" $3 "/" $2 ")"}'

echo ""

# Docker容器状态
echo "🐳 Docker容器状态："
if command -v docker &> /dev/null; then
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo "Docker未安装或未运行"
fi

echo ""

# 网络连接
echo "🌐 网络连接："
ss -tuln | grep -E ':80|:443|:8000|:22' | wc -l | awk '{print "活跃连接数: " $1}'

echo ""

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

# 最近的错误日志
echo "📝 最近的应用日志（最后5条）："
if [ -f ~/apps/flashcard_generator_mvp/logs/app.log ]; then
    tail -5 ~/apps/flashcard_generator_mvp/logs/app.log | cut -c1-80
else
    echo "日志文件不存在"
fi

echo ""
echo "==============================================="
echo "刷新：watch -n 30 ~/dashboard.sh"
echo "退出：Ctrl+C"
EOF

chmod +x ~/dashboard.sh
```

### 1.2 性能监控脚本

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

### 1.3 应用监控脚本

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

# 检查错误日志
ERROR_COUNT=0
if [ -f "logs/app.log" ]; then
    ERROR_COUNT=$(grep -c "ERROR\|CRITICAL" logs/app.log)
fi

# 内存使用（Docker容器）
CONTAINER_MEMORY="N/A"
if [ "$CONTAINER_STATUS" -gt 0 ]; then
    CONTAINER_MEMORY=$(docker stats --no-stream --format "{{.MemUsage}}" flashcard-generator 2>/dev/null | head -1)
fi

# 记录监控数据
echo "$TIMESTAMP,CONTAINERS:$CONTAINER_STATUS/$TOTAL_CONTAINERS,API:$API_HEALTH,MODELS:$MODELS_HEALTH,ERRORS:$ERROR_COUNT,MEM:$CONTAINER_MEMORY" >> $APP_LOG

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

---

## 📈 第二部分：日志管理

### 2.1 日志收集和轮换

```bash
# 创建日志管理脚本
cat > ~/log-manager.sh << 'EOF'
#!/bin/bash

LOG_DIR="$HOME/apps/flashcard_generator_mvp/logs"
ARCHIVE_DIR="$HOME/log-archives"
DATE=$(date +%Y%m%d)

# 创建归档目录
mkdir -p $ARCHIVE_DIR

# 轮换应用日志
if [ -f "$LOG_DIR/app.log" ]; then
    # 如果日志文件大于10MB，进行轮换
    if [ $(stat -f%z "$LOG_DIR/app.log" 2>/dev/null || stat -c%s "$LOG_DIR/app.log") -gt 10485760 ]; then
        mv "$LOG_DIR/app.log" "$ARCHIVE_DIR/app-$DATE.log"
        touch "$LOG_DIR/app.log"
        docker compose restart flashcard-app
        echo "$(date): 应用日志已轮换" >> $HOME/log-rotation.log
    fi
fi

# 压缩旧日志
find $ARCHIVE_DIR -name "*.log" -mtime +1 -exec gzip {} \;

# 删除超过30天的日志
find $ARCHIVE_DIR -name "*.gz" -mtime +30 -delete

# 清理Docker日志
docker system prune -f --volumes

echo "$(date): 日志管理完成" >> $HOME/log-rotation.log
EOF

chmod +x ~/log-manager.sh

# 每天凌晨3点运行日志管理
(crontab -l 2>/dev/null; echo "0 3 * * * $HOME/log-manager.sh") | crontab -
```

### 2.2 日志分析工具

```bash
# 创建日志分析脚本
cat > ~/log-analyzer.sh << 'EOF'
#!/bin/bash

APP_LOG="$HOME/apps/flashcard_generator_mvp/logs/app.log"
ANALYSIS_LOG="$HOME/log-analysis.log"
DATE=$(date '+%Y-%m-%d')

if [ ! -f "$APP_LOG" ]; then
    echo "应用日志文件不存在: $APP_LOG"
    exit 1
fi

echo "=== 日志分析报告 - $DATE ===" > $ANALYSIS_LOG

# 错误统计
echo "📊 错误统计:" >> $ANALYSIS_LOG
grep -c "ERROR" $APP_LOG >> $ANALYSIS_LOG
grep -c "WARNING" $APP_LOG >> $ANALYSIS_LOG
grep -c "CRITICAL" $APP_LOG >> $ANALYSIS_LOG

# API调用统计
echo "📈 API调用统计:" >> $ANALYSIS_LOG
grep -c "/supported_models" $APP_LOG >> $ANALYSIS_LOG
grep -c "/generate_flashcards" $APP_LOG >> $ANALYSIS_LOG
grep -c "/health" $APP_LOG >> $ANALYSIS_LOG

# 最常见的错误
echo "🔍 最常见的错误:" >> $ANALYSIS_LOG
grep "ERROR\|CRITICAL" $APP_LOG | awk '{print $NF}' | sort | uniq -c | sort -nr | head -5 >> $ANALYSIS_LOG

# 响应时间分析
echo "⏱️  响应时间分析:" >> $ANALYSIS_LOG
grep "duration" $APP_LOG | awk '{print $NF}' | sort -n | awk '
    BEGIN { count = 0; sum = 0 }
    { values[count] = $1; sum += $1; count++ }
    END {
        if (count > 0) {
            printf "平均响应时间: %.2fs\n", sum/count
            printf "中位数响应时间: %.2fs\n", values[int(count/2)]
            printf "最大响应时间: %.2fs\n", values[count-1]
        }
    }
' >> $ANALYSIS_LOG

echo "=== 分析完成 ===" >> $ANALYSIS_LOG
EOF

chmod +x ~/log-analyzer.sh

# 每天生成日志分析报告
(crontab -l 2>/dev/null; echo "0 6 * * * $HOME/log-analyzer.sh") | crontab -
```

---

## 🔧 第三部分：自动化维护

### 3.1 系统维护脚本

```bash
# 创建自动化维护脚本
cat > ~/auto-maintenance.sh << 'EOF'
#!/bin/bash

MAINTENANCE_LOG="$HOME/maintenance.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] 开始自动维护任务" >> $MAINTENANCE_LOG

# 1. 系统更新检查
echo "检查系统更新..." >> $MAINTENANCE_LOG
UPDATES=$(apt list --upgradable 2>/dev/null | wc -l)
if [ $UPDATES -gt 1 ]; then
    echo "发现 $UPDATES 个可用更新" >> $MAINTENANCE_LOG
    # 自动安装安全更新（可选）
    # sudo apt update && sudo apt upgrade -y
fi

# 2. 清理临时文件
echo "清理临时文件..." >> $MAINTENANCE_LOG
sudo apt autoremove -y >> $MAINTENANCE_LOG 2>&1
sudo apt autoclean >> $MAINTENANCE_LOG 2>&1

# 3. Docker维护
echo "Docker系统维护..." >> $MAINTENANCE_LOG
docker system prune -f >> $MAINTENANCE_LOG 2>&1

# 4. 检查磁盘空间
DISK_USAGE=$(df / | awk 'NR==2{print $5}' | cut -d'%' -f1)
echo "磁盘使用率: $DISK_USAGE%" >> $MAINTENANCE_LOG
if [ $DISK_USAGE -gt 80 ]; then
    echo "⚠️  磁盘空间不足" >> $MAINTENANCE_LOG
    # 清理更多空间
    docker image prune -a -f >> $MAINTENANCE_LOG 2>&1
fi

# 5. 内存优化
echo "内存优化..." >> $MAINTENANCE_LOG
sync
sudo sysctl -w vm.drop_caches=3

# 6. 检查服务状态
echo "检查关键服务状态..." >> $MAINTENANCE_LOG
systemctl is-active docker >> $MAINTENANCE_LOG
systemctl is-active ufw >> $MAINTENANCE_LOG
systemctl is-active fail2ban >> $MAINTENANCE_LOG

# 7. 应用健康检查
cd $HOME/apps/flashcard_generator_mvp
if docker compose ps | grep -q "Up"; then
    echo "✅ 应用容器运行正常" >> $MAINTENANCE_LOG
else
    echo "❌ 应用容器异常，尝试重启" >> $MAINTENANCE_LOG
    docker compose up -d >> $MAINTENANCE_LOG 2>&1
fi

echo "[$DATE] 自动维护任务完成" >> $MAINTENANCE_LOG
echo "===========================================" >> $MAINTENANCE_LOG
EOF

chmod +x ~/auto-maintenance.sh

# 每周日凌晨1点运行维护任务
(crontab -l 2>/dev/null; echo "0 1 * * 0 $HOME/auto-maintenance.sh") | crontab -
```

### 3.2 备份自动化

```bash
# 增强备份脚本
cat > ~/enhanced-backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="$HOME/backups"
REMOTE_BACKUP="/tmp/remote-backup"  # 可配置为远程存储
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"
mkdir -p "$REMOTE_BACKUP"

echo "开始备份 - $DATE"

# 1. 配置文件备份
echo "备份配置文件..."
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
    ~/apps/flashcard_generator_mvp/.env* \
    ~/apps/flashcard_generator_mvp/docker-compose.yml \
    ~/apps/flashcard_generator_mvp/nginx/ \
    ~/.crontab_backup 2>/dev/null

# 2. 应用日志备份
echo "备份应用日志..."
if [ -d ~/apps/flashcard_generator_mvp/logs ]; then
    tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" \
        ~/apps/flashcard_generator_mvp/logs/
fi

# 3. 系统配置备份
echo "备份系统配置..."
tar -czf "$BACKUP_DIR/system_$DATE.tar.gz" \
    /etc/nginx/ \
    /etc/docker/ \
    /etc/fail2ban/ \
    /etc/ufw/ 2>/dev/null

# 4. 监控数据备份
echo "备份监控数据..."
tar -czf "$BACKUP_DIR/monitoring_$DATE.tar.gz" \
    ~/performance-monitor.log \
    ~/app-monitor.log \
    ~/security-monitor.log \
    ~/alerts.log 2>/dev/null

# 5. 数据库备份（如果有）
# if docker compose ps | grep -q postgres; then
#     docker compose exec postgres pg_dump -U user flashcard > "$BACKUP_DIR/db_$DATE.sql"
# fi

# 6. 创建备份清单
echo "创建备份清单..."
cat > "$BACKUP_DIR/backup_manifest_$DATE.txt" << EOL
备份时间: $DATE
服务器: $(hostname)
磁盘使用: $(df -h / | awk 'NR==2{print $5}')
内存使用: $(free -h | awk 'NR==2{print $3 "/" $2}')
Docker容器: $(docker ps --format 'table {{.Names}}\t{{.Status}}')

备份文件:
$(ls -lh $BACKUP_DIR/*_$DATE.*)
EOL

# 7. 验证备份完整性
echo "验证备份完整性..."
for file in $BACKUP_DIR/*_$DATE.*; do
    if [ -f "$file" ]; then
        if file "$file" | grep -q "gzip compressed"; then
            echo "✅ $file - 压缩文件正常"
        else
            echo "❌ $file - 文件可能损坏"
        fi
    fi
done

# 8. 同步到远程备份位置（可选）
# rsync -av $BACKUP_DIR/ user@remote-server:$REMOTE_BACKUP/

# 9. 清理旧备份
echo "清理旧备份..."
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.txt" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.sql" -mtime +$RETENTION_DAYS -delete

# 10. 生成备份报告
BACKUP_SIZE=$(du -sh $BACKUP_DIR | awk '{print $1}')
echo "备份完成 - 总大小: $BACKUP_SIZE"

# 记录到日志
echo "$DATE: 备份完成，大小: $BACKUP_SIZE" >> ~/backup.log
EOF

chmod +x ~/enhanced-backup.sh

# 每天凌晨2点备份
(crontab -l 2>/dev/null; echo "0 2 * * * $HOME/enhanced-backup.sh >> $HOME/backup.log 2>&1") | crontab -
```

---

## 📊 第四部分：性能优化

### 4.1 性能调优脚本

```bash
# 创建性能优化脚本
cat > ~/performance-tuning.sh << 'EOF'
#!/bin/bash

echo "开始性能调优..."

# 1. 系统参数优化
echo "优化系统参数..."
sudo tee -a /etc/sysctl.conf > /dev/null <<EOL
# 针对2GB RAM服务器的优化
vm.swappiness=10
vm.dirty_ratio=15
vm.dirty_background_ratio=5
vm.vfs_cache_pressure=50

# 网络优化
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 16384 16777216
net.ipv4.tcp_wmem = 4096 16384 16777216
net.ipv4.tcp_congestion_control = bbr

# 文件句柄限制
fs.file-max = 65536
EOL

# 应用系统参数
sudo sysctl -p

# 2. Docker优化
echo "优化Docker配置..."
sudo tee /etc/docker/daemon.json > /dev/null <<EOL
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "5m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "live-restore": true,
  "default-address-pools": [
    {"base": "172.30.0.0/16", "size": 24}
  ],
  "max-concurrent-downloads": 3,
  "max-concurrent-uploads": 3
}
EOL

# 重启Docker
sudo systemctl restart docker

# 3. 应用配置优化
echo "优化应用配置..."
cd ~/apps/flashcard_generator_mvp

# 更新环境变量以适应2GB RAM
sed -i 's/WORKERS=4/WORKERS=2/' .env
sed -i 's/MAX_REQUESTS=1000/MAX_REQUESTS=500/' .env

# 重启应用
docker compose restart flashcard-app

echo "性能调优完成"
EOF

chmod +x ~/performance-tuning.sh
```

### 4.2 资源监控和警报

```bash
# 创建资源警报脚本
cat > ~/resource-alerts.sh << 'EOF'
#!/bin/bash

ALERT_LOG="$HOME/alerts.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 阈值设置（针对2GB RAM服务器）
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=85
LOAD_THRESHOLD=2.0
CONNECTION_THRESHOLD=100

# 获取当前指标
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100)}')
DISK_USAGE=$(df / | awk 'NR==2{print $5}' | cut -d'%' -f1)
LOAD_AVG=$(uptime | awk '{print $10}' | cut -d',' -f1)
CONNECTIONS=$(ss -tu | wc -l)

# CPU检查
if (( $(echo "$CPU_USAGE > $CPU_THRESHOLD" | bc -l) )); then
    echo "[$TIMESTAMP] 🚨 CPU使用率过高: ${CPU_USAGE}%" >> $ALERT_LOG
    # 发送邮件或webhook通知（可选）
    # curl -X POST -H 'Content-type: application/json' --data '{"text":"CPU使用率过高: '${CPU_USAGE}'%"}' YOUR_SLACK_WEBHOOK
fi

# 内存检查
if (( $(echo "$MEMORY_USAGE > $MEMORY_THRESHOLD" | bc -l) )); then
    echo "[$TIMESTAMP] 🚨 内存使用率过高: ${MEMORY_USAGE}%" >> $ALERT_LOG
    # 尝试清理内存
    sync && sudo sysctl -w vm.drop_caches=3
fi

# 磁盘检查
if [ "$DISK_USAGE" -gt "$DISK_THRESHOLD" ]; then
    echo "[$TIMESTAMP] 🚨 磁盘使用率过高: ${DISK_USAGE}%" >> $ALERT_LOG
    # 自动清理
    docker system prune -f >/dev/null 2>&1
fi

# 负载检查
if (( $(echo "$LOAD_AVG > $LOAD_THRESHOLD" | bc -l) )); then
    echo "[$TIMESTAMP] 🚨 系统负载过高: ${LOAD_AVG}" >> $ALERT_LOG
fi

# 连接数检查
if [ "$CONNECTIONS" -gt "$CONNECTION_THRESHOLD" ]; then
    echo "[$TIMESTAMP] 🚨 网络连接数过多: ${CONNECTIONS}" >> $ALERT_LOG
fi

# 应用健康检查
if ! curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    echo "[$TIMESTAMP] 🚨 应用健康检查失败" >> $ALERT_LOG
    # 尝试重启应用
    cd ~/apps/flashcard_generator_mvp
    docker compose restart flashcard-app
    echo "[$TIMESTAMP] 🔄 已尝试重启应用" >> $ALERT_LOG
fi
EOF

chmod +x ~/resource-alerts.sh

# 每分钟检查一次资源状态
(crontab -l 2>/dev/null; echo "* * * * * $HOME/resource-alerts.sh") | crontab -
```

---

## 📋 第五部分：维护检查清单

### 5.1 每日检查清单

```bash
# 创建每日检查脚本
cat > ~/daily-check.sh << 'EOF'
#!/bin/bash

CHECK_LOG="$HOME/daily-check.log"
DATE=$(date '+%Y-%m-%d')

echo "=== 每日检查报告 - $DATE ===" > $CHECK_LOG

# 1. 系统状态
echo "1. 系统状态检查:" >> $CHECK_LOG
uptime >> $CHECK_LOG
free -h >> $CHECK_LOG
df -h >> $CHECK_LOG

# 2. 服务状态
echo "2. 服务状态检查:" >> $CHECK_LOG
systemctl is-active docker >> $CHECK_LOG
systemctl is-active ufw >> $CHECK_LOG
systemctl is-active fail2ban >> $CHECK_LOG

# 3. Docker容器状态
echo "3. Docker容器状态:" >> $CHECK_LOG
docker ps >> $CHECK_LOG

# 4. 应用健康检查
echo "4. 应用健康检查:" >> $CHECK_LOG
if curl -sf http://localhost:8000/health >/dev/null; then
    echo "✅ 应用健康状态正常" >> $CHECK_LOG
else
    echo "❌ 应用健康状态异常" >> $CHECK_LOG
fi

# 5. 安全检查
echo "5. 安全检查:" >> $CHECK_LOG
sudo fail2ban-client status >> $CHECK_LOG
sudo ufw status >> $CHECK_LOG

# 6. 日志检查
echo "6. 错误日志检查:" >> $CHECK_LOG
if [ -f ~/apps/flashcard_generator_mvp/logs/app.log ]; then
    ERROR_COUNT=$(grep -c "ERROR\|CRITICAL" ~/apps/flashcard_generator_mvp/logs/app.log)
    echo "今日错误数量: $ERROR_COUNT" >> $CHECK_LOG
fi

# 7. 备份状态
echo "7. 备份状态检查:" >> $CHECK_LOG
if [ -d ~/backups ]; then
    LATEST_BACKUP=$(ls -t ~/backups/config_*.tar.gz 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        echo "最新备份: $LATEST_BACKUP" >> $CHECK_LOG
        echo "备份时间: $(stat -c %y "$LATEST_BACKUP")" >> $CHECK_LOG
    else
        echo "❌ 未找到备份文件" >> $CHECK_LOG
    fi
fi

echo "=== 检查完成 ===" >> $CHECK_LOG

# 显示摘要
echo "每日检查完成，报告已保存到: $CHECK_LOG"
grep -E "✅|❌|ERROR|CRITICAL" $CHECK_LOG
EOF

chmod +x ~/daily-check.sh

# 每天上午8点运行检查
(crontab -l 2>/dev/null; echo "0 8 * * * $HOME/daily-check.sh") | crontab -
```

### 5.2 每周维护清单

```bash
# 创建每周维护脚本
cat > ~/weekly-maintenance.sh << 'EOF'
#!/bin/bash

WEEKLY_LOG="$HOME/weekly-maintenance.log"
DATE=$(date '+%Y-%m-%d')

echo "=== 每周维护报告 - $DATE ===" > $WEEKLY_LOG

# 1. 系统更新
echo "1. 检查系统更新:" >> $WEEKLY_LOG
sudo apt update >> $WEEKLY_LOG 2>&1
UPDATES=$(apt list --upgradable 2>/dev/null | wc -l)
echo "可用更新数量: $UPDATES" >> $WEEKLY_LOG

# 2. Docker镜像更新
echo "2. Docker镜像更新:" >> $WEEKLY_LOG
cd ~/apps/flashcard_generator_mvp
docker compose pull >> $WEEKLY_LOG 2>&1

# 3. 日志分析
echo "3. 周度日志分析:" >> $WEEKLY_LOG
~/log-analyzer.sh
cat ~/log-analysis.log >> $WEEKLY_LOG

# 4. 性能总结
echo "4. 周度性能总结:" >> $WEEKLY_LOG
if [ -f ~/performance-monitor.log ]; then
    echo "本周平均CPU使用率:" >> $WEEKLY_LOG
    awk -F',' '{print $2}' ~/performance-monitor.log | grep "CPU:" | tail -168 | awk -F':' '{sum+=$2; count++} END {if(count>0) printf "%.1f%%\n", sum/count}' >> $WEEKLY_LOG
    
    echo "本周平均内存使用率:" >> $WEEKLY_LOG
    awk -F',' '{print $3}' ~/performance-monitor.log | grep "MEM:" | tail -168 | awk -F':' '{sum+=$2; count++} END {if(count>0) printf "%.1f%%\n", sum/count}' >> $WEEKLY_LOG
fi

# 5. 安全审计
echo "5. 安全审计:" >> $WEEKLY_LOG
~/security-monitor.sh
tail -20 ~/security-monitor.log >> $WEEKLY_LOG

# 6. 备份验证
echo "6. 备份验证:" >> $WEEKLY_LOG
BACKUP_COUNT=$(find ~/backups -name "*.tar.gz" -mtime -7 | wc -l)
echo "本周备份文件数量: $BACKUP_COUNT" >> $WEEKLY_LOG

# 7. 磁盘清理
echo "7. 磁盘清理:" >> $WEEKLY_LOG
BEFORE_CLEANUP=$(df / | awk 'NR==2{print $5}')
docker system prune -f >> $WEEKLY_LOG 2>&1
sudo apt autoremove -y >> $WEEKLY_LOG 2>&1
AFTER_CLEANUP=$(df / | awk 'NR==2{print $5}')
echo "清理前磁盘使用: $BEFORE_CLEANUP" >> $WEEKLY_LOG
echo "清理后磁盘使用: $AFTER_CLEANUP" >> $WEEKLY_LOG

echo "=== 每周维护完成 ===" >> $WEEKLY_LOG
EOF

chmod +x ~/weekly-maintenance.sh

# 每周日上午10点运行维护
(crontab -l 2>/dev/null; echo "0 10 * * 0 $HOME/weekly-maintenance.sh") | crontab -
```

---

## 🎯 第六部分：快速命令工具

### 6.1 管理命令集合

```bash
# 创建快速管理工具
cat > ~/manage.sh << 'EOF'
#!/bin/bash

case "$1" in
    "status")
        echo "=== 系统状态 ==="
        ~/dashboard.sh
        ;;
    "logs")
        echo "=== 应用日志 ==="
        tail -f ~/apps/flashcard_generator_mvp/logs/app.log
        ;;
    "restart")
        echo "=== 重启应用 ==="
        cd ~/apps/flashcard_generator_mvp
        docker compose restart flashcard-app
        echo "应用重启完成"
        ;;
    "update")
        echo "=== 更新应用 ==="
        cd ~/apps/flashcard_generator_mvp
        git pull
        docker compose build
        docker compose up -d
        echo "应用更新完成"
        ;;
    "backup")
        echo "=== 执行备份 ==="
        ~/enhanced-backup.sh
        ;;
    "monitor")
        echo "=== 启动监控 ==="
        watch -n 5 ~/dashboard.sh
        ;;
    "health")
        echo "=== 健康检查 ==="
        curl http://localhost:8000/health
        echo
        curl http://localhost:8000/supported_models | head -5
        ;;
    "clean")
        echo "=== 系统清理 ==="
        docker system prune -f
        sudo apt autoremove -y
        echo "清理完成"
        ;;
    "security")
        echo "=== 安全检查 ==="
        sudo fail2ban-client status
        sudo ufw status
        tail -10 ~/security-monitor.log
        ;;
    *)
        echo "用法: $0 {status|logs|restart|update|backup|monitor|health|clean|security}"
        echo ""
        echo "status   - 显示系统状态"
        echo "logs     - 查看实时日志"
        echo "restart  - 重启应用"
        echo "update   - 更新应用"
        echo "backup   - 执行备份"
        echo "monitor  - 启动监控面板"
        echo "health   - 健康检查"
        echo "clean    - 系统清理"
        echo "security - 安全检查"
        ;;
esac
EOF

chmod +x ~/manage.sh

# 创建别名
echo "alias fm='~/manage.sh'" >> ~/.bashrc
```

---

## 📝 总结

这个完整的监控和维护系统包含：

1. **实时监控**：系统资源、应用状态、网络连接
2. **自动化维护**：定期清理、更新检查、性能优化
3. **日志管理**：收集、分析、轮换、归档
4. **性能优化**：针对2GB RAM服务器的调优
5. **告警系统**：资源阈值监控、自动恢复
6. **备份策略**：全面备份、验证、清理
7. **安全监控**：入侵检测、审计日志
8. **维护清单**：每日、每周检查任务

**快速开始命令：**
```bash
# 查看系统状态
~/manage.sh status

# 启动实时监控
~/manage.sh monitor

# 执行健康检查
~/manage.sh health

# 查看帮助
~/manage.sh
```

这套监控和维护系统将确保您的AI Flashcard Generator在Debian 12服务器上稳定高效地运行。