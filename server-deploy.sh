#!/bin/bash
# AI Flashcard Generator - 自动化服务器部署脚本
# 针对 Debian 12 服务器 (2GB RAM) 优化

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "检测到root用户，建议创建专用用户运行应用"
        read -p "是否继续？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查系统要求
check_system_requirements() {
    log_info "检查系统要求..."
    
    # 检查操作系统
    if ! grep -q "Debian.*12" /etc/os-release; then
        log_warning "未检测到Debian 12，脚本可能不完全适用"
    fi
    
    # 检查内存
    TOTAL_MEM=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    if [ $TOTAL_MEM -lt 1800 ]; then
        log_error "内存不足：需要至少2GB，当前 ${TOTAL_MEM}MB"
        exit 1
    fi
    
    # 检查磁盘空间
    DISK_SPACE=$(df / | awk 'NR==2{print $4}')
    if [ $DISK_SPACE -lt 10485760 ]; then  # 10GB in KB
        log_error "磁盘空间不足：需要至少10GB"
        exit 1
    fi
    
    log_success "系统要求检查通过"
}

# 更新系统
update_system() {
    log_info "更新系统包..."
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y curl wget git vim ufw fail2ban htop
    log_success "系统更新完成"
}

# 安装Docker
install_docker() {
    log_info "检查Docker安装状态..."
    
    if command -v docker &> /dev/null; then
        log_success "Docker已安装"
        return
    fi
    
    log_info "安装Docker..."
    
    # 添加Docker官方GPG密钥
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
    
    # 将当前用户添加到docker组
    sudo usermod -aG docker $USER
    
    # 配置Docker守护进程（针对2GB RAM优化）
    sudo mkdir -p /etc/docker
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
    
    # 启动Docker服务
    sudo systemctl enable docker
    sudo systemctl start docker
    
    log_success "Docker安装完成"
    log_warning "请重新登录以使Docker组权限生效"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    
    # 重置防火墙规则
    sudo ufw --force reset
    
    # 设置默认策略
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # 允许SSH
    sudo ufw allow ssh
    sudo ufw allow 22/tcp
    
    # 允许HTTP和HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # 允许应用端口
    sudo ufw allow 8000/tcp
    
    # 启用防火墙
    sudo ufw --force enable
    
    # 配置Fail2ban
    sudo systemctl enable fail2ban
    sudo systemctl start fail2ban
    
    log_success "防火墙配置完成"
}

# 克隆项目
clone_project() {
    log_info "克隆项目代码..."
    
    # 创建应用目录
    mkdir -p ~/apps
    cd ~/apps
    
    # 检查是否已存在项目目录
    if [ -d "flashcard_generator_mvp" ]; then
        log_warning "项目目录已存在，是否重新克隆？"
        read -p "(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf flashcard_generator_mvp
        else
            cd flashcard_generator_mvp
            git pull
            log_success "项目代码更新完成"
            return
        fi
    fi
    
    # 这里需要用户提供实际的仓库地址
    log_warning "请确保项目代码已经在当前目录，或提供仓库地址"
    # git clone https://github.com/your-username/flashcard_generator_mvp.git
    
    cd flashcard_generator_mvp
    log_success "项目代码准备完成"
}

# 配置环境变量
configure_environment() {
    log_info "配置生产环境变量..."
    
    # 复制生产环境配置
    if [ ! -f .env ]; then
        cp .env.production .env
        log_success "环境配置文件已创建"
    else
        log_warning "环境配置文件已存在"
    fi
    
    log_warning "请编辑 .env 文件设置以下必需配置："
    echo "1. OPENROUTER_API_KEY - 您的OpenRouter API密钥"
    echo "2. SECRET_KEY - 安全密钥"
    echo "3. CORS_ORIGINS - 您的域名"
    
    read -p "是否现在编辑配置文件？(Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        vim .env
    fi
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    
    mkdir -p logs nginx/ssl
    chmod 755 logs
    chmod 700 nginx/ssl
    
    log_success "目录创建完成"
}

