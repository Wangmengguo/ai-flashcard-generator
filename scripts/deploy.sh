#!/bin/bash

# =============================================================================
# AI Flashcard Generator - 一键云端部署脚本
# 适配新的HTTPS架构：nginx (HTTPS) + Docker + SSL证书
# =============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
SERVER_IP="198.23.164.200"
SERVER_USER="root"
PROJECT_NAME="ai-flashcard-generator"
DOMAIN="explain1thing.top"
CONTAINER_NAME="flashcard-generator-new"

# 打印带颜色的消息
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查本地环境
check_local_env() {
    print_status "检查本地部署环境..."
    
    # 检查SSH连接
    if ! ssh -o ConnectTimeout=5 $SERVER_USER@$SERVER_IP "echo 'SSH连接正常'" >/dev/null 2>&1; then
        print_error "无法连接到服务器 $SERVER_IP"
        exit 1
    fi
    
    # 检查必要文件
    local required_files=("main_refactored.py" "unified_index.html" "requirements.txt" "prompt_templates.json")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            print_error "缺少必要文件: $file"
            exit 1
        fi
    done
    
    print_success "本地环境检查通过"
}

# 备份服务器当前配置
backup_server_config() {
    print_status "备份服务器配置..."
    
    ssh $SERVER_USER@$SERVER_IP << 'EOF'
        # 创建备份目录
        BACKUP_DIR="/root/backup-$(date +%Y%m%d-%H%M%S)"
        mkdir -p $BACKUP_DIR
        
        # 备份nginx配置
        if [[ -f /etc/nginx/sites-enabled/explain1thing_ssl.conf ]]; then
            cp /etc/nginx/sites-enabled/explain1thing_ssl.conf $BACKUP_DIR/
        fi
        
        # 备份应用文件
        if [[ -d /var/www/ai-flashcard-generator ]]; then
            cp -r /var/www/ai-flashcard-generator $BACKUP_DIR/
        fi
        
        # 备份Docker配置
        docker ps | grep flashcard > $BACKUP_DIR/docker_status.txt || true
        
        echo "配置已备份到: $BACKUP_DIR"
EOF
    
    print_success "服务器配置备份完成"
}

