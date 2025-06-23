#!/bin/bash
# AI Flashcard Generator - 快速部署脚本
# 专为 198.23.164.200 Debian 12 服务器优化

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 检查环境
check_environment() {
    log_info "检查部署环境..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先运行 server-deploy.sh 安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose未安装"
        exit 1
    fi
    
    # 检查文件
    if [ ! -f "main_refactored.py" ]; then
        log_error "主程序文件 main_refactored.py 不存在"
        exit 1
    fi
    
    if [ ! -f "unified_index.html" ]; then
        log_error "前端文件 unified_index.html 不存在"
        exit 1
    fi
    
    log_success "环境检查通过"
}

# 创建环境配置
setup_environment() {
    log_info "设置环境配置..."
    
    # 创建 .env 文件（如果不存在）
    if [ ! -f ".env" ]; then
        cat > .env << 'EOF'
# === 生产环境配置 ===
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000
WORKERS=2

# === API配置 ===
OPENROUTER_API_KEY=your-openrouter-api-key-here

# === 安全配置 ===
SECRET_KEY=your-super-secret-key-$(date +%s)
CORS_ORIGINS=http://198.23.164.200:8000,https://yourdomain.com

# === 日志配置 ===
LOG_LEVEL=info
LOG_FORMAT=json

# === 其他配置 ===
MAX_TEXT_LENGTH=10000
REQUEST_TIMEOUT=60
EOF
        log_success "环境配置文件已创建"
        log_warning "请编辑 .env 文件设置您的 OPENROUTER_API_KEY"
    else
        log_info "环境配置文件已存在"
    fi
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    mkdir -p logs nginx/ssl
    
    # 确保logs目录权限正确（重要：解决权限问题）
    chmod 755 logs
    chmod 700 nginx/ssl
    
    # 如果logs目录已有文件，修复权限
    if [ -d "logs" ] && [ "$(ls -A logs)" ]; then
        log_info "修复已存在的日志文件权限..."
        chmod 644 logs/* 2>/dev/null || true
    fi
    
    log_success "目录创建完成"
}

# 构建和启动应用
deploy_application() {
    log_info "开始构建和部署应用..."
    
    # 停止现有容器
    log_info "停止现有容器..."
    docker compose down || true
    
    # 构建镜像
    log_info "构建Docker镜像..."
    docker compose build --no-cache
    
    # 启动应用
    log_info "启动应用容器..."
    docker compose up -d
    
    # 等待容器启动
    log_info "等待应用启动（30秒）..."
    sleep 30
    
    log_success "应用部署完成"
}

# 验证部署
verify_deployment() {
    log_info "验证部署状态..."
    
    # 检查容器状态
    if docker compose ps | grep -q "Up"; then
        log_success "容器运行正常"
    else
        log_error "容器未正常启动"
        docker compose logs
        return 1
    fi
    
    # 测试API端点
    log_info "测试API端点..."
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost:8000/supported_models > /dev/null; then
            log_success "API端点响应正常"
            break
        else
            log_info "尝试 $attempt/$max_attempts - 等待API启动..."
            sleep 5
            ((attempt++))
        fi
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "API端点无响应"
        return 1
    fi
    
    # 测试健康检查
    if curl -f -s http://localhost:8000/health > /dev/null; then
        log_success "健康检查通过"
    else
        log_warning "健康检查失败"
    fi
    
    log_success "部署验证完成"
}

# 显示部署信息
show_deployment_info() {
    echo
    log_success "🎉 快速部署完成！"
    echo
    echo "=== 访问信息 ==="
    echo "🌐 应用地址: http://198.23.164.200:8000"
    echo "🏠 本地地址: http://localhost:8000"
    echo
    echo "=== 管理命令 ==="
    echo "📊 查看状态: docker compose ps"
    echo "📜 查看日志: docker compose logs -f flashcard-app"
    echo "🔄 重启应用: docker compose restart flashcard-app"
    echo "⏹️  停止应用: docker compose down"
    echo "🔧 更新应用: git pull && docker compose build && docker compose up -d"
    echo
    echo "=== 测试命令 ==="
    echo "curl http://localhost:8000/supported_models"
    echo "curl http://localhost:8000/health"
    echo
    echo "=== 重要提醒 ==="
    log_warning "请确保已在 .env 文件中设置正确的 OPENROUTER_API_KEY"
    echo "📝 编辑配置: vim .env"
    echo "🔄 重启生效: docker compose restart flashcard-app"
    echo
}

# 错误处理
handle_error() {
    log_error "部署过程中出现错误，正在收集诊断信息..."
    
    echo "=== 容器状态 ==="
    docker compose ps || true
    
    echo "=== 容器日志 ==="
    docker compose logs --tail=50 || true
    
    echo "=== 系统资源 ==="
    free -h
    df -h
    
    echo "=== 错误排查建议 ==="
    echo "1. 检查 .env 文件中的 OPENROUTER_API_KEY"
    echo "2. 检查系统内存使用情况"
    echo "3. 检查端口 8000 是否被占用"
    echo "4. 查看详细日志: docker compose logs flashcard-app"
}

# 主函数
main() {
    echo "=== AI Flashcard Generator 快速部署 ==="
    echo "目标服务器: 198.23.164.200 (Debian 12, 2GB RAM)"
    echo "项目版本: v2.0 生产级"
    echo

    # 设置错误处理
    trap handle_error ERR
    
    check_environment
    setup_environment
    create_directories
    deploy_application
    verify_deployment
    show_deployment_info
}

# 检查参数
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  help    显示此帮助信息"
        echo "  logs    显示应用日志"
        echo "  status  显示容器状态"
        echo "  restart 重启应用"
        echo ""
        echo "快速部署: $0"
        exit 0
        ;;
    "logs")
        docker compose logs -f flashcard-app
        exit 0
        ;;
    "status")
        docker compose ps
        exit 0
        ;;
    "restart")
        log_info "重启应用..."
        docker compose restart flashcard-app
        log_success "应用已重启"
        exit 0
        ;;
    "fix-logs")
        log_info "修复日志权限问题..."
        # 停止容器
        docker compose down
        # 修复权限
        chmod 755 logs 2>/dev/null || mkdir -p logs && chmod 755 logs
        chmod 644 logs/* 2>/dev/null || true
        # 重新启动
        docker compose up -d
        log_success "日志权限已修复"
        exit 0
        ;;
    "")
        # 默认执行部署
        main
        ;;
    *)
        log_error "未知参数: $1"
        echo "使用 '$0 help' 查看帮助"
        exit 1
        ;;
esac