# 部署应用
deploy_application() {
    log_info "构建和部署应用..."
    
    # 检查Docker组权限
    if ! docker ps &> /dev/null; then
        log_error "Docker权限不足，请重新登录或使用 'newgrp docker'"
        return 1
    fi
    
    # 构建镜像
    log_info "构建Docker镜像..."
    docker compose build
    
    # 启动应用
    log_info "启动应用容器..."
    docker compose up -d
    
    # 等待容器启动
    log_info "等待应用启动..."
    sleep 30
    
    log_success "应用部署完成"
}

# 验证部署
verify_deployment() {
    log_info "验证部署状态..."
    
    # 检查容器状态
    if ! docker compose ps | grep -q "Up"; then
        log_error "容器未正常启动"
        docker compose logs
        return 1
    fi
    
    # 测试API端点
    log_info "测试API端点..."
    if curl -f http://localhost:8000/supported_models &> /dev/null; then
        log_success "API端点响应正常"
    else
        log_error "API端点无响应"
        return 1
    fi
    
    # 测试健康检查
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "健康检查通过"
    else
        log_warning "健康检查失败，请检查日志"
    fi
    
    log_success "部署验证完成"
}

# 设置监控
setup_monitoring() {
    log_info "设置基础监控..."
    
    # 创建监控脚本
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
    
    # 创建健康检查脚本
    cat > ~/health_check.sh << 'EOF'
#!/bin/bash
cd ~/apps/flashcard_generator_mvp

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
    
    log_success "监控脚本创建完成"
}

# 设置备份
setup_backup() {
    log_info "设置自动备份..."
    
    # 创建备份脚本
    cat > ~/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="$HOME/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# 备份配置文件
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
    ~/apps/flashcard_generator_mvp/.env \
    ~/apps/flashcard_generator_mvp/docker-compose.yml

# 备份日志
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" \
    ~/apps/flashcard_generator_mvp/logs/

# 清理旧备份（保留7天）
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF
    
    chmod +x ~/backup.sh
    
    # 设置定时备份
    (crontab -l 2>/dev/null; echo "0 2 * * * $HOME/backup.sh >> $HOME/backup.log 2>&1") | crontab -
    
    log_success "自动备份设置完成"
}

# 显示部署信息
show_deployment_info() {
    echo
    log_success "🎉 部署完成！"
    echo
    echo "=== 访问信息 ==="
    echo "应用地址: http://$(curl -s ifconfig.me):8000"
    echo "本地地址: http://localhost:8000"
    echo
    echo "=== 管理命令 ==="
    echo "查看状态: docker compose ps"
    echo "查看日志: docker compose logs -f flashcard-app"
    echo "重启应用: docker compose restart flashcard-app"
    echo "系统监控: ~/monitor.sh"
    echo "健康检查: ~/health_check.sh"
    echo "手动备份: ~/backup.sh"
    echo
    echo "=== 重要提醒 ==="
    echo "1. 请确保已设置正确的OPENROUTER_API_KEY"
    echo "2. 建议配置域名并启用HTTPS"
    echo "3. 定期运行系统更新和备份"
    echo "4. 监控系统资源使用情况"
    echo
}

# 主函数
main() {
    echo "=== AI Flashcard Generator 自动部署脚本 ==="
    echo "目标: Debian 12 服务器 (2GB RAM)"
    echo
    
    check_root
    check_system_requirements
    
    log_info "开始自动部署流程..."
    
    # 安装阶段
    update_system
    install_docker
    configure_firewall
    
    # 如果Docker刚安装，需要重新登录
    if ! docker ps &> /dev/null; then
        log_warning "Docker权限设置完成，请重新登录后再次运行此脚本"
        echo "执行: newgrp docker 或重新SSH登录"
        exit 0
    fi
    
    # 部署阶段
    clone_project
    configure_environment
    create_directories
    deploy_application
    verify_deployment
    
    # 配置阶段
    setup_monitoring
    setup_backup
    
    show_deployment_info
}

# 运行主函数
main "$@"