# 部署应用文件
deploy_application() {
    print_status "部署应用文件到服务器..."
    
    # 创建临时目录并复制文件
    local temp_dir=$(mktemp -d)
    
    # 复制核心文件
    cp main_refactored.py "$temp_dir/"
    cp unified_index.html "$temp_dir/"
    cp requirements.txt "$temp_dir/"
    cp prompt_templates.json "$temp_dir/"
    
    # 复制模型管理相关文件
    if [[ -f "model_manager.py" ]]; then
        cp model_manager.py "$temp_dir/"
    fi
    
    if [[ -f "local_model_metadata.json" ]]; then
        cp local_model_metadata.json "$temp_dir/"
    fi
    
    if [[ -f "prompt_manager.py" ]]; then
        cp prompt_manager.py "$temp_dir/"
    fi
    
    # 传输文件到服务器
    scp -r "$temp_dir"/* $SERVER_USER@$SERVER_IP:/root/ai-flashcard-generator/src/
    
    # 清理临时目录
    rm -rf "$temp_dir"
    
    print_success "应用文件部署完成"
}

# 更新前端配置
update_frontend_config() {
    print_status "更新前端API配置..."
    
    ssh $SERVER_USER@$SERVER_IP << 'EOF'
        # 备份原文件
        cd /var/www/ai-flashcard-generator
        cp unified_index.html unified_index.html.backup-$(date +%Y%m%d-%H%M%S)
        
        # 复制新版本
        cp /root/ai-flashcard-generator/src/unified_index.html ./
        
        # 确保API_BASE_URL配置正确
        sed -i "s|window\.API_BASE_URL = ''|window.API_BASE_URL = '/ai-flashcard-generator/api'|g" unified_index.html
        
        # 设置权限
        chown -R www-data:www-data /var/www/ai-flashcard-generator
        
        echo "前端配置更新完成"
EOF
    
    print_success "前端配置更新完成"
}

# 更新Docker容器
update_docker_container() {
    print_status "更新Docker容器..."
    
    ssh $SERVER_USER@$SERVER_IP << 'EOF'
        cd /root/ai-flashcard-generator
        
        # 停止现有容器
        if docker ps | grep -q flashcard-generator; then
            echo "停止现有容器..."
            docker stop flashcard-generator-new || docker stop flashcard-generator || true
        fi
        
        # 重新构建镜像
        echo "重新构建Docker镜像..."
        docker build -t ai-flashcard-generator-flashcard-app .
        
        # 启动新容器（仅绑定到本地，保持安全配置）
        echo "启动新容器..."
        docker run -d --name flashcard-generator-new \
          --restart unless-stopped \
          -p 127.0.0.1:8000:8000 \
          --mount type=bind,source=/root/ai-flashcard-generator/src/config,target=/app/config,readonly \
          ai-flashcard-generator-flashcard-app
        
        # 清理旧容器
        docker container prune -f
        
        # 等待容器启动
        sleep 10
        
        # 验证容器状态
        if docker ps | grep -q flashcard-generator-new; then
            echo "Docker容器启动成功"
        else
            echo "Docker容器启动失败"
            exit 1
        fi
EOF
    
    print_success "Docker容器更新完成"
}

# 验证nginx配置并重载
reload_nginx() {
    print_status "验证并重载nginx配置..."
    
    ssh $SERVER_USER@$SERVER_IP << 'EOF'
        # 测试nginx配置
        if nginx -t; then
            echo "nginx配置验证通过"
            systemctl reload nginx
            echo "nginx重载完成"
        else
            echo "nginx配置验证失败"
            exit 1
        fi
        
        # 验证nginx服务状态
        if systemctl is-active --quiet nginx; then
            echo "nginx服务正常运行"
        else
            echo "nginx服务异常"
            exit 1
        fi
EOF
    
    print_success "nginx配置重载完成"
}

# 验证部署结果
verify_deployment() {
    print_status "验证部署结果..."
    
    ssh $SERVER_USER@$SERVER_IP << 'EOF'
        echo "=== 系统状态检查 ==="
        
        # 检查端口监听
        echo "检查端口监听状态："
        ss -tlnp | grep :443 && echo "✓ 443端口正常监听" || echo "✗ 443端口未监听"
        ss -tlnp | grep :8000 && echo "✓ 8000端口正常监听" || echo "✗ 8000端口未监听"
        
        # 检查Docker容器
        echo "检查Docker容器状态："
        if docker ps | grep -q flashcard-generator-new; then
            echo "✓ Docker容器正常运行"
        else
            echo "✗ Docker容器未运行"
        fi
        
        # 检查nginx状态
        echo "检查nginx状态："
        if systemctl is-active --quiet nginx; then
            echo "✓ nginx服务正常"
        else
            echo "✗ nginx服务异常"
        fi
        
        echo "=== 功能测试 ==="
        
        # 测试本地API
        echo "测试本地API连接："
        if curl -s http://127.0.0.1:8000/health >/dev/null; then
            echo "✓ 本地API响应正常"
        else
            echo "✗ 本地API响应异常"
        fi
        
        # 测试nginx代理
        echo "测试nginx API代理："
        if curl -s http://127.0.0.1/ai-flashcard-generator/api/health >/dev/null; then
            echo "✓ nginx API代理正常"
        else
            echo "✗ nginx API代理异常"
        fi
EOF
    
    # 测试外部访问
    print_status "测试外部访问..."
    
    if curl -s -I "https://$DOMAIN/ai-flashcard-generator/" | grep -q "200 OK"; then
        print_success "✓ HTTPS外部访问正常"
    else
        print_warning "✗ HTTPS外部访问可能异常"
    fi
    
    if curl -s "https://$DOMAIN/ai-flashcard-generator/api/health" | grep -q "status"; then
        print_success "✓ API外部访问正常"
    else
        print_warning "✗ API外部访问可能异常"
    fi
    
    print_success "部署验证完成"
}

# 显示部署结果
show_deployment_summary() {
    echo ""
    echo "=============================================="
    echo -e "${GREEN}🎉 部署完成！${NC}"
    echo "=============================================="
    echo ""
    echo "📋 访问信息："
    echo "  🌐 主应用: https://$DOMAIN/ai-flashcard-generator"
    echo "  🏠 个人主页: https://www.$DOMAIN"
    echo "  📡 API健康检查: https://$DOMAIN/ai-flashcard-generator/api/health"
    echo ""
    echo "🔧 管理命令："
    echo "  查看容器状态: ssh $SERVER_USER@$SERVER_IP 'docker ps | grep flashcard'"
    echo "  查看应用日志: ssh $SERVER_USER@$SERVER_IP 'docker logs flashcard-generator-new'"
    echo "  重启容器: ssh $SERVER_USER@$SERVER_IP 'docker restart flashcard-generator-new'"
    echo "  重载nginx: ssh $SERVER_USER@$SERVER_IP 'systemctl reload nginx'"
    echo ""
    echo "🔒 安全特性："
    echo "  ✅ 端到端HTTPS加密 (Let's Encrypt)"
    echo "  ✅ 8000端口本地保护"
    echo "  ✅ Cloudflare WAF防护"
    echo "  ✅ 防火墙规则配置"
    echo ""
}

# 主执行流程
main() {
    echo "=============================================="
    echo -e "${BLUE}🚀 AI Flashcard Generator 一键部署${NC}"
    echo "=============================================="
    echo ""
    
    # 确认执行
    read -p "确认要部署到生产服务器 $SERVER_IP 吗？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "部署已取消"
        exit 0
    fi
    
    # 执行部署流程
    check_local_env
    backup_server_config
    deploy_application
    update_frontend_config
    update_docker_container
    reload_nginx
    verify_deployment
    show_deployment_summary
    
    print_success "🎉 一键部署完成！"
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi